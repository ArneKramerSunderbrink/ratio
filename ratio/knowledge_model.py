"""Defines how knowledge is structured in python."""

from rdflib import OWL
from rdflib import RDF
from rdflib import RDFS
from rdflib import URIRef


class Field:
    """Represents a possible owl:ObjectProperty or owl:DatatypeProperty of an Entity"""
    def __init__(self, property_uri, label, comment, is_object_property, is_functional, range_uri, values):
        self.property_uri = property_uri
        self.label = label
        self.comment = comment
        self.is_object_property = is_object_property
        self.is_functional = is_functional
        self.range_uri = range_uri
        self.values = values


def build_empty_field(ontology, property_uri, range_uri):
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

    values = []

    return Field(property_uri, label, comment, is_object_property, is_functional, range_uri, values)


class Entity:
    """Represents a owl:NamedIndividual"""
    def __init__(self, uri, label, comment, fields):
        self.uri = uri
        self.label = label
        self.comment = comment
        self.fields = fields  # fields s.t. field.property_uri rdfs:domain self.uri


def build_empty_entity(ontology, type_uri):
    nr = 123  # todo nr of objects of this type in db + 1
    uri = URIRef(type_uri + '_' + str(nr))

    # currently classes don't have labels in the ontology but would be nice
    type_label = ontology.objects(type_uri, RDFS.label)
    try:
        type_label = next(type_label)
    except StopIteration:
        type_label = type_uri.split('#')[-1]
    label = type_label + ' ' + str(nr)  # just a default, can be changed by user

    comment = ontology.objects(type_uri, RDFS.comment)
    try:
        comment = next(comment)
    except StopIteration:
        comment = None

    fields = [
        build_empty_field(ontology, property_uri, range_uri)
        for property_uri in ontology.subjects(RDFS.domain, type_uri)
        for range_uri in ontology.objects(property_uri, RDFS.range)
    ]

    return Entity(uri, label, comment, fields)
