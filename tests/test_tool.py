import pytest
from flask import url_for
from lxml import html


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
    response = html.fromstring(client.get('/').data)
    xpath = './/div[@id="subgraph-list"]//a[@href="/{}"]'
    for subgraph_id in range(1, 5):
        assert (response.find(xpath.format(subgraph_id)) is not None) == access[subgraph_id - 1]


# todo test subgraph /1 subgraph1 im header nicht finished
def test_index_with_subgraph(client, auth):
    auth.login()
    response = html.fromstring(client.get('/1').data)
    assert response.find('.//a[@id="subgraph-name"]').text == 'subgraph1'  # name in header
    # todo js funktioniert gar nicht, sicherstellen dass die input checkbox den richtigen wert hat immer!
    # todo not finished
    # todo knowledge is displayed ...


# todo test subgraph /99 -> redirect to /, message Subgraph with id 99 does not exist.
# todo test subgraph /3 -> redirect to /, message You have no access to subgraph with id 3
# todo test subgraph /4 -> redirect to /, message You have no access to subgraph with id 4 (deleted)

# todo test set finished

# todo test edit_subgraph_name

# todo test delete_subgraph

# todo test undo_delete_subgraph

# todo test add_subgraph

