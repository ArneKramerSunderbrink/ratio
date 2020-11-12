"""Functionality to display and edit subgraphs"""

from flask import Blueprint
from flask import g
from flask import jsonify
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for

from ratio.auth import login_required, subgraph_access
from ratio.db import get_db

MSG_SUBGRAPH_ACCESS = 'Subgraph with id {} does not exist or is not owned by user {} currently logged in.'

bp = Blueprint('tool', __name__)


@bp.route('/')
@bp.route('/<int:subgraph_id>')
@bp.route('/msg:<string:message>')
@login_required
def index(subgraph_id=None, message=None):
    """Main view of the tool.
    Contains list of accessible subgraphs and displays knowledge of the selected subgraph if subgraph_id not none.
    """
    user_id = g.user['id']
    db = get_db()

    # for the subgraph menu
    subgraph_list = db.execute(
        'SELECT id, name, finished'
        ' FROM access JOIN subgraph ON subgraph_id = id'
        ' WHERE user_id = ? and deleted = 0'
        ' ORDER BY user_id ASC',
        (user_id,)
    ).fetchall()

    if subgraph_id is None:
        subgraph = {'id': 0, 'name': '', 'finished': False}
        return render_template('tool/index.html', subgraph=subgraph, subgraph_list=subgraph_list, message=message)

    subgraph = db.execute(
        'SELECT * FROM subgraph WHERE id = ?', (subgraph_id,)
    ).fetchone()

    if subgraph is None:
        return redirect(url_for('tool.index', message='Subgraph with id {} does not exist.'.format(subgraph_id)))

    if not subgraph_access(user_id, subgraph_id):
        return redirect(url_for('tool.index', message='You have no access to subgraph with id {}.'.format(subgraph_id)))

    knowledge = db.execute(
        'SELECT * FROM knowledge WHERE subgraph_id = ?', (subgraph_id,)
    )

    return render_template('tool/index.html', subgraph=subgraph, knowledge=knowledge, subgraph_list=subgraph_list)


@bp.route('/_set_finished')
@login_required
def set_finished():
    """What it does.
    
    Request arguments:
        subgraph_id: ...
        finished: ...
    
    Returns JSON:
        error: msg...
        finished: ...
    """  #todo doku fertig
    # todo ist das eig nötig das ich finished returne? mach ich doch sonst auch nicht
    user_id = g.user['id']
    subgraph_id = request.args.get('subgraph_id', 0, type=int)
    finished = request.args.get('finished', '', type=str)

    if not subgraph_id:
        return jsonify(error='Subgraph id cannot be empty.')

    db = get_db()

    if not subgraph_access(user_id, subgraph_id):
        return jsonify(error=MSG_SUBGRAPH_ACCESS.format(subgraph_id, user_id))

    if finished == 'true' or finished == 'false':
        finished = finished == 'true'
        db.execute(
            'UPDATE subgraph SET finished = ? WHERE id = ?', (finished, subgraph_id)
        )
        db.commit()
        return jsonify(finished=finished)
    else:
        return jsonify(error='Argument "finished" has to be "true" or "false"')


@bp.route('/_edit_subgraph_name')
@login_required
def edit_subgraph_name():
    user_id = g.user['id']
    subgraph_id = request.args.get('subgraph_id', 0, type=int)
    subgraph_name = request.args.get('name', '', type=str)

    if not subgraph_id:
        return jsonify(error='Subgraph id cannot be empty.')
    if not subgraph_name or subgraph_name.isspace():
        return jsonify(error='Subgraph name cannot be empty.')

    db = get_db()
    db_cursor = db.cursor()

    if not subgraph_access(user_id, subgraph_id):
        return jsonify(error=MSG_SUBGRAPH_ACCESS.format(subgraph_id, user_id))

    db_cursor.execute(
        'UPDATE subgraph SET name = ? WHERE id = ?',
        (subgraph_name, subgraph_id)
    )

    db.commit()
    return jsonify(name=subgraph_name)


@bp.route('/_delete_subgraph')
@login_required
def delete_subgraph():
    user_id = g.user['id']
    subgraph_id = request.args.get('subgraph_id', 0, type=int)

    if not subgraph_id:
        return jsonify(error='Subgraph id cannot be empty.')

    db = get_db()
    db_cursor = db.cursor()

    if not subgraph_access(user_id, subgraph_id):
        return jsonify(error=MSG_SUBGRAPH_ACCESS.format(subgraph_id, user_id))

    subgraph_name = db_cursor.execute(
        'SELECT name FROM subgraph WHERE id = ?', (subgraph_id,)
    ).fetchone()[0]

    db_cursor.execute(
        'UPDATE subgraph SET deleted = 1 WHERE id = ?', (subgraph_id,)
    )

    db.commit()

    return jsonify(name=subgraph_name)


@bp.route('/_undo_delete_subgraph')
@login_required
def undo_delete_subgraph():
    user_id = g.user['id']
    subgraph_id = request.args.get('subgraph_id', 0, type=int)

    if not subgraph_id:
        return jsonify(error='Subgraph id cannot be empty.')

    db = get_db()
    db_cursor = db.cursor()

    access = db_cursor.execute(
        'SELECT EXISTS ('
        ' SELECT 1 FROM access JOIN subgraph ON subgraph_id = id WHERE user_id = ? AND subgraph_id = ?'
        ')',
        (user_id, subgraph_id)
    ).fetchone()[0]

    if not access:
        return jsonify(error=MSG_SUBGRAPH_ACCESS.format(subgraph_id, user_id))

    db_cursor.execute(
        'UPDATE subgraph SET deleted = 0 WHERE id = ?', (subgraph_id,)
    )

    db.commit()

    return jsonify()


@bp.route('/_add_subgraph')
@login_required
def add_subgraph():
    user_id = g.user['id']
    subgraph_name = request.args.get('name', '', type=str)

    if not subgraph_name or subgraph_name.isspace():
        return jsonify(error='Subgraph name cannot be empty.')

    db = get_db()
    db_cursor = db.cursor()

    db_cursor.execute(
        'INSERT INTO subgraph (name, finished, deleted) VALUES (?, ?, ?)',
        (subgraph_name, False, False)
    )

    subgraph_id = db_cursor.lastrowid

    db.execute(
        'INSERT INTO access (user_id, subgraph_id) VALUES (?, ?)',
        (user_id, subgraph_id)
    )

    db.commit()
    return jsonify(redirect=url_for('tool.index', subgraph_id=subgraph_id))
