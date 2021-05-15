"""Database functionality."""

import click
import sqlite3
from flask import current_app
from flask import g
from flask.cli import with_appcontext


def get_db():
    """Connect to the application's configured database.
    The connection is unique for each request and will be reused if this is called again.
    """
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'], detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db


def close_db(e=None):
    """If this request connected to the database, close the connection."""
    db = g.pop('db', None)

    if db is not None:
        db.close()


def get_new_subgraph_instructions():
    """Returns empty subgraph template string"""
    with current_app.open_resource(current_app.config['NEW_SUBGRAPH_INSTRUCTIONS'], 'r') as f:
        empty_subgraph_template = f.read()
    return empty_subgraph_template


def get_filter_description():
    with current_app.open_resource(current_app.config['FILTER'], 'r') as f:
        return f.read()


def get_db_backup():
    db = get_db()
    backup_db = sqlite3.connect(current_app.config['BACKUP'])
    db.backup(backup_db)
    backup_db.close()
    with current_app.open_resource(current_app.config['BACKUP'], 'rb') as f:
        return f.read()


def upload_backup(backup_file):
    with open(current_app.config['DATABASE'], 'wb+') as f:
        f.write(backup_file.read())


def db_init():
    """Clear existing data and create new tables."""
    with current_app.open_resource('schema.sql') as f:
        get_db().executescript(f.read().decode('utf8'))


@click.command('db-init')
@with_appcontext
def db_init_command():
    """Command to clear existing data and create new tables."""
    db_init()
    click.echo('Initialized the database.')


def db_populate_dummy():
    """Populates database with dummy data for testing and development."""
    # TODO add dummy as sql backup
    with current_app.open_resource('dummy/admin.sql') as f:  # todo I won't need this afterwards
        get_db().executescript(f.read().decode('utf8'))

    from ratio.knowledge_model import get_ontology
    with current_app.open_resource('dummy/ontology.ttl') as f:  # todo I won't need this afterwards
        get_ontology().load_rdf_data(f, 'turtle')

    with current_app.open_resource('dummy/new_subgraph.ratio') as f:
        with open(current_app.config['NEW_SUBGRAPH_INSTRUCTIONS'], 'wb+') as f2:
            f2.write(f.read())

    with current_app.open_resource('dummy/filter.ttl') as f:
        with open(current_app.config['FILTER'], 'wb+') as f2:
            f2.write(f.read())


@click.command('db-add-dummy')
@with_appcontext
def db_populate_dummy_command():
    """Command to populates database with dummy data for testing and development."""
    db_populate_dummy()
    click.echo('Added dummy data to the database.')


@click.command('db-backup')
@with_appcontext
def db_backup_command():
    db = get_db()
    backup_db = sqlite3.connect('backup.sqlite')
    db.backup(backup_db)
    backup_db.close()
    click.echo('Backup created.')


@click.command('db-load-backup')
@click.argument('backup_file', type=click.File('rb'))
@with_appcontext
def db_load_backup_command(backup_file):
    with open(current_app.config['DATABASE'], 'wb+') as f:
        f.write(backup_file.read())
    click.echo('Loaded backup into the database.')


def init_app(app):
    """Register database functions with the Flask app.
    This is called by the application factory.
    """
    app.teardown_appcontext(close_db)
    app.cli.add_command(db_init_command)
    app.cli.add_command(db_populate_dummy_command)
    app.cli.add_command(db_backup_command)
    app.cli.add_command(db_load_backup_command)
