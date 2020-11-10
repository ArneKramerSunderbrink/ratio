import pytest
from ratio.db import get_db
from ratio.tool import MSG_SUBGRAPH_ACCESS
from flask import url_for
from lxml import html
from urllib.parse import urlparse


def test_index(client, auth):
    auth.login()
    response = client.get("/")
    assert response.status_code == 200
    assert b'test' in response.data  # username in header
    assert b'href="/logout"' in response.data  # logout button


@pytest.mark.parametrize(
    ('user_id', 'access'),
    ((1, [True, True, False, False]), (2, [False, True, True, False]))
)
def test_subgraph_list(client, auth, user_id, access):
    """Subgraph 1 is owned by user 1 only
    Subgraph 2 is owned by both users
    Subgraph 3 is owned by user 2 only
    Subgraph 4 is owned by user 1 but deleted"""
    auth.login(user_id=user_id)
    data = html.fromstring(client.get('/').data)
    xpath = './/div[@id="subgraph-list"]//a[@href="/{}"]'
    for subgraph_id in range(1, 5):
        assert (data.find(xpath.format(subgraph_id)) is not None) == access[subgraph_id - 1]


@pytest.mark.parametrize(
    ('url', 'name', 'finished'),
    (('/1', 'subgraph1', False), ('/2', 'subgraph2', True))
)
def test_index_with_subgraph(client, auth, url, name, finished):
    auth.login()
    data = html.fromstring(client.get(url).data)
    # name in header
    assert data.find('.//a[@id="subgraph-name"]').text == name
    # finished-checkbox in header
    assert (data.find('.//input[@id="finished"]').get('checked') is not None) == finished
    # todo check if knowledge is displayed ...


@pytest.mark.parametrize(
    ('url', 'message'),
    (('/3', 'You have no access to subgraph with id 3.'),  # not owned by user 1
     ('/4', 'You have no access to subgraph with id 4.'),  # owned but deleted
     ('/99', 'Subgraph with id 99 does not exist.'))  # does not exist
)
def test_index_redirect(client, auth, url, message):
    auth.login()
    response = client.get(url)
    assert response.location == url_for('tool.index', message=message, _external=True)
    response = client.get(urlparse(response.location).path)  # follow redirect
    assert message.encode() in response.data


@pytest.mark.usefixtures("reset_db")
def test_set_finished(client, auth):
    db = get_db()
    assert not db.execute('SELECT * FROM subgraph WHERE id = 1').fetchone()['finished']
    auth.login()
    response = client.get('/_set_finished?subgraph_id=1&finished=true')
    assert 'error' not in response.get_json()
    assert response.get_json()['finished']
    assert db.execute('SELECT * FROM subgraph WHERE id = 1').fetchone()['finished']


@pytest.mark.parametrize(
    ('query', 'message'),
    (('finished=true', 'Subgraph id cannot be empty.'),
     ('subgraph_id=3&finished=true', MSG_SUBGRAPH_ACCESS.format(3, 1)),  # not owned
     ('subgraph_id=4&finished=true', MSG_SUBGRAPH_ACCESS.format(4, 1)),  # owned but deleted
     ('subgraph_id=99&finished=true', MSG_SUBGRAPH_ACCESS.format(99, 1)),  # doesn't exist
     ('subgraph_id=1', 'Argument "finished" has to be "true" or "false"'),
     ('subgraph_id=1&finished=123', 'Argument "finished" has to be "true" or "false"'))
)
def test_set_finished_validate_input(client, auth, query, message):
    auth.login()
    response = client.get('/_set_finished?' + query)
    assert 'finished' not in response.get_json()
    assert response.get_json()['error'] == message


@pytest.mark.usefixtures("reset_db")
def test_edit_subgraph_name(client, auth):
    db = get_db()
    assert db.execute('SELECT * FROM subgraph WHERE id = 1').fetchone()['name'] == 'subgraph1'
    auth.login()
    response = client.get('/_edit_subgraph_name?subgraph_id=1&name=test')
    assert 'error' not in response.get_json()
    assert response.get_json()['name'] == 'test'
    assert db.execute('SELECT * FROM subgraph WHERE id = 1').fetchone()['name'] == 'test'


