from flask import current_app
from flask import Blueprint
from flask import g
from flask import jsonify
from flask import get_template_attribute
from flask import redirect
from flask import render_template
from flask import request
from flask import Response
from flask import url_for
from time import strftime
from urllib.parse import quote, unquote
from werkzeug.security import generate_password_hash

from ratio.auth import admin_required
from ratio.db import get_db, get_db_backup, upload_db_backup, get_admin_message, set_admin_message
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
        'SELECT id, username, admin, uri'
        ' FROM user'
        ' WHERE deleted = 0'
        ' ORDER BY id ASC',
    ).fetchall()

    show_admin_message, admin_message = get_admin_message()

    return render_template(
        'tool/admin.html', user_list=user_list,
        show_admin_message=show_admin_message, admin_message=admin_message,
        message=message
    )


@bp.route('user<int:user_id>')
@admin_required
def user_administration(user_id):

    db = get_db()
    user = db.execute(
        'SELECT * FROM user WHERE id = ?', (user_id,)
    ).fetchone()

    subgraph_list = db.execute(
        'SELECT id, name, finished'
        ' FROM access JOIN subgraph ON subgraph_id = id'
        ' WHERE user_id = ? and deleted = 0'
        ' ORDER BY subgraph_id ASC',
        (user_id,)
    ).fetchall()

    return render_template('tool/admin_user.html', user=user, subgraph_list=subgraph_list)


@bp.route('/_edit_user', methods=['POST'])
@admin_required
def edit_user():
    user_id = request.json.get('user_id')
    user_name = request.json.get('name')
    user_password = request.json.get('password')
    user_is_admin = request.json.get('admin') is not None

    if user_id is None:
        return jsonify(error='User id cannot be empty.')
    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify(error='User id has to be an integer.')
    if user_id == g.user['id'] and not user_is_admin:
        return jsonify(error='You cannot remove admin rights from your own account.')
    if not user_name or user_name.isspace():
        return jsonify(error='User name cannot be empty.')

    db = get_db()

    db.execute(
        'UPDATE user SET username = ?, admin = ? WHERE id = ?',
        (user_name, user_is_admin, user_id)
    )

    if user_password is not None and not user_password.isspace():
        db.execute(
            'UPDATE user SET password = ? WHERE id = ?',
            (generate_password_hash(user_password), user_id)
        )

    db.commit()
    return jsonify(user_name=user_name, user_is_admin=user_is_admin)


@bp.route('/_delete_user', methods=['POST'])
@admin_required
def delete_subgraph():
    user_id = request.json.get('user_id')

    if user_id is None:
        return jsonify(error='User id cannot be empty.')
    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify(error='User id has to be an integer.')
    if user_id == g.user['id']:
        return jsonify(error='You cannot delete your own account.')

    db = get_db()
    db_cursor = db.cursor()

    user_name = db_cursor.execute(
        'SELECT username FROM user WHERE id = ?', (user_id,)
    ).fetchone()[0]

    db_cursor.execute(
        'UPDATE user SET deleted = 1 WHERE id = ?', (user_id,)
    )

    db.commit()

    return jsonify(name=user_name)


@bp.route('/_undo_delete_user', methods=['POST'])
@admin_required
def undo_delete_user():
    user_id = request.json.get('user_id')

    if user_id is None:
        return jsonify(error='User id cannot be empty.')
    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify(error='User id has to be an integer.')

    db = get_db()
    db.execute(
        'UPDATE user SET deleted = 0 WHERE id = ?', (user_id,)
    )
    db.commit()

    return jsonify()


@bp.route('/_add_user', methods=['POST'])
@admin_required
def add_user():
    user_name = request.json.get('name')
    user_password = request.json.get('password')
    user_is_admin = request.json.get('admin') is not None

    if not user_name or user_name.isspace():
        return jsonify(error='Username cannot be empty.')
    user_name = user_name.strip()
    if not user_password or user_password.isspace():
        return jsonify(error='Password cannot be empty.')
    user_password = generate_password_hash(user_password)

    user_uri = get_ontology().get_new_uri_user().n3()

    db = get_db()
    db_cursor = db.cursor()

    if user_name in (r['username'] for r in db_cursor.execute(
        'SELECT username FROM user'
    ).fetchall()):
        return jsonify(error='There is already a (potentially deleted) user of that name.')

    db_cursor.execute(
        'INSERT INTO user (username, password, admin, uri) VALUES (?, ?, ?, ?)',
        (user_name, user_password, user_is_admin, user_uri)
    )
    user_id = db_cursor.lastrowid
    user = db_cursor.execute(
        'SELECT id, username, admin, uri FROM user WHERE id = ?',
        (user_id,)
    ).fetchone()
    db.commit()

    render_user_row = get_template_attribute('tool/admin_macros.html', 'user_row')
    user_row = render_user_row(user)

    return jsonify(user_row=user_row)


@bp.route('/_download_db_backup')
@admin_required
def download_backup():
    """
    The backup includes the instance/ratio.sqlite file, not the admin_message.txt, filter.ttl or new_subgraph.ratio!
    """

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
        return jsonify(error='File cannot be empty.')
    file = request.files['file']
    # if user does not select file, browser also submit an empty part without filename
    if file.filename == '':
        return jsonify(error='File cannot be empty.')
    upload_db_backup(file)
    return redirect(url_for('admin.index', message=quote('Upload successful.')))


@bp.route('/_change_admin_message', methods=['POST'])
@admin_required
def change_admin_message():
    message = request.form.get('message')
    show_message = request.form.get('show-message') is not None

    if show_message and (not message or message.isspace()):
        return redirect(url_for('admin.index', message=quote('Message cannot be empty.')))
    message = message.strip()

    set_admin_message(show_message, message)

    msg = 'Changed admin message.'
    if show_message:
        msg += ' Admin message active.'

    return redirect(url_for('admin.index', message=quote(msg)))
