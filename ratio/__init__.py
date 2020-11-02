import os
import logging

from flask import Flask, jsonify


class URLPrefixMiddleware(object):
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
    app.config.from_mapping(
        # a default secret that should be overridden by instance config
        SECRET_KEY='dev',
        # store the database in the instance folder
        DATABASE=os.path.join(app.instance_path, 'ratio.sqlite'),
        # Prepend URL_PREFIX to all routes, including static etc.
        URL_PREFIX='',
        # Don't do logging via gunicorn and with the gunicorn level
        GUNICORN_LOGGER=False,
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.update(test_config)

    app.wsgi_app = URLPrefixMiddleware(app.wsgi_app, url_prefix=app.config['URL_PREFIX'])

    if app.config['GUNICORN_LOGGER']:
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
    from ratio import db

    db.init_app(app)

    # apply the blueprints to the app
    from ratio import auth, tool

    app.register_blueprint(auth.bp)
    app.register_blueprint(tool.bp)

    return app
