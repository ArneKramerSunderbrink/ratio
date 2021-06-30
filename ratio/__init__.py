import logging
import os

from flask import Flask
from flask import jsonify

from ratio.db import db_init_app


class URLPrefixMiddleware:
    """To listen to and provide the correct URLs when running und a server with a non-empty script name."""

    def __init__(self, app, url_prefix=''):
        self.app = app
        self.url_prefix = url_prefix

    def __call__(self, environ, start_response):
        if environ['PATH_INFO'].startswith(self.url_prefix):
            environ['PATH_INFO'] = environ['PATH_INFO'][len(self.url_prefix):]
            environ['SCRIPT_NAME'] = self.url_prefix
            return self.app(environ, start_response)
        else:
            start_response('404', [('Content-Type', 'text/plain')])
            return ['This url does not belong to the app.'.encode()]


def create_app(test_config=None):
    """Create and configure an instance of the Flask application."""

    app = Flask(__name__, instance_relative_config=True)
    # Note that some of the configuration things are overwritten when deploying the tool. See deploy/deploy.sh!
    app.config.from_mapping(
        # a default secret that should be overridden by instance config
        SECRET_KEY='dev',
        # store the database in the instance folder
        DATABASE=os.path.join(app.instance_path, 'ratio.sqlite'),
        # place to store a temporary backup of the database
        BACKUP=os.path.join(app.instance_path, 'backup.sqlite'),
        # place to store an admin message that can be shown to all users
        ADMIN_MESSAGE=os.path.join(app.instance_path, 'admin_message.txt'),
        # instructions for creating new subgraphs
        NEW_SUBGRAPH_INSTRUCTIONS=os.path.join(app.instance_path, 'new_subgraph.ratio'),
        # the file describing the filter
        FILTER=os.path.join(app.instance_path, 'filter.ttl'),
        # Prepend URL_PREFIX to all routes, including static etc.
        URL_PREFIX='',
        # Don't do logging via gunicorn and with the gunicorn level
        GUNICORN_LOGGER=False,
        # Frontend config dictionary
        FRONTEND_CONFIG=dict(
            tool_name='CTrO-Editor',
            tool_description='CtrO-Editor allows capturing the information contained in published clinical trials and '
                             'exports it into a semantic machine-readable format (RDF).',
            Subgraph_term='Clinical trial',
            subgraph_term='clinical trial',
            color0='#EDEDED',
            color1='#E6F7FF',
            color2='#F3F3DB',
            color3='#BBFFB3'
        )
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.update(test_config)

    app.wsgi_app = URLPrefixMiddleware(app.wsgi_app, url_prefix=app.config['URL_PREFIX'])

    @app.context_processor
    def inject_frontend_config():
        return dict(frontend_config=app.config['FRONTEND_CONFIG'])

    if app.config['GUNICORN_LOGGER']:
        # do logging via gunicorn and with the gunicorn level
        gunicorn_logger = logging.getLogger('gunicorn.error')
        app.logger.handlers = gunicorn_logger.handlers
        app.logger.setLevel(gunicorn_logger.level)

    @app.route('/_test_logging')
    def test_logging():
        app.logger.debug('this is a DEBUG message')
        app.logger.info('this is an INFO message')
        app.logger.warning('this is a WARNING message')
        app.logger.error('this is an ERROR message')
        app.logger.critical('this is a CRITICAL message')
        return jsonify('Debug, info, warning, error and critical message logged.')

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # register the database commands
    db_init_app(app)

    # apply the blueprints to the app
    from ratio import auth, admin, tool, knowledge, search, call

    app.register_blueprint(auth.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(tool.bp)
    app.register_blueprint(knowledge.bp)
    app.register_blueprint(search.bp)
    app.register_blueprint(call.bp)

    return app
