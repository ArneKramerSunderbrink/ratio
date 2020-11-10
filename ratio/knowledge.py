from flask import Blueprint
from flask import g
from flask import get_template_attribute
from flask import request
from flask import jsonify

from ratio.auth import login_required, subgraph_access
from ratio.db import get_db

MSG_SUBGRAPH_ACCESS = 'Subgraph with id {} does not exist or is not owned by user {} currently logged in.'

bp = Blueprint('knowledge', __name__)


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
