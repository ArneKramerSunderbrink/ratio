import pytest
from flask import url_for


def test_index(client, auth):
    response = client.get('/')
    assert response.headers["Location"] == url_for('auth.login', next_url=url_for('tool.index'), _external=True) + '%3F'

    auth.login()
    response = client.get("/")
    assert response.status_code == 200

    # todo if I have content on index check if it's shown
    #assert b"test title" in response.data
    #assert b"by test on 2018-01-01" in response.data
    #assert b"test\nbody" in response.data
    #assert b'href="/1/update"' in response.data
