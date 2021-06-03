from flask import current_app
from flask import Blueprint
from flask import redirect
from flask import render_template
from flask import request
from flask import Response
from flask import url_for
from time import strftime
from urllib.parse import quote

from ratio.auth import admin_required
from ratio.db import get_db_backup, upload_db_backup

bp = Blueprint('admin', __name__)


@bp.route('/admin')
@admin_required
def admin():
    return render_template('tool/admin.html')


@bp.route('/_download_db_backup')
@admin_required
def download_db_backup():
    filename = '{}_backup_{}.sqlite'.format(
        current_app.config['FRONTEND_CONFIG']['tool_name'],
        strftime('%Y-%m-%d-%H-%M-%S')
    )
    content = get_db_backup()

    return Response(
        content,
        mimetype='application/sql',
        headers={'Content-disposition': 'attachment; filename=' + filename})


@bp.route('/_upload_db_backup', methods=['GET', 'POST'])
@admin_required
def upload_db_backup():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also submit an empty part without filename
        if file.filename == '':
            return redirect(request.url)
        upload_db_backup(file)
        return redirect(url_for('tool.index', message=quote('Upload successful.')))
    return '''
    <!doctype html>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file required>
      <input type=submit value=Upload>
    </form>
    '''