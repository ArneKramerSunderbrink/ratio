"""Functionality related to editing of knowledge."""

from flask import Blueprint
from flask import current_app
from flask import g
from flask import get_template_attribute
from flask import jsonify
from flask import request
from flask import url_for

from ratio.auth import login_required
from ratio.auth import subgraph_access
from ratio.knowledge_model import get_subgraph_knowledge, get_ontology

MSG_SUBGRAPH_ACCESS = 'Subgraph with id {} does not exist or is not owned by user {} currently logged in.'

bp = Blueprint('knowledge', __name__)


@bp.route('/_add_value', methods=['POST'])
@login_required
def add_value():
    user_id = g.user['id']
    subgraph_id = request.json.get('subgraph_id')
    property_uri = request.json.get('property_uri')
    entity_uri = request.json.get('entity_uri')

    if subgraph_id is None:
        return jsonify(error='Subgraph id cannot be empty.')
    try:
        subgraph_id = int(subgraph_id)
    except ValueError:
        return jsonify(error='{} id has to be an integer.'
                       .format(current_app.config['FRONTEND_CONFIG']['Subgraph_term']))
    if not property_uri or property_uri.isspace():
        return jsonify(error='Property URI cannot be empty.')
    if not entity_uri or property_uri.isspace():
        return jsonify(error='Entity URI cannot be empty.')

    if not subgraph_access(user_id, subgraph_id):
        return jsonify(error=MSG_SUBGRAPH_ACCESS.format(subgraph_id, user_id))

    subgraph_knowledge = get_subgraph_knowledge(subgraph_id)
    field = subgraph_knowledge.get_field(entity_uri, property_uri)

    if field.is_described:
        return jsonify(error='You have to use {} to add a described individual'.format(url_for('knowledge.add_entity')))
    if field.is_functional and field.values:
        return jsonify(error='You cannot add more than one value to this field.')

    index = subgraph_knowledge.new_value(entity_uri, property_uri)

    if field.options is None:
        render_value_div = get_template_attribute('tool/edit_macros.html', 'value_free')
    else:
        render_value_div = get_template_attribute('tool/edit_macros.html', 'value_options')
    value_div = render_value_div(field, '', index)

    return jsonify(value_div=value_div)


@bp.route('/_change_value', methods=['POST'])
@login_required
def change_value():
    user_id = g.user['id']
    subgraph_id = request.json.get('subgraph_id')
    entity_uri = request.json.get('entity_uri')
    property_uri = request.json.get('property_uri')
    index = request.json.get('index')
    value = request.json.get('value').strip()

    if subgraph_id is None:
        return jsonify(error='Subgraph id cannot be empty.')
    try:
        subgraph_id = int(subgraph_id)
    except ValueError:
        return jsonify(error='{} id has to be an integer.'
                       .format(current_app.config['FRONTEND_CONFIG']['Subgraph_term']))
    if not entity_uri or entity_uri.isspace():
        return jsonify(error='Entity URI cannot be empty.')
    if not property_uri or property_uri.isspace():
        return jsonify(error='Property URI cannot be empty.')
    if index is None:
        return jsonify(error='Index cannot be empty.')
    try:
        index = int(index)
    except ValueError:
        return jsonify(error='Index has to be an integer.')
    if value is None:
        return jsonify(error='Value cannot be empty.')

    if not subgraph_access(user_id, subgraph_id):
        return jsonify(error=MSG_SUBGRAPH_ACCESS.format(subgraph_id, user_id))

    subgraph_knowledge = get_subgraph_knowledge(subgraph_id)

    if get_ontology().is_property_described(property_uri):
        return jsonify(error='You have to use /_change_label to change the label of a described individual')

    if index == subgraph_knowledge.get_property_free_index(entity_uri, property_uri):
        subgraph_knowledge.new_value(entity_uri, property_uri)
    validity = subgraph_knowledge.change_value(entity_uri, property_uri, index, value.strip())
    if validity:
        return jsonify(validity=validity)

    return jsonify()


