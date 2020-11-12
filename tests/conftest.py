import os
import pytest
import tempfile

from ratio import create_app
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
    skip_browser = pytest.mark.skip(reason='need --runbrowser option to run')
    for item in items:
        if 'browser' in item.fixturenames:
            item.add_marker(skip_browser)


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
def reset_db(app):
    # use this fixture to reset the db after the test
    yield
    with app.app_context():
        init_db()
        db_populate_dummy()


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()


class AuthActions(object):
    """A class that provides methods to log the test client in and out."""
    def __init__(self, client):
        self._client = client
        self.usernames = ['test', 'other']
        self.passwords = ['test', 'other']

    def login(self, username="test", password="test", user_id=None):
        if user_id:
            username = self.usernames[user_id - 1]
            password = self.passwords[user_id - 1]
        return self._client.post(
            "/login", data={"username": username, "password": password}
        )

    def logout(self):
        return self._client.get("/logout")


@pytest.fixture
def auth(client):
    return AuthActions(client)
