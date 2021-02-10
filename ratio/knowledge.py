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

    return jsonify(value_div=value_div)


@bp.route('/_change_value')
@login_required
def change_value():
    user_id = g.user['id']
    subgraph_id = request.args.get('subgraph_id', 0, type=int)
    entity_uri = request.args.get('entity_uri', '', type=str)
    property_uri = request.args.get('property_uri', '', type=str)
    index = request.args.get('index', -2, type=int)
    value = request.args.get('value', '', type=str).strip()

    if not subgraph_id:
        return jsonify(error='Subgraph id cannot be empty.')
    if not entity_uri or entity_uri.isspace():
        return jsonify(error='Entity URI cannot be empty.')
    if not property_uri or property_uri.isspace():
        return jsonify(error='Property URI cannot be empty.')
    if index < -1:
        return jsonify(error='Index cannot be empty.')

    if not subgraph_access(user_id, subgraph_id):
        return jsonify(error=MSG_SUBGRAPH_ACCESS.format(subgraph_id, user_id))

    subgraph_knowledge = get_subgraph_knowledge(subgraph_id)
    field = subgraph_knowledge.get_field(entity_uri, property_uri)

    if field.is_described:
        return jsonify(error='You have to use /_change_label to change the label of a described individual')

    if index == -1:
        index = subgraph_knowledge.new_value(entity_uri, property_uri)
    validity = subgraph_knowledge.change_value(entity_uri, property_uri, index, value)
    if validity:
        return jsonify(index=index, validity=validity)

    return jsonify(index=index)


@bp.route('/_add_option')
@login_required
def add_option():
    user_id = g.user['id']
    subgraph_id = request.args.get('subgraph_id', 0, type=int)
    entity_uri = request.args.get('entity_uri', '', type=str)
    property_uri = request.args.get('property_uri', '', type=str)
    label = request.args.get('label', '', type=str)

    if not subgraph_id:
        return jsonify(error='Subgraph id cannot be empty.')
    if not property_uri or property_uri.isspace():
        return jsonify(error='Property URI cannot be empty.')
    if not entity_uri or entity_uri.isspace():
        return jsonify(error='Entity URI cannot be empty.')
    if not label or label.isspace():
        return jsonify(error='Label cannot be empty.')

    if not subgraph_access(user_id, subgraph_id):
        return jsonify(error=MSG_SUBGRAPH_ACCESS.format(subgraph_id, user_id))

    subgraph_knowledge = get_subgraph_knowledge(subgraph_id)
    field = subgraph_knowledge.get_field(entity_uri, property_uri)

    if field.is_described:
        return jsonify(error='Use _add_entity to add entities to a described field.')
    if not field.is_add_option_allowed:
        return jsonify(error='Adding options to this field is not allowed.')

    option, option_fields = subgraph_knowledge.new_option(field.range_uri, label)

    render_option_div = get_template_attribute('tool/macros.html', 'option_div')
    option_div = render_option_div(option, True)

    return jsonify(option_div=option_div, option_fields=list(option_fields))


@bp.route('/_change_label')
@login_required
def change_label():
    user_id = g.user['id']
    subgraph_id = request.args.get('subgraph_id', 0, type=int)
    entity_uri = request.args.get('entity_uri', '', type=str)
    label = request.args.get('label', '', type=str)

    if not subgraph_id:
        return jsonify(error='Subgraph id cannot be empty.')
    if not entity_uri or entity_uri.isspace():
        return jsonify(error='Entity URI cannot be empty.')
    if not label or label.isspace():
        return jsonify(error='Label cannot be empty.')

    if not subgraph_access(user_id, subgraph_id):
        return jsonify(error=MSG_SUBGRAPH_ACCESS.format(subgraph_id, user_id))

    subgraph_knowledge = get_subgraph_knowledge(subgraph_id)

    entity = subgraph_knowledge.get_entity(entity_uri)
    if not entity.is_deletable:
        return jsonify(error='You are not allowed to change the label of this entity.')

    subgraph_knowledge.change_label(entity_uri, label)

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

    if not field.is_deletable:
        return jsonify(error='You are not allowed to add entities to this field.')

    if field.is_functional and field.values:
        return jsonify(error='You cannot add more than one value to this field.')

    entity, index = subgraph_knowledge.new_individual(field.range_uri, entity_label, parent_uri, property_uri)

    render_entity_div = get_template_attribute('tool/macros.html', 'entity_div')
    entity_div = render_entity_div(entity, False, index)

    option_fields = {str(f.property_uri) for f in subgraph_knowledge.get_fields()
                     if f.is_object_property and not f.is_described and f.range_uri == entity.class_uri}
    if option_fields:
        render_option_div = get_template_attribute('tool/macros.html', 'option_div')
        option_div = render_option_div(entity, True)
        return jsonify(entity_div=entity_div, remove_plus=field.is_functional,
                       option_fields=list(option_fields), option_div=option_div)

    return jsonify(entity_div=entity_div, remove_plus=field.is_functional)


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

    entity = subgraph_knowledge.get_entity(entity_uri)
    if not entity.is_deletable:
        return jsonify(error='You are not allowed to delete this entity.')

    deleted = subgraph_knowledge.delete_individual_recursive(entity_uri)

    return jsonify(deleted=list(deleted))


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
