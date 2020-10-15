from flask import Blueprint
from flask import g
from flask import render_template
from flask import request
from flask import url_for
from flask import jsonify
from werkzeug.exceptions import abort
from sqlite3 import IntegrityError

from ratio.auth import login_required
from ratio.db import get_db

bp = Blueprint('tool', __name__)


@bp.route('/')
@bp.route('/<int:subgraph_id>')
@login_required
def index(subgraph_id=None):
    """Show all the posts, most recent first.""" #todo docu machen
    user_id = g.user['id']
    db = get_db()

    # for the subgraph menu
    subgraph_list = db.execute(
        'SELECT id, name, finished'
        ' FROM access JOIN subgraph ON subgraph_id = id'
        ' WHERE user_id = ?'
        ' ORDER BY name ASC',
        (user_id,)
    ).fetchall()

    if subgraph_id is None:
        subgraph = {'id': 0, 'name': '', 'finished': False}
        return render_template('tool/index.html', subgraph=subgraph, subgraph_list=subgraph_list)

    # todo testen ob dem user der subgraph gehört (gen function schreiben) abort(403)

    subgraph = db.execute(
        'SELECT * FROM subgraph WHERE id = ?', (subgraph_id,)
    ).fetchone()

    if subgraph is None:
        abort(404)

    return render_template('tool/index.html', subgraph=subgraph, subgraph_list=subgraph_list)


@login_required
@bp.route('/_set_finished')
def set_finished():
    subgraph_id = request.args.get('subgraph_id', 0, type=int)
    finished = request.args.get('finished', '', type=str)

    # todo testen ob es den subgraph gibt abort(404)
    # todo testen ob dem user der subgraph gehört (gen function schreiben) abort(403)

    if finished == 'true' or finished == 'false':
        finished = finished == 'true'
        db = get_db()
        db.execute(
            "UPDATE subgraph SET finished = ? WHERE id = ?", (finished, subgraph_id)
        )
        db.commit()
        return jsonify(finished=finished)
    else:
        abort(404)


@login_required
@bp.route('/_add_subgraph')
def add_subgraph():
    user_id = g.user['id']
    subgraph_name = request.args.get('name', '', type=str)

    if not subgraph_name or subgraph_name.isspace():
        return jsonify(error='Subgraph name cannot be empty.')

    db = get_db()
    try:
        db.execute(
            'INSERT INTO subgraph (name, finished) VALUES (?, ?)',
            (subgraph_name, False),
        )
    except IntegrityError:
        return jsonify(error='A subgraph of that name already exists.')

    subgraph = db.execute(
        'SELECT * FROM subgraph WHERE name = ?', (subgraph_name,)
    ).fetchone()

    db.execute(
        'INSERT INTO access (user_id, subgraph_id) VALUES (?, ?)',
        (user_id, subgraph['id']),
    )

    db.commit()
    return jsonify(redirect=url_for("tool.index", subgraph_id=subgraph['id']))
