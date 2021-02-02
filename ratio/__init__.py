import logging
import os

from flask import Flask
from flask import jsonify
from flask import render_template
from flask import request


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
    app.config.from_mapping(
        # a default secret that should be overridden by instance config
        SECRET_KEY='dev',
        # store the database in the instance folder
        DATABASE=os.path.join(app.instance_path, 'ratio.sqlite'),
        # Prepend URL_PREFIX to all routes, including static etc.
        URL_PREFIX='',
        # Don't do logging via gunicorn and with the gunicorn level
        GUNICORN_LOGGER=False,
        # Frontend config dictionary
        FRONTEND_CONFIG=dict(
            Subgraph_term='Clinical trial',
            subgraph_term='clinical trial',
            color0='#EDEDED',
            color1='#E6F7FF',
            color2='#F3F3DB'
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

    if app.config['GUNICORN_LOGGER']:  # pragma: no cover
        # do logging via gunicorn and with the gunicorn level
        gunicorn_logger = logging.getLogger('gunicorn.error')
        app.logger.handlers = gunicorn_logger.handlers
        app.logger.setLevel(gunicorn_logger.level)

    @app.route('/_test_logging')
    def test_logging():  # pragma: no cover
        app.logger.debug('this is a DEBUG message')
        app.logger.info('this is an INFO message')
        app.logger.warning('this is a WARNING message')
        app.logger.error('this is an ERROR message')
        app.logger.critical('this is a CRITICAL message')
        return jsonify('Debug, info, warning, error and critical message logged.')

    @app.route('/_color_picker', methods=('GET', 'POST'))
    def color_picker():  # pragma: no cover
        # only for development
        if request.method == 'POST':
            app.config['FRONTEND_CONFIG']['color0'] = request.form['color0']
            app.config['FRONTEND_CONFIG']['color1'] = request.form['color1']
            app.config['FRONTEND_CONFIG']['color2'] = request.form['color2']

        return render_template('color_picker.html')

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # register the database commands
    from ratio import db

    db.init_app(app)

    # apply the blueprints to the app
    from ratio import auth, tool, knowledge

    app.register_blueprint(auth.bp)
    app.register_blueprint(tool.bp)
    app.register_blueprint(knowledge.bp)

    return app
