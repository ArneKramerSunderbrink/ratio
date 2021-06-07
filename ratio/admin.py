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

from ratio.auth import admin_required
from ratio.db import get_db, get_db_backup, upload_db_backup

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