@pytest.mark.parametrize(
    ('query', 'message'),
    (('name=test', 'Subgraph id cannot be empty.'),
     ('subgraph_id=3', 'Subgraph name cannot be empty.'),
     ('subgraph_id=3&name=%20', 'Subgraph name cannot be empty.'),
     ('subgraph_id=3&name=test', MSG_SUBGRAPH_ACCESS.format(3, 1)),  # not owned
     ('subgraph_id=4&name=test', MSG_SUBGRAPH_ACCESS.format(4, 1)),  # owned but deleted
     ('subgraph_id=99&name=test', MSG_SUBGRAPH_ACCESS.format(99, 1)))  # doesn't exist
)
def test_edit_subgraph_name_validate_input(client, auth, query, message):
    auth.login()
    response = client.get('/_edit_subgraph_name?' + query)
    assert 'name' not in response.get_json()
    assert response.get_json()['error'] == message


@pytest.mark.usefixtures("reset_db")
def test_delete_subgraph(client, auth):
    db = get_db()
    assert not db.execute('SELECT * FROM subgraph WHERE id = 1').fetchone()['deleted']
    auth.login()
    response = client.get('/_delete_subgraph?subgraph_id=1')
    assert 'error' not in response.get_json()
    assert response.get_json()['name'] == 'subgraph1'
    assert db.execute('SELECT * FROM subgraph WHERE id = 1').fetchone()['deleted']


@pytest.mark.parametrize(
    ('query', 'message'),
    (('', 'Subgraph id cannot be empty.'),
     ('subgraph_id=3', MSG_SUBGRAPH_ACCESS.format(3, 1)),  # not owned
     ('subgraph_id=4', MSG_SUBGRAPH_ACCESS.format(4, 1)),  # owned but deleted
     ('subgraph_id=99', MSG_SUBGRAPH_ACCESS.format(99, 1)))  # doesn't exist
)
def test_delete_subgraph_validate_input(client, auth, query, message):
    auth.login()
    response = client.get('/_delete_subgraph?' + query)
    assert 'name' not in response.get_json()
    assert response.get_json()['error'] == message


@pytest.mark.usefixtures("reset_db")
def test_undo_delete_subgraph(client, auth):
    db = get_db()
    assert db.execute('SELECT * FROM subgraph WHERE id = 4').fetchone()['deleted']
    auth.login()
    response = client.get('/_undo_delete_subgraph?subgraph_id=4')
    assert 'error' not in response.get_json()
    assert not db.execute('SELECT * FROM subgraph WHERE id = 4').fetchone()['deleted']


@pytest.mark.parametrize(
    ('query', 'message'),
    (('', 'Subgraph id cannot be empty.'),
     ('subgraph_id=3', MSG_SUBGRAPH_ACCESS.format(3, 1)),  # not owned
     ('subgraph_id=99', MSG_SUBGRAPH_ACCESS.format(99, 1)))  # doesn't exist
)
def test_undo_delete_subgraph_validate_input(client, auth, query, message):
    auth.login()
    response = client.get('/_undo_delete_subgraph?' + query)
    assert 'name' not in response.get_json()
    assert response.get_json()['error'] == message


@pytest.mark.usefixtures("reset_db")
def test_add_subgraph(client, auth):
    db = get_db()
    assert not db.execute('SELECT EXISTS (SELECT 1 FROM subgraph WHERE name = "new")').fetchone()[0]
    auth.login()
    response = client.get('/_add_subgraph?name=new')
    assert 'error' not in response.get_json()
    new = db.execute('SELECT * FROM subgraph WHERE name = "new"').fetchone()
    assert new
    assert response.get_json()['redirect'] == url_for('tool.index', subgraph_id=new['id'])


@pytest.mark.parametrize(
    ('query', 'message'),
    (('', 'Subgraph name cannot be empty.'),)  # doesn't exist
)
def test_add_subgraph_validate_input(client, auth, query, message):
    auth.login()
    response = client.get('/_add_subgraph?' + query)
    assert 'name' not in response.get_json()
    assert response.get_json()['error'] == message
