"""Functionality to display and edit subgraphs"""

from flask import Blueprint
from flask import current_app
from flask import g
from flask import jsonify
from flask import render_template
from flask import request
from flask import Response
from flask import redirect
from flask import url_for
from time import strftime
from urllib.parse import quote, unquote

from ratio.auth import login_required, subgraph_access
from ratio.db import get_db, get_new_subgraph_instructions
from ratio.knowledge_model import get_subgraph_knowledge

MSG_SUBGRAPH_ACCESS = '{} with id {} does not exist or is not owned by user {} currently logged in.'

bp = Blueprint('tool', __name__)


@bp.route('/')
@bp.route('/msg:<string:message>')
@login_required
def index(message=None):
    """Home view of the tool.
    Contains list of accessible subgraphs.
    """
    user_id = g.user['id']

    if message:
        message = unquote(message)

    db = get_db()

    # for the subgraph menu
    subgraph_list = db.execute(
        'SELECT id, name, finished'
        ' FROM access JOIN subgraph ON subgraph_id = id'
        ' WHERE user_id = ? and deleted = 0'
        ' ORDER BY user_id ASC',
        (user_id,)
    ).fetchall()

    return render_template('tool/index.html', subgraph_list=subgraph_list, message=message)


@bp.route('/<int:subgraph_id>')
@login_required
def edit_view(subgraph_id):
    """Edit view.
    Displays knowledge about a subgraph and allows users to edit it."""
    user_id = g.user['id']

    db = get_db()

    subgraph = db.execute(
        'SELECT * FROM subgraph WHERE id = ?', (subgraph_id,)
    ).fetchone()

    if subgraph is None:
        message = '{} with id {} does not exist.'.format(
            current_app.config['FRONTEND_CONFIG']['Subgraph_term'], subgraph_id
        )
        # for some reason I need to unquote two times (once via url_for, once via quote) on the server, else
        # I'd get a bad request
        return redirect(url_for('tool.index', message=quote(message)))

    if not subgraph_access(user_id, subgraph_id):
        message = 'You have no access to {} with id {}.'.format(
            current_app.config['FRONTEND_CONFIG']['subgraph_term'], subgraph_id
        )
        return redirect(url_for('tool.index', message=quote(message)))

    root = get_subgraph_knowledge(subgraph_id).get_root()

    return render_template('tool/edit.html', subgraph=subgraph, root=root)


@bp.route('/<int:subgraph_id>/overview')
@login_required
def overview(subgraph_id):
    user_id = g.user['id']

    db = get_db()

    if subgraph_id is None:
        return jsonify(error='{} id cannot be empty.'.format(current_app.config['FRONTEND_CONFIG']['Subgraph_term']))

    subgraph = db.execute(
        'SELECT * FROM subgraph WHERE id = ?', (subgraph_id,)
    ).fetchone()

    if subgraph is None:
        message = '{} with id {} does not exist.'.format(
            current_app.config['FRONTEND_CONFIG']['Subgraph_term'], subgraph_id
        )
        return redirect(url_for('tool.index', message=quote(message)))

    if not subgraph_access(user_id, subgraph_id):
        message = 'You have no access to {} with id {}.'.format(
            current_app.config['FRONTEND_CONFIG']['subgraph_term'], subgraph_id
        )
        return redirect(url_for('tool.index', message=quote(message)))

    return render_template('tool/overview.html', subgraph=subgraph,
                           rdf_graph=get_subgraph_knowledge(subgraph_id).get_graph(clean=True, ontology=True))


@bp.route('/_set_finished')
@login_required
def set_finished():
    """Changes the finished flag of a subgraph.
    
    Request args:
        subgraph_id (int): Id of the Subgraph to change.
        finished (str: 'true' or 'false'): The new value of the finished flag of the subgraph.

    Context:
        g.user (sqlite3.Row): Logged in user. Must have access to the subgraph.

    Returns JSON:
        error (str): An error message if something went wrong.

    """
    user_id = g.user['id']
    subgraph_id = request.args.get('subgraph_id', 0, type=int)
    finished = request.args.get('finished', '', type=str)

    if not subgraph_id:
        return jsonify(error='{} id cannot be empty.'.format(current_app.config['FRONTEND_CONFIG']['Subgraph_term']))

    db = get_db()

    if not subgraph_access(user_id, subgraph_id):
        return jsonify(error=MSG_SUBGRAPH_ACCESS.format(current_app.config['FRONTEND_CONFIG']['Subgraph_term'],
                                                        subgraph_id, user_id))

    if finished == 'true' or finished == 'false':
        finished = finished == 'true'
        db.execute(
            'UPDATE subgraph SET finished = ? WHERE id = ?', (finished, subgraph_id)
        )
        db.commit()
        return jsonify()
    else:
        return jsonify(error='Argument "finished" has to be "true" or "false"')