@bp.route('/_add_option', methods=['POST'])
@login_required
def add_option():
    # If an index is given, the corresponding value is changed to the new option
    user_id = g.user['id']
    user_uri = g.user['uri']
    subgraph_id = request.json.get('subgraph_id')
    entity_uri = request.json.get('entity_uri')
    property_uri = request.json.get('property_uri')
    label = request.json.get('label')
    index = request.json.get('index')

    if subgraph_id is None:
        return jsonify(error='Subgraph id cannot be empty.')
    try:
        subgraph_id = int(subgraph_id)
    except ValueError:
        return jsonify(error='{} id has to be an integer.'
                       .format(current_app.config['FRONTEND_CONFIG']['Subgraph_term']))
    if not property_uri or property_uri.isspace():
        return jsonify(error='Property URI cannot be empty.')
    if not label or label.isspace():
        return jsonify(error='Label cannot be empty.')

    if not subgraph_access(user_id, subgraph_id):
        return jsonify(error=MSG_SUBGRAPH_ACCESS.format(subgraph_id, user_id))

    subgraph_knowledge = get_subgraph_knowledge(subgraph_id)
    ontology = get_ontology()

    if ontology.is_property_described(property_uri):
        return jsonify(error='Use _add_entity to add entities to a described field.')
    if not ontology.is_property_add_custom_option_allowed(property_uri):
        return jsonify(error='Adding options to this field is not allowed.')

    option, option_fields = ontology.new_option(ontology.get_property_range(property_uri), label, user_uri)

    if index is not None:
        try:
            index = int(index)
        except ValueError:
            return jsonify(error='Index has to be an integer.')
        # not only add the option to the ontology but also to the list of values of the field
        if not entity_uri or entity_uri.isspace():
            return jsonify(error='Entity URI cannot be empty.')

        if index == subgraph_knowledge.get_property_free_index(entity_uri, property_uri):
            index = subgraph_knowledge.new_value(entity_uri, property_uri)
        subgraph_knowledge.change_value(entity_uri, property_uri, index, option.uri)

    render_option_div = get_template_attribute('tool/edit_macros.html', 'option_div')
    option_div = render_option_div(option, True)

    return jsonify(option_div=option_div, option_fields=list(option_fields),
                   option_label=option.label, option_uri=option.uri, index=index)


@bp.route('/_change_label', methods=['POST'])
@login_required
def change_label():
    user_id = g.user['id']
    subgraph_id = request.json.get('subgraph_id')
    entity_uri = request.json.get('entity_uri')
    label = request.json.get('label')

    if subgraph_id is None:
        return jsonify(error='{} id cannot be empty.'.format(current_app.config['FRONTEND_CONFIG']['Subgraph_term']))
    try:
        subgraph_id = int(subgraph_id)
    except ValueError:
        return jsonify(error='{} id has to be an integer.'
                       .format(current_app.config['FRONTEND_CONFIG']['Subgraph_term']))
    if not entity_uri or entity_uri.isspace():
        return jsonify(error='Entity URI cannot be empty.')
    if not label or label.isspace():
        return jsonify(error='Label cannot be empty.')

    if not subgraph_access(user_id, subgraph_id):
        return jsonify(error=MSG_SUBGRAPH_ACCESS.format(subgraph_id, user_id))

    subgraph_knowledge = get_subgraph_knowledge(subgraph_id)

    if not subgraph_knowledge.is_individual_deletable(entity_uri):
        return jsonify(error='You are not allowed to change the label of this entity.')

    subgraph_knowledge.change_label(entity_uri, label.strip())

    return jsonify()


