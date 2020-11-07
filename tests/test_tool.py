import pytest
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

# todo test set finished

# todo test edit_subgraph_name

# todo test delete_subgraph

# todo test undo_delete_subgraph

# todo test add_subgraph