@bp.route('/_edit_subgraph_name')
@login_required
def edit_subgraph_name():
    """Changes the name of a subgraph.

    Request args:
        subgraph_id (int): Id of the Subgraph to change.
        name (str): The new name of the subgraph.

    Context:
        g.user (sqlite3.Row): Logged in user. Must have access to the subgraph.

    Returns JSON:
        name (str): The new name of the subgraph. (identical to the argument, only to make js simpler)
        error (str): An error message if something went wrong.

    """
    user_id = g.user['id']
    subgraph_id = request.args.get('subgraph_id', 0, type=int)
    subgraph_name = request.args.get('name', '', type=str)

    if not subgraph_id:
        return jsonify(error='{} id cannot be empty.'.format(current_app.config['FRONTEND_CONFIG']['Subgraph_term']))
    if not subgraph_name or subgraph_name.isspace():
        return jsonify(error='{} name cannot be empty.'.format(current_app.config['FRONTEND_CONFIG']['Subgraph_term']))

    db = get_db()
    db_cursor = db.cursor()

    if not subgraph_access(user_id, subgraph_id):
        return jsonify(error=MSG_SUBGRAPH_ACCESS.format(current_app.config['FRONTEND_CONFIG']['Subgraph_term'],
                                                        subgraph_id, user_id))

    db_cursor.execute(
        'UPDATE subgraph SET name = ? WHERE id = ?',
        (subgraph_name, subgraph_id)
    )

    db.commit()
    return jsonify(name=subgraph_name)


@bp.route('/_delete_subgraph')
@login_required
def delete_subgraph():
    """Marks a subgraph as deleted.

    The subgraph is not actually deleted from the db and can be made accessible again by setting the
    deleted flag back to 0.

    Request args:
        subgraph_id (int): Id of the Subgraph to delete.

    Context:
        g.user (sqlite3.Row): Logged in user. Must have access to the subgraph.

    Returns JSON:
        name (str): The new name of the deleted subgraph.
        error (str): An error message if something went wrong.

    """
    user_id = g.user['id']
    subgraph_id = request.args.get('subgraph_id', 0, type=int)

    if not subgraph_id:
        return jsonify(error='{} id cannot be empty.'.format(current_app.config['FRONTEND_CONFIG']['Subgraph_term']))

    db = get_db()
    db_cursor = db.cursor()

    if not subgraph_access(user_id, subgraph_id):
        return jsonify(error=MSG_SUBGRAPH_ACCESS.format(current_app.config['FRONTEND_CONFIG']['Subgraph_term'],
                                                        subgraph_id, user_id))

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
    """Marks a subgraph as not deleted.

    Request args:
        subgraph_id (int): Id of the Subgraph to un-delete.

    Context:
        g.user (sqlite3.Row): Logged in user. Must have access to the subgraph.

    Returns JSON:
        error (str): An error message if something went wrong.

    """
    user_id = g.user['id']
    subgraph_id = request.args.get('subgraph_id', 0, type=int)

    if not subgraph_id:
        return jsonify(error='{} id cannot be empty.'.format(current_app.config['FRONTEND_CONFIG']['Subgraph_term']))

    db = get_db()
    db_cursor = db.cursor()

    access = db_cursor.execute(
        'SELECT EXISTS ('
        ' SELECT 1 FROM access JOIN subgraph ON subgraph_id = id WHERE user_id = ? AND subgraph_id = ?'
        ')',
        (user_id, subgraph_id)
    ).fetchone()[0]

    if not access:
        return jsonify(error=MSG_SUBGRAPH_ACCESS.format(current_app.config['FRONTEND_CONFIG']['Subgraph_term'],
                                                        subgraph_id, user_id))

    db_cursor.execute(
        'UPDATE subgraph SET deleted = 0 WHERE id = ?', (subgraph_id,)
    )

    db.commit()

    return jsonify()


@bp.route('/_add_subgraph')
@login_required
def add_subgraph():
    """Add a new subgraph.

    Request args:
        name (str): Name of the new subgraph.

    Context:
        g.user (sqlite3.Row): Logged in user. The new subgraph will be made accessible to this user.

    Returns JSON:
        redirect (str): URL of the new subgraph.
        error (str): An error message if something went wrong.

    """
    user_id = g.user['id']
    subgraph_name = request.args.get('name', '', type=str)

    if not subgraph_name or subgraph_name.isspace():
        return jsonify(error='{} name cannot be empty.'.format(current_app.config['FRONTEND_CONFIG']['Subgraph_term']))

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

    get_subgraph_knowledge(subgraph_id).execute_ratio_instructions(get_new_subgraph_instructions())

    db.commit()
    return jsonify(redirect=url_for('tool.edit_view', subgraph_id=subgraph_id))


@bp.route('/<int:subgraph_id>/_download_rdf')
@login_required
def download_rdf(subgraph_id):
    user_id = g.user['id']

    if not subgraph_id:
        return jsonify(error='{} id cannot be empty.'.format(current_app.config['FRONTEND_CONFIG']['Subgraph_term']))

    if not subgraph_access(user_id, subgraph_id):
        return jsonify(error=MSG_SUBGRAPH_ACCESS.format(current_app.config['FRONTEND_CONFIG']['Subgraph_term'],
                                                        subgraph_id, user_id))

    filename = "{}_{}_{}.ttl".format(
        current_app.config['FRONTEND_CONFIG']['Subgraph_term'],
        subgraph_id,
        strftime('%Y-%m-%d-%H-%M-%S')
    )
    content = get_subgraph_knowledge(subgraph_id).get_serialization(clean=True, ontology=False)

    return Response(
        content,
        mimetype="text/plain",
        headers={"Content-disposition": "attachment; filename="+filename})