@bp.route('/_add_entity', methods=['POST'])
@login_required
def add_entity():
    user_id = g.user['id']
    subgraph_id = request.json.get('subgraph_id')
    property_uri = request.json.get('property_uri')
    parent_uri = request.json.get('entity_uri')
    entity_label = request.json.get('label')

    if subgraph_id is None:
        return jsonify(error='{} id cannot be empty.'.format(current_app.config['FRONTEND_CONFIG']['Subgraph_term']))
    try:
        subgraph_id = int(subgraph_id)
    except ValueError:
        return jsonify(error='{} id has to be an integer.'
                       .format(current_app.config['FRONTEND_CONFIG']['Subgraph_term']))
    if not property_uri or property_uri.isspace():
        return jsonify(error='Property URI cannot be empty.')
    if not parent_uri or parent_uri.isspace():
        return jsonify(error='Parent URI cannot be empty.')
    if not entity_label or entity_label.isspace():
        return jsonify(error='Entity label cannot be empty.')

    if not subgraph_access(user_id, subgraph_id):
        return jsonify(error=MSG_SUBGRAPH_ACCESS.format(subgraph_id, user_id))

    subgraph_knowledge = get_subgraph_knowledge(subgraph_id)
    ontology = get_ontology()
    field_is_deletable = ontology.is_property_deletable(property_uri)
    field_is_functional = ontology.is_property_functional(property_uri)
    field_values = subgraph_knowledge.get_property_values(parent_uri, property_uri)
    field_range = ontology.get_property_range(property_uri)

    if not field_is_deletable:
        return jsonify(error='You are not allowed to add entities to this field.')

    if field_is_functional and field_values:
        return jsonify(error='You cannot add more than one value to this field.')

    index = subgraph_knowledge.new_value(parent_uri, property_uri)
    entity, option_fields = subgraph_knowledge.new_individual(field_range, entity_label, True)
    subgraph_knowledge.change_value(parent_uri, property_uri, index, entity.uri)

    render_entity_div = get_template_attribute('tool/edit_macros.html', 'entity_div')
    entity_div = render_entity_div(entity, index=index, is_deletable=field_is_deletable, collapsed=False)

    if option_fields:
        option_fields = [str(f.property_uri) for f in option_fields]
        render_option_div = get_template_attribute('tool/edit_macros.html', 'option_div')
        option_div = render_option_div(entity, True)
        return jsonify(entity_div=entity_div, remove_plus=field_is_functional,
                       option_fields=option_fields, option_div=option_div)

    return jsonify(entity_div=entity_div, remove_plus=field_is_functional)


@bp.route('/_delete_entity', methods=['POST'])
@login_required
def delete_entity():
    user_id = g.user['id']
    subgraph_id = request.json.get('subgraph_id')
    entity_uri = request.json.get('entity_uri')
    property_uri = request.json.get('property_uri')

    if subgraph_id is None:
        return jsonify(error='{} id cannot be empty.'.format(current_app.config['FRONTEND_CONFIG']['Subgraph_term']))
    try:
        subgraph_id = int(subgraph_id)
    except ValueError:
        return jsonify(error='{} id has to be an integer.'
                       .format(current_app.config['FRONTEND_CONFIG']['Subgraph_term']))
    if not entity_uri or entity_uri.isspace():
        return jsonify(error='Entity URI cannot be empty.')

    if not subgraph_access(user_id, subgraph_id):
        return jsonify(error=MSG_SUBGRAPH_ACCESS.format(subgraph_id, user_id))

    subgraph_knowledge = get_subgraph_knowledge(subgraph_id)

    if not subgraph_knowledge.is_individual_deletable(entity_uri):
        return jsonify(error='You are not allowed to delete this entity.')

    deleted = subgraph_knowledge.delete_individual_recursive(entity_uri)

    if property_uri:
        is_functional = get_ontology().is_property_functional(property_uri)
        return jsonify(deleted=deleted, functional=is_functional)

    return jsonify(deleted=deleted)


@bp.route('/_undo_delete_entity', methods=['POST'])
@login_required
def undo_delete_entity():
    user_id = g.user['id']
    subgraph_id = request.json.get('subgraph_id')
    entity_uri = request.json.get('entity_uri')

    if subgraph_id is None:
        return jsonify(error='{} id cannot be empty.'.format(current_app.config['FRONTEND_CONFIG']['Subgraph_term']))
    try:
        subgraph_id = int(subgraph_id)
    except ValueError:
        return jsonify(error='{} id has to be an integer.'
                       .format(current_app.config['FRONTEND_CONFIG']['Subgraph_term']))
    if not entity_uri or entity_uri.isspace():
        return jsonify(error='Entity URI cannot be empty.')

    if not subgraph_access(user_id, subgraph_id):
        return jsonify(error=MSG_SUBGRAPH_ACCESS.format(subgraph_id, user_id))

    # TODO actually we should check whether restoring the information would violate any
    #  functional property constraints, but that would be very complicated and currently we
    #  have no described functional deletable entities where that could happen

    subgraph_knowledge = get_subgraph_knowledge(subgraph_id)
    subgraph_knowledge.undo_delete_individual(entity_uri)

    return jsonify()
