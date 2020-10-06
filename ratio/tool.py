from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask import jsonify
from werkzeug.exceptions import abort

from ratio.auth import login_required
from ratio.db import get_db

bp = Blueprint('tool', __name__)


@bp.route('/')
@login_required
def index():
    """Show all the posts, most recent first."""
    db = get_db()
    #posts = db.execute(
    #    "SELECT p.id, title, body, created, author_id, username"
    #    " FROM post p JOIN user u ON p.author_id = u.id"
    #    " ORDER BY created DESC"
    #).fetchall()
    # todo get subgraph from g oder so
    subgraph = {'name': 'blabla', 'finished': False}
    return render_template('tool/index.html', subgraph=subgraph)


@bp.route('/_test')
def test():
    arg = request.args.get('arg', '', type=str)
    return jsonify(result='test successful: ' + arg)
