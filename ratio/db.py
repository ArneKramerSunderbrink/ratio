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
    ontology = g.pop('ontology', None)
    db = g.pop('db', None)

    if db is not None:
        db.close()


def init_db():
    """Clear existing data and create new tables."""
    with current_app.open_resource('schema.sql') as f:
        get_db().executescript(f.read().decode('utf8'))


@click.command('init-db')
@with_appcontext
def init_db_command():
    """Command to clear existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')


def db_populate_dummy():
    """Populates database with dummy data for testing and development."""
    with current_app.open_resource('data_dummy.sql') as f:
        get_db().executescript(f.read().decode('utf8'))


@click.command('db-add-dummy')
@with_appcontext
def db_populate_dummy_command():
    """Command to populates database with dummy data for testing and development."""
    db_populate_dummy()
    click.echo('Added dummy data to the database.')


@click.command('load-ontology-file')
@click.argument('path', type=click.Path(exists=True))
@click.option('-f', '--format', 'rdf_format', default='turtle')
@with_appcontext
def load_ontology_file_command(path, rdf_format):
    from ratio.knowledge_model import get_ontology
    get_ontology().load_ontology_file(path, rdf_format)
    click.echo('Loaded ontology into the database.')


def init_app(app):
    """Register database functions with the Flask app.
    This is called by the application factory.
    """
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    app.cli.add_command(db_populate_dummy_command)
    app.cli.add_command(load_ontology_file_command)
