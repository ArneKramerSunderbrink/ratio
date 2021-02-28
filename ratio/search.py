"""Functionality for searching the database"""

from flask import Blueprint
from flask import g
from flask import render_template
from rdflib import Graph
from rdflib import OWL
from rdflib import RDF
from rdflib import RDFS

from ratio.auth import login_required
from ratio.db import get_filter_description
from ratio.knowledge_model import RATIO, get_ontology, guess_label

bp = Blueprint('search', __name__)


@bp.route('/search')
@login_required
def search():
    filter_object = get_filter()
    return render_template('search.html', filter=filter_object)


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

        self.fields = [
            FilterField(property_uri, self.graph, get_ontology().graph)
            for property_uri in set(self.graph.subjects())
        ]
        self.fields.sort(key=lambda field: field.order)

        # todo just for debugging, should be tested when uploading a new ontology
        if [f.order for f in self.fields] != list(range(1, len(self.fields)+1)):
            print('There is an error in the order of the fields of the filter')
            print([(f.order, f.label) for f in self.fields])


class FilterField:
    def __init__(self, property_uri, filter_graph, ontology):
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
        self.is_functional = False

        try:
            self.order = next(ontology.objects(property_uri, RATIO.order)).value
        except StopIteration:
            self.order = 0

        try:
            self.width = next(ontology.objects(property_uri, RATIO.width)).value
        except StopIteration:
            self.width = 50

        self.is_add_option_allowed = False
        self.options = []  # todo add all values from all subgraphs

    def get_sorted_values(self):
        return []
