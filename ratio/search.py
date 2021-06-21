"""Functionality for searching the database"""

from flask import Blueprint
from flask import current_app
from flask import g
from flask import get_template_attribute
from flask import jsonify
from flask import render_template
from flask import request
from rdflib import Graph
from rdflib import OWL
from rdflib import RDF
from rdflib import RDFS

from ratio.auth import login_required
from ratio.db import get_db, get_filter_description
from ratio.knowledge_model import RATIO, Option, get_subgraph_knowledge, get_ontology, get_uri_suffix, \
    parse_n3_term, row_to_rdf

bp = Blueprint('search', __name__, url_prefix='/search')


@bp.route('')
@login_required
def search_view():
    filter_object = get_filter()

    db = get_db()
    rows = db.execute(
        'SELECT id, name FROM access JOIN subgraph ON subgraph_id = id'
        ' WHERE deleted = 0  AND finished = 1'
    ).fetchall()

    return render_template('tool/search.html', filter=filter_object, subgraphs=rows)


@bp.route('_search', methods=['POST'])
@login_required
def search():
    filter_data = request.json

    # todo get_result(filter_data) should be a method of the filter
    # get list of subgraphs that are finished and not deleted
    db = get_db()
    rows = db.execute(
        'SELECT id FROM access JOIN subgraph ON subgraph_id = id'
        ' WHERE deleted = 0 AND finished = 1'
    ).fetchall()
    results = {row['id'] for row in rows}
    knowledge = {subgraph_id: {(str(p), str(o))
                               for s, p, o in get_subgraph_knowledge(subgraph_id).get_graph(clean=True)}
                 for subgraph_id in results}
    results = filter(lambda subgraph_id: all(po in knowledge[subgraph_id] for po in filter_data.items()), results)

    return jsonify(results=[str(subgraph_id) for subgraph_id in results])


@bp.route('/_get_overview', methods=['POST'])
@login_required
def get_overview():
    subgraph_id = request.json.get('subgraph_id')

    if subgraph_id is None:
        return jsonify(error='Subgraph id cannot be empty.')
    try:
        subgraph_id = int(subgraph_id)
    except ValueError:
        return jsonify(error='{} id has to be an integer.'
                       .format(current_app.config['FRONTEND_CONFIG']['Subgraph_term']))

    db = get_db()
    subgraph = db.execute(
        'SELECT * FROM subgraph WHERE id = ?', (subgraph_id,)
    ).fetchone()

    if subgraph is None:
        return jsonify(error='{} with id {} does not exist.'.format(
            current_app.config['FRONTEND_CONFIG']['Subgraph_term'], subgraph_id
        ))

    if not subgraph['finished']:
        return jsonify(error='You have no access to {} with id {}.'.format(
            current_app.config['FRONTEND_CONFIG']['subgraph_term'], subgraph_id
        ))

    render_overview_table = get_template_attribute('tool/overview_table.html', 'overview')
    overview_table = render_overview_table(get_subgraph_knowledge(subgraph_id).get_graph(clean=True, ontology=True))

    return jsonify(overview_table=overview_table)


def get_filter():
    if 'filter' not in g:
        g.filter = Filter()

    return g.filter


class Filter:
    def __init__(self):
        self.graph = Graph()
        self.graph.parse(data=get_filter_description(), format='ttl')

        self.uri = RATIO.Filter
        self.label = 'Filter'
        self.comment = ''
        self.is_deletable = False

        self.knowledge = Graph()
        db = get_db()
        for row in db.execute('SELECT * FROM namespace').fetchall():
            self.knowledge.namespace_manager.bind(row['prefix'], parse_n3_term(row['uri']))

        rows = db.execute(
            'SELECT subject, predicate, object FROM knowledge WHERE subgraph_id IN ('
            '   SELECT id FROM subgraph WHERE finished = 1 AND deleted = 0'
            ')',
        ).fetchall()
        for row in rows:
            self.knowledge.add(row_to_rdf(row))

        self.fields = [
            FilterField(property_uri, self.graph, get_ontology().graph, self.knowledge)
            for property_uri in set(self.graph.subjects())
        ]
        self.fields.sort(key=lambda field: field.order)

        # todo just for debugging, should be tested when uploading a new filter.ttl
        # also, check that there are no described fields
        if [f.order for f in self.fields] != list(range(1, len(self.fields)+1)):
            print('There is an error in the order of the fields of the filter')
            print([(f.order, f.label) for f in self.fields])


class FilterField:
    # todo much of this is redundant code from class Field, should be implemented in the same place
    # having to update this in two different places already caused problems in the past
    def __init__(self, property_uri, filter_graph, ontology, knowledge):
        self.property_uri = property_uri

        self.label = ontology.objects(property_uri, RDFS.label)
        try:
            self.label = next(self.label)
        except StopIteration:
            self.label = get_uri_suffix(property_uri)

        self.comment = ontology.objects(property_uri, RDFS.comment)
        try:
            self.comment = next(self.comment)
        except StopIteration:
            self.comment = None

        try:
            self.order = next(filter_graph.objects(property_uri, RATIO.order)).value
        except StopIteration:
            self.order = 0

        self.is_described = False
        self.is_deletable = False
        self.is_functional = True
        self.is_add_option_allowed = False

        if RATIO.Subheading in ontology.objects(property_uri, RDF.type):
            self.type = 'Subheading'
            self.width = None
            self.options = []
            return

        if OWL.ObjectProperty in ontology.objects(property_uri, RDF.type):
            self.type = 'ObjectProperty'
        else:
            self.type = 'DatatypeProperty'

        try:
            self.width = next(filter_graph.objects(property_uri, RATIO.width)).value
        except StopIteration:
            self.width = 50

        self.options = list({o for o in knowledge.objects(predicate=property_uri) if str(o) != ''})
        if self.is_object_property:
            self.options = [Option.from_ontology(o) for o in self.options]
            self.options.append(Option('', '', ''))
        else:
            self.options.append('')

    @property
    def is_object_property(self):
        return self.type == 'ObjectProperty'

    @property
    def is_datatype_property(self):
        return self.type == 'DatatypeProperty'

    @property
    def is_subheading(self):
        return self.type == 'Subheading'

    def get_sorted_values(self):
        return []
