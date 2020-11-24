"""Defines how knowledge is structured in python.
Specifically the translation of an rdf ontology into Python classes
"""

from flask import g
from rdflib import Graph
from rdflib import Literal
from rdflib import OWL
from rdflib import Namespace
from rdflib import RDF
from rdflib import RDFS
from rdflib import URIRef

from ratio.db import get_db


RATIO = Namespace('http://www.example.org/ratio-tool#')


def row_to_rdf(row):
    print(row['subject'])
    print(row['predicate'])
    print(row['object'])
    print(row['object_is_uri'])
    return URIRef(row['subject']), \
           URIRef(row['predicate']), \
           URIRef(row['object']) if row['object_is_uri'] else Literal(row['object'])


class Ontology:
    """Wrapper for rdflib.Graph that connects it to the database."""
    def __init__(self):
        self.graph = Graph()

        db = get_db()
        rows = db.execute('SELECT * FROM ontology').fetchall()
        for row in rows:
            self.graph.add(row_to_rdf(row))

    def load_ontology_file(self, file, rdf_format='turtle'):
        self.graph = Graph()
        self.graph.parse(file=file, format=rdf_format)

        db = get_db()
        db.execute('DELETE FROM ontology')

        for subject, predicate, object_ in self.graph[::]:
            db.execute('INSERT INTO ontology (subject, predicate, object, object_is_uri) VALUES (?, ?, ?, ?)',
                       (str(subject), str(predicate), str(object_), 1 if type(object_) == URIRef else 0))

        db.commit()


def get_ontology():
    """Get the Ontology.
    The connection is unique for each request and will be reused if this is called again.
    """
    if 'ontology' not in g:
        g.ontology = Ontology()

    return g.ontology


class SubgraphKnowledge:
    """Manages knowledge about in certain subgraph."""

    def __init__(self, subgraph_id):
        self.graph = Graph()
        self.id = subgraph_id

        db = get_db()

        self.root_uri = URIRef(db.execute('SELECT root FROM subgraph WHERE id = ?', (subgraph_id,)).fetchone()['root'])

        rows = db.execute(
            'SELECT subject, predicate, object, object_is_uri FROM knowledge WHERE subgraph_id = ?',
            (subgraph_id,)
        ).fetchall()
        for row in rows:
            self.graph.add(row_to_rdf(row))

    def get_root(self):
        return build_entity_from_knowledge(get_ontology().graph, self.graph, self.root_uri)

    def new_individual(self, class_uri):
        pass  # create the triples for a new individual, give it an unique uri


def get_subgraph_knowledge(subgraph_id):
    """Get SubgraphKnowledge of a certain subgraph.
    The connection is unique for each request and will be reused if this is called again.
    """
    if 'knowledge' not in g:
        g.knowledge = dict()

    if subgraph_id not in g.knowledge:
        g.knowledge[subgraph_id] = SubgraphKnowledge(subgraph_id)

    return g.knowledge[subgraph_id]


class Field:
    """Represents a possible owl:ObjectProperty or owl:DatatypeProperty of an Entity"""
    def __init__(self, property_uri, label, comment,
                 is_object_property, is_described, is_functional,
                 range_uri, values):
        self.property_uri = property_uri
        self.label = label
        self.comment = comment
        self.is_object_property = is_object_property
        self.is_described = is_described
        self.is_functional = is_functional
        self.range_uri = range_uri
        self.values = values


def build_empty_field(ontology, property_uri, range_class_uri):
    # currently properties don't have labels in the ontology but would be nice...
    label = ontology.objects(property_uri, RDFS.label)
    try:
        label = next(label)
    except StopIteration:
        label = property_uri.split('#')[-1]

    comment = ontology.objects(property_uri, RDFS.comment)
    try:
        comment = next(comment)
    except StopIteration:
        comment = None

    # if false, the field belongs to a owl:DatatypeProperty
    is_object_property = OWL.ObjectProperty in ontology.objects(property_uri, RDF.type)
    is_functional = OWL.FunctionalProperty in ontology.objects(property_uri, RDF.type)
    is_described = RATIO.Described in ontology.objects(range_class_uri, RDF.type)

    values = []

    return Field(property_uri, label, comment, is_object_property, is_described, is_functional, range_class_uri, values)


def build_field_from_knowledge(ontology, knowledge, individual_uri, property_uri, range_class_uri):
    # currently properties don't have labels in the ontology but would be nice...
    label = ontology.objects(property_uri, RDFS.label)
    try:
        label = next(label)
    except StopIteration:
        label = property_uri.split('#')[-1]

    comment = ontology.objects(property_uri, RDFS.comment)
    try:
        comment = next(comment)
    except StopIteration:
        comment = None

    # if false, the field belongs to a owl:DatatypeProperty
    is_object_property = OWL.ObjectProperty in ontology.objects(property_uri, RDF.type)
    is_functional = OWL.FunctionalProperty in ontology.objects(property_uri, RDF.type)
    is_described = RATIO.Described in ontology.objects(range_class_uri, RDF.type)

    values = list(knowledge.objects(individual_uri, property_uri))
    if is_object_property and is_described:
        values = [build_entity_from_knowledge(ontology, knowledge, value) for value in values]

    return Field(property_uri, label, comment, is_object_property, is_described, is_functional, range_class_uri, values)


class Entity:
    """Represents a owl:NamedIndividual"""
    def __init__(self, uri, label, comment, fields):
        self.uri = uri
        self.label = label
        self.comment = comment
        self.fields = fields  # fields s.t. field.property_uri rdfs:domain self.uri


def build_empty_entity(ontology, class_uri):
    nr = 123  # todo nr of objects of this type in db + 1
    uri = URIRef(class_uri + '_' + str(nr))

    # currently classes don't have labels in the ontology but would be nice
    class_label = ontology.objects(class_uri, RDFS.label)
    try:
        class_label = next(class_label)
    except StopIteration:
        # default label is the substring after the last '/' or '#' of the URI
        split = [s2 for s1 in class_label.split("#") for s2 in s1.split("/")]
        class_label = split[-1]
    label = class_label + ' ' + str(nr)  # just a default, can be changed by user

    comment = ontology.objects(class_uri, RDFS.comment)
    try:
        comment = next(comment)
    except StopIteration:
        comment = None

    fields = [
        build_empty_field(ontology, property_uri, range_uri)
        for property_uri in ontology.subjects(RDFS.domain, class_uri)
        for range_uri in ontology.objects(property_uri, RDFS.range)
    ]

    return Entity(uri, label, comment, fields)


def build_entity_from_knowledge(ontology, knowledge, uri):
    class_uri = None
    for o in knowledge.objects(uri, RDF.type):
        if o in ontology.subjects(RDF.type, RATIO.Described):
            class_uri = o
            break
    if class_uri is None:
        raise KeyError('No type found for individual ' + str(uri))

    label = next(knowledge.objects(uri, RDFS.label))

    comment = ontology.objects(class_uri, RDFS.comment)
    try:
        comment = next(comment)
    except StopIteration:
        comment = None

    fields = [
        build_field_from_knowledge(ontology, knowledge, uri, property_uri, range_uri)
        for property_uri in ontology.subjects(RDFS.domain, class_uri)
        for range_uri in ontology.objects(property_uri, RDFS.range)
    ]

    return Entity(uri, label, comment, fields)
