"""Functionality for searching the database"""

from flask import Blueprint
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
from ratio.knowledge_model import RATIO, build_option, get_subgraph_knowledge, get_ontology, guess_label, Option, \
    parse_n3_term, row_to_rdf

bp = Blueprint('search', __name__)


@bp.route('/overview')
@login_required
def search_view():
    filter_object = get_filter()

    db = get_db()
    rows = db.execute(
        'SELECT id, name FROM subgraph WHERE finished = 1 AND deleted = 0',
    ).fetchall()

    return render_template('search.html', filter=filter_object, results=rows)


@bp.route('/_search')
@login_required
def search():
    filter_data = {p: request.args.get(p, '', type=str) for p in request.args}

    # get list of subgraphs that are finished and not deleted
    db = get_db()
    rows = db.execute(
        'SELECT id FROM subgraph WHERE finished = 1 AND deleted = 0',
    ).fetchall()
    subgraphs = {row['id'] for row in rows}

    results = subgraphs.copy()
    # todo this should be a method of the filter
    for id_ in subgraphs:
        knowledge = {(str(p), str(o)) for s, p, o in get_subgraph_knowledge(id_).get_root().get_triples()}
        for po in filter_data.items():
            if po in knowledge:
                continue
            else:
                results.remove(id_)
                break

    return jsonify(results=[str(id_) for id_ in results])


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

        # todo just for debugging, should be tested when uploading a new ontology
        if [f.order for f in self.fields] != list(range(1, len(self.fields)+1)):
            print('There is an error in the order of the fields of the filter')
            print([(f.order, f.label) for f in self.fields])


class FilterField:
    def __init__(self, property_uri, filter_graph, ontology, knowledge):
        self.property_uri = property_uri

        self.label = ontology.objects(property_uri, RDFS.label)
        try:
            self.label = next(self.label)
        except StopIteration:
            self.label = guess_label(property_uri)

        self.comment = ontology.objects(property_uri, RDFS.comment)
        try:
            self.comment = next(self.comment)
        except StopIteration:
            self.comment = None

        self.is_object_property = OWL.ObjectProperty in ontology.objects(property_uri, RDF.type)
        self.is_described = False
        self.is_deletable = False
        self.is_functional = True

        try:
            self.order = next(filter_graph.objects(property_uri, RATIO.order)).value
        except StopIteration:
            self.order = 0

        try:
            self.width = next(filter_graph.objects(property_uri, RATIO.width)).value
        except StopIteration:
            self.width = 50

        self.is_add_option_allowed = False
        self.options = []
        for i, o in [(p[len(property_uri)+1:], o) for s, p, o in knowledge[::] if p.startswith(property_uri)]:
            try:
                int(i)
            except ValueError:
                continue
            self.options.append(o)

        self.options = list(set(self.options))
        if self.is_object_property:
            self.options = [build_option(ontology, knowledge, o) for o in self.options]
            self.options.append(Option('', '', '', False))
        else:
            self.options.append('')

    def get_sorted_values(self):
        return []
