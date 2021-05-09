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


def get_empty_subgraph_template(subgraph_id=None):
    """Returns empty subgraph template string"""
    with current_app.open_resource(current_app.config['EMPTY_SUBGRAPH_TEMPLATE'], 'r') as f:
        empty_subgraph_template = f.read()
    if subgraph_id is not None:
        empty_subgraph_template = empty_subgraph_template.format(id=subgraph_id)
    return empty_subgraph_template


def get_filter_description():
    with current_app.open_resource(current_app.config['FILTER'], 'r') as f:
        return f.read()


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
    with current_app.open_resource('dummy/admin.sql') as f:
        get_db().executescript(f.read().decode('utf8'))

    from ratio.knowledge_model import get_ontology
    with current_app.open_resource('dummy/ontology.ttl') as f:
        get_ontology().load_rdf_data(f, 'turtle')

    with current_app.open_resource('dummy/empty_subgraph_template.sql') as f:
        get_db().executescript(f.read().decode('utf8'))  # todo just a test

    from ratio.knowledge_model import get_subgraph_knowledge
    with current_app.open_resource('dummy/empty_subgraph_template.ttl') as f:
        get_subgraph_knowledge(2).load_rdf_data(f.read().decode('utf8').format(id=2))

    with current_app.open_resource('dummy/empty_subgraph_template.ttl') as f:
        with open(current_app.config['EMPTY_SUBGRAPH_TEMPLATE'], 'wb+') as f2:
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


@click.command('load-ontology-file')
@click.argument('file', type=click.File('rb'))
@click.option('-f', '--format', 'rdf_format', default='turtle')
@with_appcontext
def load_ontology_file_command(file, rdf_format):
    from ratio.knowledge_model import get_ontology
    get_ontology().load_ontology_file(file, rdf_format)
    click.echo('Loaded ontology into the database.')


def init_app(app):
    """Register database functions with the Flask app.
    This is called by the application factory.
    """
    app.teardown_appcontext(close_db)
    app.cli.add_command(db_init_command)
    app.cli.add_command(db_populate_dummy_command)
    app.cli.add_command(load_ontology_file_command)
