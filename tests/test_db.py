import pytest
from sqlite3 import ProgrammingError

from ratio.db import get_db


def test_get_close_db(app):
    with app.app_context():
        db = get_db()
        assert db is get_db()

    with pytest.raises(ProgrammingError) as e:
        db.execute('SELECT 1')

    assert 'closed' in str(e.value)


def test_init_db_command(runner, monkeypatch):
    class Recorder(object):
        called = False

    def fake_init_db():
        Recorder.called = True

    monkeypatch.setattr('ratio.db.init_db', fake_init_db)
    result = runner.invoke(args=['init-db'])
    assert 'Initialized' in result.output
    assert Recorder.called


def test_db_populate_dummy_command(runner, monkeypatch):
    class Recorder(object):
        called = False

    def fake_db_populate_dummy():
        Recorder.called = True

    monkeypatch.setattr('ratio.db.db_populate_dummy', fake_db_populate_dummy)
    result = runner.invoke(args=['db-add-dummy'])
    assert 'dummy data' in result.output
    assert Recorder.called
