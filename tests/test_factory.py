import pytest

from ratio import create_app


def test_config():
    """Tests create_app without passing test config."""
    assert not create_app().testing
    assert create_app({'TESTING': True}).testing


@pytest.mark.parametrize(
    ('url', 'status', 'message'),
    (('/login', 404, b'This url does not belong to the app.'), ('prefix/login', 200, b'Log In'))
)
def test_url_prefix(url, status, message):
    """Tests the option to add an URL prefix."""
    app = create_app({'URL_PREFIX': 'prefix'})
    client = app.test_client()
    response = client.get(url)
    assert response.status_code == status
    assert message in response.data
