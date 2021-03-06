import pytest
from flask import g
from flask import session
from flask import url_for
from urllib.parse import urlparse


def test_login(client, auth):
    # test that viewing the page renders without template errors
    assert client.get('/login').status_code == 200

    # test that successful login redirects to the index page
    response = auth.login()
    assert response.location == url_for('tool.index', _external=True)

    # login request set the user_id in the session
    # check that the user is loaded from the session
    with client:
        client.get('/')
        assert session['user_id'] == 1
        assert g.user['username'] == 'test'


@pytest.mark.parametrize(
    ('username', 'password', 'message'),
    (('a', 'test', b'Incorrect username.'), ('test', 'a', b'Incorrect password.'))
)
def test_login_validate_input(auth, username, password, message):
    response = auth.login(username, password)
    assert message in response.data
    assert bytes(username, 'utf8') in response.data


def test_login_redirect(client):
    response = client.get('/1')
    # redirects to login
    url = urlparse(response.location)
    assert url.path == '/login'
    response = client.post(url.path + '?' + url.query, data={'username': 'test', 'password': 'test'})
    # redirects to /1
    url = urlparse(response.location)
    response = client.get(url.path)
    assert b'Clinical trial 1' in response.data


def test_logout(client, auth):
    auth.login()

    with client:
        auth.logout()
        assert 'user_id' not in session
