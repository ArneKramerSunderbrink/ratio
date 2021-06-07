from flask import current_app
from flask import Blueprint
from flask import jsonify
from flask import redirect
from flask import render_template
from flask import request
from flask import Response
from flask import url_for
from time import strftime
from urllib.parse import quote, unquote
from werkzeug.security import generate_password_hash

from ratio.auth import admin_required
from ratio.db import get_db, get_db_backup, upload_db_backup
from ratio.knowledge_model import get_ontology

bp = Blueprint('admin', __name__, url_prefix='/admin')


@bp.route('')
@bp.route('/msg:<string:message>')
@admin_required
def index(message=None):
    if message:
        message = unquote(message)

    db = get_db()
    user_list = db.execute(
        'SELECT id, username, admin'
        ' FROM user'
        ' ORDER BY id ASC',
    ).fetchall()

    return render_template('tool/admin.html', user_list=user_list, message=message)


@bp.route('/_add_user', methods=['POST'])
@admin_required
def add_subgraph():
    user_name = request.json.get('name')
    user_password = request.json.get('password')
    user_is_admin = request.json.get('admin') is not None

    if user_name is None or user_name.isspace():
        return jsonify(error='Username cannot be empty.')
    if user_password is None or user_password.isspace():
        return jsonify(error='Password cannot be empty.')
    user_password = generate_password_hash(user_password)

    user_uri = get_ontology().get_new_uri_user().n3()

    db = get_db()
    db_cursor = db.cursor()
    db_cursor.execute(
        'INSERT INTO user (username, password, admin, uri) VALUES (?, ?, ?, ?)',
        (user_name, user_password, user_is_admin, user_uri)
    )
    user_id = db_cursor.lastrowid
    db.commit()

    # todo render user row and add to list

    return jsonify()  # todo


@bp.route('/_download_db_backup')
@admin_required
def download_backup():
    filename = '{}_backup_{}.sqlite'.format(
        current_app.config['FRONTEND_CONFIG']['tool_name'],
        strftime('%Y-%m-%d-%H-%M-%S')
    )
    content = get_db_backup()

    return Response(
        content,
        mimetype='application/sql',
        headers={'Content-disposition': 'attachment; filename=' + filename})


@bp.route('/_upload_db_backup', methods=['POST'])
@admin_required
def upload_backup():
    # check if the post request has the file part
    if 'file' not in request.files:
        print('request.files', request.files)
        return jsonify(error='File cannot be empty.')
    file = request.files['file']
    # if user does not select file, browser also submit an empty part without filename
    if file.filename == '':
        return jsonify(error='File cannot be empty.')
    upload_db_backup(file)
    return redirect(url_for('admin.index', message=quote('Upload successful.')))  # todo redirect to admin
