"""Functionality related to editing of knowledge."""

from flask import Blueprint
from flask import g
from flask import get_template_attribute
from flask import jsonify
from flask import request

from ratio.auth import login_required
from ratio.auth import subgraph_access
from ratio.db import get_db
from ratio.knowledge_model import get_subgraph_knowledge

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


@bp.route('/_add_value')
@login_required
def add_value():
    user_id = g.user['id']
    subgraph_id = request.args.get('subgraph_id', 0, type=int)
    property_uri = request.args.get('property_uri', '', type=str)
    entity_uri = request.args.get('entity_uri', '', type=str)

    if not subgraph_id:
        return jsonify(error='Subgraph id cannot be empty.')
    if not property_uri or property_uri.isspace():
        return jsonify(error='Property URI cannot be empty.')
    if not entity_uri or entity_uri.isspace():
        return jsonify(error='Entity URI cannot be empty.')

    if not subgraph_access(user_id, subgraph_id):
        return jsonify(error=MSG_SUBGRAPH_ACCESS.format(subgraph_id, user_id))

    subgraph_knowledge = get_subgraph_knowledge(subgraph_id)
    field = subgraph_knowledge.get_field(entity_uri, property_uri)

    if field.is_described:
        return jsonify(error='You have to use /_add_entity to add a described individual')
    if field.is_functional and field.values:
        return jsonify(error='You cannot add more than one value to this field.')

    index = subgraph_knowledge.new_value(entity_uri, property_uri)

    if field.options is None:
        render_value_div = get_template_attribute('tool/macros.html', 'value_free')
    else:
        render_value_div = get_template_attribute('tool/macros.html', 'value_options')
    value_div = render_value_div(field, '', index)

    return jsonify(value_div=value_div,
                   property_uri=property_uri, entity_uri=entity_uri,
                   remove_plus=field.is_functional)


@bp.route('/_change_value')
@login_required
def change_value():
    user_id = g.user['id']
    subgraph_id = request.args.get('subgraph_id', 0, type=int)
    entity_uri = request.args.get('entity_uri', '', type=str)
    property_uri = request.args.get('property_uri', '', type=str)
    index = request.args.get('index', -1, type=int)
    value = request.args.get('value', '', type=str).strip()

    if not subgraph_id:
        return jsonify(error='Subgraph id cannot be empty.')
    if not entity_uri or entity_uri.isspace():
        return jsonify(error='Entity URI cannot be empty.')
    if not property_uri or property_uri.isspace():
        return jsonify(error='Property URI cannot be empty.')
    if index < 0:
        return jsonify(error='Index cannot be empty.')

    if not subgraph_access(user_id, subgraph_id):
        return jsonify(error=MSG_SUBGRAPH_ACCESS.format(subgraph_id, user_id))

    subgraph_knowledge = get_subgraph_knowledge(subgraph_id)
    field = subgraph_knowledge.get_field(entity_uri, property_uri)

    if field.is_described:
        # todo stimmt der link?
        return jsonify(error='You have to use /_change_entity_label to change the label of a described individual')

    validity = subgraph_knowledge.change_value(entity_uri, property_uri, index, value)
    if validity:
        return jsonify(validity=validity)

    return jsonify()


@bp.route('/_add_entity')
@login_required
def add_entity():
    user_id = g.user['id']
    subgraph_id = request.args.get('subgraph_id', 0, type=int)
    property_uri = request.args.get('property_uri', '', type=str)
    parent_uri = request.args.get('entity_uri', '', type=str)
    entity_label = request.args.get('label', '', type=str)

    if not subgraph_id:
        return jsonify(error='Subgraph id cannot be empty.')
    if not property_uri or property_uri.isspace():
        return jsonify(error='Property URI cannot be empty.')
    if not parent_uri or parent_uri.isspace():
        return jsonify(error='Parent URI cannot be empty.')
    if not entity_label or entity_label.isspace():
        return jsonify(error='Entity label cannot be empty.')

    if not subgraph_access(user_id, subgraph_id):
        return jsonify(error=MSG_SUBGRAPH_ACCESS.format(subgraph_id, user_id))

    subgraph_knowledge = get_subgraph_knowledge(subgraph_id)
    field = subgraph_knowledge.get_field(parent_uri, property_uri)

    if field.is_functional and field.values:
        return jsonify(error='You cannot add more than one value to this field.')

    entity, index = subgraph_knowledge.new_individual(field.range_uri, entity_label, parent_uri, property_uri)

    render_entity_div = get_template_attribute('tool/macros.html', 'entity_div')
    entity_div = render_entity_div(entity, False, index)

    return jsonify(entity_div=entity_div,
                   property_uri=property_uri, parent_uri=parent_uri,
                   remove_plus=field.is_functional)


@bp.route('/_delete_entity')
@login_required
def delete_entity():
    user_id = g.user['id']
    subgraph_id = request.args.get('subgraph_id', 0, type=int)
    entity_uri = request.args.get('entity_uri', '', type=str)

    if not subgraph_id:
        return jsonify(error='Subgraph id cannot be empty.')
    if not entity_uri or entity_uri.isspace():
        return jsonify(error='Entity URI cannot be empty.')

    if not subgraph_access(user_id, subgraph_id):
        return jsonify(error=MSG_SUBGRAPH_ACCESS.format(subgraph_id, user_id))

    subgraph_knowledge = get_subgraph_knowledge(subgraph_id)
    subgraph_knowledge.delete_individual_recursive(entity_uri)

    return jsonify()


@bp.route('/_undo_delete_entity')
@login_required
def undo_delete_entity():
    user_id = g.user['id']
    subgraph_id = request.args.get('subgraph_id', 0, type=int)
    entity_uri = request.args.get('entity_uri', '', type=str)

    if not subgraph_id:
        return jsonify(error='Subgraph id cannot be empty.')
    if not entity_uri or entity_uri.isspace():
        return jsonify(error='Entity URI cannot be empty.')

    if not subgraph_access(user_id, subgraph_id):
        return jsonify(error=MSG_SUBGRAPH_ACCESS.format(subgraph_id, user_id))

    subgraph_knowledge = get_subgraph_knowledge(subgraph_id)
    subgraph_knowledge.undo_delete_individual(entity_uri)

    return jsonify()
