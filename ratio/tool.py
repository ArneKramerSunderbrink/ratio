from flask import Blueprint
from flask import g
from flask import render_template
from flask import get_template_attribute
from flask import request
from flask import url_for
from flask import jsonify
from werkzeug.exceptions import abort
from sqlite3 import IntegrityError

from ratio.auth import login_required, subgraph_access
from ratio.db import get_db

MSG_SUBGRAPH_ACCESS = 'Subgraph with id {} does not exist or is not owned by user {} currently logged in.'

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
        ' WHERE user_id = ? and deleted = 0'
        ' ORDER BY user_id ASC',
        (user_id,)
    ).fetchall()

    if subgraph_id is None:
        subgraph = {'id': 0, 'name': '', 'finished': False}
        return render_template('tool/index.html', subgraph=subgraph, subgraph_list=subgraph_list)

    subgraph = db.execute(
        'SELECT * FROM subgraph WHERE id = ?', (subgraph_id,)
    ).fetchone()

    if subgraph is None:
        abort(404)

    if not subgraph_access(user_id, subgraph_id):
        abort(403)

    knowledge = db.execute(
        'SELECT * FROM knowledge WHERE subgraph_id = ?', (subgraph_id,)
    )

    return render_template('tool/index.html', subgraph=subgraph, knowledge=knowledge, subgraph_list=subgraph_list)


@bp.route('/_set_finished')
@login_required
def set_finished():
    user_id = g.user['id']
    subgraph_id = request.args.get('subgraph_id', 0, type=int)
    finished = request.args.get('finished', '', type=str)

    db = get_db()

    if not subgraph_access(user_id, subgraph_id):
        return jsonify(error=MSG_SUBGRAPH_ACCESS.format(subgraph_id, user_id))

    if finished == 'true' or finished == 'false':
        finished = finished == 'true'
        db.execute(
            "UPDATE subgraph SET finished = ? WHERE id = ?", (finished, subgraph_id)
        )
        db.commit()
        return jsonify(finished=finished)
    else:
        abort(404)


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


@bp.route('/_edit_knowledge')
@login_required
def edit_knowledge():
    user_id = g.user['id']
    knowledge_id = request.args.get('knowledge_id', 0, type=int)
    subgraph_id = request.args.get('subgraph_id', 0, type=int)
    rdf_subject = request.args.get('subject', '', type=str)
    rdf_predicate = request.args.get('predicate', '', type=str)
    rdf_object = request.args.get('object', '', type=str)

    if not subgraph_id:
        return jsonify(error='Subgraph id cannot be empty.')
    if not knowledge_id:
        return jsonify(error='Knowledge id cannot be empty.')
    if not rdf_subject or rdf_subject.isspace():
        return jsonify(error='Subject cannot be empty.')
    if not rdf_predicate or rdf_predicate.isspace():
        return jsonify(error='Predicate cannot be empty.')
    if not rdf_object or rdf_object.isspace():
        return jsonify(error='Object cannot be empty.')

    db = get_db()
    db_cursor = db.cursor()

    if not subgraph_access(user_id, subgraph_id):
        return jsonify(error=MSG_SUBGRAPH_ACCESS.format(subgraph_id, user_id))

    knowledge_exists = db_cursor.execute(
        'SELECT EXISTS (SELECT 1 FROM knowledge WHERE id = ? AND subgraph_id = ?)', (knowledge_id, subgraph_id)
    ).fetchone()[0]

    if not knowledge_exists:
        return jsonify(error='Knowledge with id {} in subgraph with id {} does not exist.'
                       .format(knowledge_id, subgraph_id))

    db_cursor.execute(
        'UPDATE knowledge SET subject = ?, predicate = ?, object = ? WHERE id = ?',
        (rdf_subject, rdf_predicate, rdf_object, knowledge_id)
    )

    db.commit()

    return jsonify(subject=rdf_subject, predicate=rdf_predicate, object=rdf_object)


@bp.route('/_delete_knowledge')
@login_required
def delete_knowledge():
    user_id = g.user['id']
    knowledge_id = request.args.get('knowledge_id', 0, type=int)
    subgraph_id = request.args.get('subgraph_id', 0, type=int)

    if not subgraph_id:
        return jsonify(error='Subgraph id cannot be empty.')
    if not knowledge_id:
        return jsonify(error='Knowledge id cannot be empty.')

    db = get_db()
    db_cursor = db.cursor()

    if not subgraph_access(user_id, subgraph_id):
        return jsonify(error=MSG_SUBGRAPH_ACCESS.format(subgraph_id, user_id))

    knowledge_exists = db_cursor.execute(
        'SELECT EXISTS (SELECT 1 FROM knowledge WHERE id = ? AND subgraph_id = ?)', (knowledge_id, subgraph_id)
    ).fetchone()[0]

    if not knowledge_exists:
        return jsonify(error='Knowledge with id {} in subgraph with id {} does not exist.'
                       .format(knowledge_id, subgraph_id))

    db_cursor.execute(
        'DELETE FROM knowledge WHERE id = ?', (knowledge_id,)
    )

    db.commit()

    return jsonify()


@bp.route('/_add_knowledge')
@login_required
def add_knowledge():
    user_id = g.user['id']
    subgraph_id = request.args.get('subgraph_id', 0, type=int)
    rdf_subject = request.args.get('subject', '', type=str)
    rdf_predicate = request.args.get('predicate', '', type=str)
    rdf_object = request.args.get('object', '', type=str)

    if not subgraph_id:
        return jsonify(error='Subgraph id cannot be empty.')
    if not rdf_subject or rdf_subject.isspace():
        return jsonify(error='Subject cannot be empty.')
    if not rdf_predicate or rdf_predicate.isspace():
        return jsonify(error='Predicate cannot be empty.')
    if not rdf_object or rdf_object.isspace():
        return jsonify(error='Object cannot be empty.')

    db = get_db()
    db_cursor = db.cursor()

    if not subgraph_access(user_id, subgraph_id):
        return jsonify(error=MSG_SUBGRAPH_ACCESS.format(subgraph_id, user_id))

    db_cursor.execute(
        'INSERT INTO knowledge (subgraph_id, author_id, subject, predicate, object) VALUES (?, ?, ?, ?, ?)',
        (subgraph_id, user_id, rdf_subject, rdf_predicate, rdf_object)
    )
    knowledge_id = db_cursor.lastrowid

    db.commit()

    render_knowledge_row = get_template_attribute('tool/macros.html', 'knowledge_row')
    knowledge_row = render_knowledge_row(knowledge_id, subgraph_id, rdf_subject, rdf_predicate, rdf_object)

    return jsonify(knowledge_id=knowledge_id, subject=rdf_subject, predicate=rdf_predicate, object=rdf_object,
                   knowledge_row=knowledge_row)
