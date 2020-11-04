import os
import tempfile

import pytest

from ratio import create_app
from ratio.db import get_db
from ratio.db import init_db
from ratio.db import db_populate_dummy


# configure pytest

def pytest_addoption(parser):
    parser.addoption(
        '--runbrowser', action='store_true', default=False, help='run browser tests'
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption('--runbrowser'):
        return
    skip_selenium = pytest.mark.skip(reason='need --runbrowser option to run')
    for item in items:
        if 'browser' in item.fixturenames:
            item.add_marker(skip_selenium)


# define tools used by the test

@pytest.fixture(scope='session')
def app():
    """Create and configure a new app instance for each test."""
    # create a temporary file to isolate the database for each test
    db_fd, db_path = tempfile.mkstemp()
    # create the app with common test config
    app = create_app({"TESTING": True, "DATABASE": db_path})

    # create the database and load test data
    with app.app_context():
        init_db()
        db_populate_dummy()

    yield app

    # close and remove the temporary database
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()


class AuthActions(object):
    def __init__(self, client):
        self._client = client

    def login(self, username="test", password="test"):
        return self._client.post(
            "/login", data={"username": username, "password": password}
        )

    def logout(self):
        return self._client.get("/logout")


@pytest.fixture
def auth(client):
    return AuthActions(client)
