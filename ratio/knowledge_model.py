"""Defines how knowledge is structured in python.
Specifically the translation of an rdf ontology into Python classes
"""

from collections import defaultdict
from itertools import count
from re import fullmatch

from flask import g
from rdflib import BNode
from rdflib import Graph
from rdflib import Literal
from rdflib import OWL
from rdflib import Namespace
from rdflib import RDF
from rdflib import RDFS
from rdflib import URIRef
from rdflib import XSD

from ratio.db import get_db


RATIO = Namespace('http://www.example.org/ratio-tool#')
TRUE = Literal('true', datatype=XSD.boolean)
FALSE = Literal('false', datatype=XSD.boolean)


def parse_n3_term(s):
    """Translates a n3 string s to an rdflib.URIRef, rdflib.Literal or rdflib.BNode.

    Only used to parse rows in the database stored using .n3(), not for parsing general rdf files!
    """

    if s.startswith('<') and s.endswith('>'):
        return URIRef(s[1:-1])
    elif s.startswith('"'):
        # value surrounded by unescaped quotes, can contain escaped quotes
        # the suffix cannot contain quotes
        value, suffix = fullmatch(r'(?:"""|")((?:(?:[^"]|\\")*[^\\])?)(?:"""|")([^"]*)', s).group(1, 2)
        if suffix:
            if suffix.startswith('@'):
                return Literal(value, lang=suffix[1:])
            elif suffix.startswith('^^'):
                return Literal(value, datatype=URIRef(suffix[3:-1]))
            else:
                raise ValueError('{} cannot be parsed'.format(s))
        else:
            return Literal(value)
    elif s.startswith('_:'):
        return BNode(s[2:])
    else:
        raise ValueError('{} cannot be parsed'.format(s))


def construct_list(ontology, list_node):
    """For parsing a rdf:List."""
    list_ = []
    while list_node != RDF.nil:
        list_.append(next(ontology.objects(list_node, RDF.first)))
        list_node = next(ontology.objects(list_node, RDF.rest))
    return list_


def row_to_rdf(row):
    """Turns a row from the database into a rdf triple."""
    subject = parse_n3_term(row['subject'])
    predicate = parse_n3_term(row['predicate'])
    object_ = parse_n3_term(row['object'])
    return subject, predicate, object_


def get_subclasses(graph, class_):
    stack = {class_}
    subclasses = set()
    while stack:
        c = stack.pop()
        stack.update(graph[:RDFS.subClassOf:c])
        subclasses.update(graph[:RDFS.subClassOf:c])
    return subclasses


def get_superclasses(graph, class_):
    stack = {class_}
    superclasses = set()
    while stack:
        c = stack.pop()
        stack.update(graph[c:RDFS.subClassOf:])
        superclasses.update(graph[c:RDFS.subClassOf:])
    return superclasses


def get_tokens(graph, class_):
    classes = {class_}
    classes.update(get_subclasses(graph, class_))
    tokens = set()
    for c in classes:
        tokens.update(graph[:RDF.type:c])
    return tokens


def get_uri_suffix(uri):
    # returns the tail of the uri string that does not contain # or :
    return fullmatch(r'(?:.*[:#])*([^:#]*)', uri).group(1)


class Ontology:
    """Wrapper for rdflib.Graph that connects it to the database."""
    def __init__(self):
        self.graph = Graph()

        db = get_db()
        for row in db.execute('SELECT * FROM ontology').fetchall():
            self.graph.add(row_to_rdf(row))

        for row in db.execute('SELECT * FROM namespace').fetchall():
            self.graph.namespace_manager.bind(row['prefix'], parse_n3_term(row['uri']))

    def load_rdf_data(self, data, rdf_format='turtle'):
        self.graph = Graph()
        if type(data) == str:
            self.graph.parse(data=data, format=rdf_format)
        else:
            self.graph.parse(file=data, format=rdf_format)

        db = get_db()
        db.execute('DELETE FROM ontology')

        for subject, predicate, object_ in self.graph[::]:
            db.execute('INSERT INTO ontology (subject, predicate, object) VALUES (?, ?, ?)',
                       (subject.n3(), predicate.n3(), object_.n3()))

        for prefix, uri in self.graph.namespaces():
            db.execute('INSERT INTO namespace (prefix, uri) VALUES (?, ?)',
                       (prefix, uri.n3()))

        db.commit()

    def get_base(self):
        # The prefix for new URIs created in the tool
        return next(self.graph.objects(RATIO.Configuration, RATIO.hasBase))

    def is_functional(self, property_uri):
        if type(property_uri) == str:
            property_uri = URIRef(property_uri)
        return OWL.FunctionalProperty in self.graph.objects(property_uri, RDF.type)


def get_ontology():
    """Get the Ontology.
    The connection is unique for each request and will be reused if this is called again.
    """
    if 'ontology' not in g:
        g.ontology = Ontology()

    return g.ontology


class SubgraphKnowledge:
    """Manages knowledge about a subgraph."""

    def __init__(self, subgraph_id):
        self.id = subgraph_id
        self.graph = Graph()
        # since rdf triples are not ordered but the values of the property fields in the tool are we need to store this
        # additional information outside the rdf graph object:
        self.properties = defaultdict(dict)
        self.root = None

        db = get_db()

        for row in db.execute('SELECT * FROM namespace').fetchall():
            self.graph.namespace_manager.bind(row['prefix'], parse_n3_term(row['uri']))

        for row in db.execute(
            'SELECT subject, predicate, object, property_index, deleted FROM knowledge WHERE subgraph_id = ?',
            (subgraph_id,)
        ).fetchall():
            subject, predicate, object_ = row_to_rdf(row)
            index = row['property_index']
            deleted = row['deleted']
            if deleted is None:
                self.graph.add((subject, predicate, object_))
            if index is not None:
                self.properties[(subject, predicate)][index] = object_

    def get_root(self):
        if self.root is None:
            root_uri = next(self.graph[:RATIO.isRoot:TRUE])
            self.root = Entity.from_knowledge(self.id, root_uri, False)
        return self.root

    def get_entity(self, entity_uri):
        if type(entity_uri) == str:
            entity_uri = URIRef(entity_uri)

        stack = [self.get_root()]
        # we don't need to keep track of what we visited because the graph with only is_described-properties as edges
        # has to be a tree to be displayed in the interface anyway
        while stack:
            e = stack.pop()
            if e.uri == entity_uri:
                return e
            stack += [f.values[i] for f in e.fields for i in f.values if f.is_described]

        raise KeyError('No entity with URI {} found.'.format(entity_uri))

    def get_field(self, entity_uri, property_uri):
        if type(entity_uri) == str:
            entity_uri = URIRef(entity_uri)
        if type(property_uri) == str:
            property_uri = URIRef(property_uri)

        e = self.get_entity(entity_uri)
        for f in e.fields:
            if f.property_uri == property_uri:
                return f

        raise KeyError('No field with URI {} found.'.format(property_uri))

    def get_fields(self, filter_function=lambda f: True):
        fields = []
        stack = [self.get_root()]
        # we don't need to keep track of what we visited because the graph with only is_described-properties as edges
        # has to be a tree to be displayed in the interface anyway
        while stack:
            e = stack.pop()
            fields += filter(filter_function, e.fields)
            stack += [f.values[i] for f in e.fields for i in f.values if f.is_described]
        return fields

    def new_value(self, entity_uri, property_uri):
        if type(entity_uri) == str:
            entity_uri = URIRef(entity_uri)
        if type(property_uri) == str:
            property_uri = URIRef(property_uri)

        index = max(self.properties[(entity_uri, property_uri)].keys(), default=0) + 1
        value = Literal('')

        self.graph.add((entity_uri, property_uri, value))
        self.properties[(entity_uri, property_uri)][index] = value
        db = get_db()
        db.execute(
            'INSERT INTO knowledge (subgraph_id, subject, predicate, object, property_index) VALUES (?, ?, ?, ?, ?)',
            (self.id, entity_uri.n3(), property_uri.n3(), value.n3(), index)
        )
        db.commit()

        self.root = None  # forces a rebuild of the root entity

        return index

    def change_value(self, entity_uri, property_uri, index, value):
        if type(entity_uri) == str:
            entity_uri = URIRef(entity_uri)
        if type(property_uri) == str:
            property_uri = URIRef(property_uri)

        field = self.get_field(entity_uri, property_uri)

        validity, value = field.check_value(value)
        if validity:
            # the check returned an error message
            return validity

        self.graph.remove((entity_uri, property_uri, None))
        self.graph.add((entity_uri, property_uri, value))
        self.properties[(entity_uri, property_uri)][index] = value
        db = get_db()
        db.execute(
            'UPDATE knowledge SET object = ? '
            '   WHERE subgraph_id = ? AND subject = ? AND predicate = ? AND property_index = ?',
            (value.n3(), self.id, entity_uri.n3(), property_uri.n3(), index)
        )
        db.commit()

        self.root = None  # forces a rebuild of the root entity

    def change_label(self, entity_uri, label):
        entity_uri = URIRef(entity_uri)

        label = Literal(label)

        self.graph.remove((entity_uri, RDFS.label, None))
        self.graph.add((entity_uri, RDFS.label, label))

        db = get_db()
        db.execute(
            'UPDATE knowledge SET object = ? '
            '   WHERE subgraph_id = ? AND subject = ? AND predicate = ?',
            (label.n3(), self.id, entity_uri.n3(), RDFS.label.n3())
        )
        db.commit()

        self.root = None  # forces a rebuild of the root entity

    def new_individual(self, class_uri, label, parent_uri, property_uri):
        if type(class_uri) == str:
            class_uri = URIRef(class_uri)
        if type(parent_uri) == str:
            parent_uri = URIRef(parent_uri)
        if type(property_uri) == str:
            property_uri = URIRef(property_uri)
        label = Literal(label, datatype=XSD.string)

        field = self.get_field(parent_uri, property_uri)

        # place in the list of values of the parent
        value_index = max(self.properties[(parent_uri, property_uri)].keys(), default=0) + 1

        # construct a unique uri
        db = get_db()
        used_uris = {str(parse_n3_term(row['subject'])) for row in db.execute(
            'SELECT DISTINCT subject FROM knowledge'
        ).fetchall()}

        uri = '{}{}_{}_'.format(
            get_ontology().get_base(),
            get_uri_suffix(class_uri),
            self.id
        )

        uri = URIRef(next(uri + str(i) for i in count(1) if uri + str(i) not in used_uris))

        entity = Entity.new(self.id, class_uri, uri, label, field.is_deletable)

        # update triples
        triples = [
            (parent_uri, property_uri, uri, value_index),
            (uri, RDF.type, OWL.NamedIndividual, None),
            (uri, RDF.type, class_uri, None),
            (uri, RDFS.label, label, None)
        ]

        # add triples to graph
        for s, p, o, i in triples:
            self.graph.add((s, p, o))

        # add triples to database
        db.executemany(
            'INSERT INTO knowledge (subgraph_id, subject, predicate, object, property_index) VALUES (?, ?, ?, ?, ?)',
            [(self.id, s.n3(), p.n3(), o.n3(), i) for s, p, o, i in triples]
        )
        db.commit()

        self.root = None  # forces a rebuild of the root entity

        # fields with a list of options where the new entity has to be added
        option_fields = self.get_fields(
            filter_function=lambda f: f.is_object_property and not f.is_described and f.range_uri == entity.class_uri)

        return entity, value_index, option_fields

    def delete_individual_recursive(self, uri):
        if type(uri) == str:
            uri = URIRef(uri)

        db = get_db()
        db_cursor = db.cursor()

        stack = [self.get_entity(uri)]
        deleted = []
        while stack:
            e = stack.pop()
            u = e.uri
            deleted.append(str(u))
            stack += [f.values[i] for f in e.fields for i in f.values if f.is_described]

            # remove links from parents
            self.graph.remove((None, None, u))
            db_cursor.execute(
                'UPDATE knowledge SET deleted = ? WHERE subgraph_id = ? AND object = ? AND deleted IS NULL',
                (uri.n3(), self.id, u.n3())
            )

            # remove links to children
            self.graph.remove((u, None, None))
            db_cursor.execute(
                'UPDATE knowledge SET deleted = ? WHERE subgraph_id = ? AND subject = ? AND deleted IS NULL',
                (uri.n3(), self.id, u.n3())
            )
        db.commit()

        self.root = None  # forces a rebuild of the root entity

        return deleted

    def undo_delete_individual(self, uri):
        if type(uri) == str:
            uri = URIRef(uri)

        db = get_db()

        rows = db.execute(
            'SELECT subject, predicate, object FROM knowledge WHERE subgraph_id = ? AND deleted = ?',
            (self.id, uri.n3())
        ).fetchall()

        for row in rows:
            self.graph.add(row_to_rdf(row))

        db.execute(
            'UPDATE knowledge SET deleted = NULL WHERE subgraph_id = ? AND deleted = ?',
            (self.id, uri.n3())
        )

        db.commit()

        self.root = None  # forces a rebuild of the root entity

    def new_option(self, class_uri, label):
        if type(class_uri) == str:
            class_uri = URIRef(class_uri)
        label = Literal(label, datatype=XSD.string)

        # construct a unique uri
        db = get_db()
        used_uris = {str(parse_n3_term(row['subject'])) for row in db.execute(
            'SELECT DISTINCT subject FROM knowledge'
        ).fetchall()}

        uri = '{}{}_{}_'.format(
            get_ontology().get_base(),
            get_uri_suffix(class_uri),
            self.id
        )
        uri = URIRef(next(uri + str(i) for i in count(1) if uri + str(i) not in used_uris))

        option = Option(uri, label, class_uri, TRUE)

        # update triples
        triples = [
            (uri, RDF.type, OWL.NamedIndividual),
            (uri, RDF.type, class_uri),
            (uri, RDFS.label, label),
            (uri, RATIO.isCustom, TRUE)
        ]

        # add triples to graph
        for t in triples:
            self.graph.add(t)

        # add triples to database
        db.executemany(
            'INSERT INTO knowledge (subgraph_id, subject, predicate, object) VALUES (?, ?, ?, ?)',
            [(self.id, s.n3(), p.n3(), o.n3()) for s, p, o in triples]
        )
        db.commit()

        self.root = None  # forces a rebuild of the root entity

        # collect all property URIs where this new option needs to be attached to the range in the frontend
        ontology = get_ontology().graph
        classes = {class_uri}
        classes.update(get_superclasses(ontology, class_uri))
        properties = {p for c in classes for p in ontology[:RDFS.range:c]
                      if TRUE not in ontology[p:RATIO.described:]}

        return option, properties

    def load_rdf_data(self, data, rdf_format='turtle'):
        self.graph = Graph()
        self.properties = defaultdict(dict)
        if type(data) == str:
            self.graph.parse(data=data, format=rdf_format)
        else:
            self.graph.parse(file=data, format=rdf_format)

        db = get_db()
        db.execute('DELETE FROM knowledge WHERE subgraph_id = ?', (self.id,))
        for subject, predicate, object_ in self.graph[::]:
            index = None
            if (subject, predicate) in self.properties:
                index = max(self.properties[(subject, predicate)].keys()) + 1
                self.properties[(subject, predicate)][index] = object_
            elif predicate in get_ontology().graph[:RDF.type:OWL.ObjectProperty] \
                    or predicate in get_ontology().graph[:RDF.type:OWL.DatatypeProperty]:
                index = 1
                self.properties[(subject, predicate)][index] = object_
            db.execute('INSERT INTO knowledge (subgraph_id, subject, predicate, object, property_index)'
                       ' VALUES (?, ?, ?, ?, ?)',
                       (self.id, subject.n3(), predicate.n3(), object_.n3(), index))
        db.commit()

        self.root = None  # forces a rebuild of the root entity
        self.get_root()  # to test immediately whether everything is building correctly

    def get_graph(self, clean=False, ontology=False):
        graph = Graph()
        graph.namespace_manager = self.graph.namespace_manager

        for t in self.graph[::]:
            graph.add(t)

        if ontology:
            for t in get_ontology().graph[::]:
                graph.add(t)

        if clean:
            graph.remove((None, RATIO.isRoot, None))
            # remove unused custom options
            for s in graph[:RATIO.isCustom:TRUE]:
                if s not in graph.objects():
                    graph.remove((s, None, None))
            if ontology:
                graph.remove((RATIO.Configuration, None, None))
                graph.remove((None, RATIO.deletable, None))
                graph.remove((None, RATIO.described, None))
                graph.remove((None, RATIO.order, None))
                graph.remove((None, RATIO.width, None))
                graph.remove((None, None, RATIO.Subheading))

        return graph

    def get_serialization(self, rdf_format='turtle', clean=True, ontology=False):
        return self.get_graph(clean, ontology).serialize(format=rdf_format)


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
                 type_, is_described, is_deletable, is_functional,
                 range_uri, range_label,
                 order, width, values, is_add_option_allowed, options=None):
        self.property_uri = property_uri
        self.label = label
        self.comment = comment
        self.type = type_
        self.is_described = is_described
        self.is_deletable = is_deletable
        self.is_functional = is_functional
        self.range_uri = range_uri
        self.range_label = range_label
        self.order = order
        self.width = width
        self.values = values
        self.is_add_option_allowed = is_add_option_allowed
        self.options = options

    @property
    def is_object_property(self):
        return self.type == 'ObjectProperty'

    @property
    def is_datatype_property(self):
        return self.type == 'DatatypeProperty'

    @property
    def is_subheading(self):
        return self.type == 'Subheading'

    def check_value(self, value):
        """Checks if the value is valid and transforms it into a corresponding rdflib.Literal
        Returns a pair of a validity message and the Literal
        If the value is valid the validity message is an emptystring.
        If the value is not valid instead of the literal, None is returned
        """
        if value == '':
            # Empty values are allowed but will be deleted on reloading the page
            # (they are persisted in the db though because I have not found out what's the best occasion to delete
            # them yet..)
            return '', Literal(value)
        elif self.is_object_property and self.options:
            uri = URIRef(value)
            if uri in (o.uri for o in self.options):
                return '', uri
            else:
                return 'Choose an option from the list.', None
        elif self.options:
            lit = Literal(value, datatype=XSD.boolean) if self.range_uri == XSD.boolean else Literal(value)
            if lit in self.options:
                return '', lit
            else:
                return 'Choose an option from the list.', None
        elif self.range_uri == RDFS.Literal:
            pass
        elif self.range_uri == XSD.string:
            pass
        elif self.range_uri == XSD.float:
            try:
                float(value)
            except (ValueError, SyntaxError):
                return '{} is not a valid float.'.format(value), None
        elif self.range_uri == XSD.integer:
            try:
                int(value)
            except (ValueError, SyntaxError):
                return '{} is not a valid integer.'.format(value), None
        elif self.range_uri == XSD.nonNegativeInteger:
            try:
                i = int(value)
            except (ValueError, SyntaxError):
                return '{} is not a valid integer.'.format(value), None
            if i < 0:
                return '{} is not a non-negative value.'.format(value), None
        elif self.range_uri == XSD.positiveInteger:
            try:
                i = int(value)
            except (ValueError, SyntaxError):
                return '{} is not a valid integer.'.format(value), None
            if i <= 0:
                return '{} is not a positive value.'.format(value), None
        else:
            return 'Unknown Datatype: {}'.format(self.range_uri), None
        return '', Literal(value, datatype=self.range_uri)

    def get_sorted_values(self):
        """Get (index, value)-pairs for non empty values sorted by index."""
        if self.is_object_property:
            if self.is_described:
                return sorted(self.values.items(), key=lambda i: i[0])
            else:
                non_empty = [i for i in self.values if type(self.values[i]) != Literal]
        else:
            non_empty = [i for i in self.values if self.values[i].value != '']
        return sorted([(i, self.values[i]) for i in non_empty], key=lambda iv: iv[0])

    # Factories
    @classmethod
    def from_knowledge(cls, subgraph_id, individual_uri, property_uri):
        knowledge = get_subgraph_knowledge(subgraph_id).graph
        ontology = get_ontology().graph

        label = next(ontology[property_uri:RDFS.label:], None)
        if label is None:
            label = get_uri_suffix(property_uri)

        comment = next(ontology[property_uri:RDFS.comment:], None)

        order = int(next(ontology.objects(property_uri, RATIO.order), 0))

        if RATIO.Subheading in ontology[property_uri:RDF.type:]:
            return cls.subheading(property_uri, label, comment, order)

        range_class_uri = next(ontology[property_uri:RDFS.range:])
        if type(range_class_uri) == BNode:
            range_label = 'Literal'
        else:
            range_label = next(ontology[range_class_uri:RDFS.label:], None)
            if range_label is None:
                range_label = get_uri_suffix(range_class_uri)

        # Are the range objects described by a user in the tool
        is_range_described = any(TRUE in ontology[p:RATIO.described:] for p in ontology[:RDFS.range:range_class_uri])

        type_ = 'ObjectProperty' if OWL.ObjectProperty in ontology.objects(property_uri, RDF.type) \
            else 'DatatypeProperty'
        is_functional = OWL.FunctionalProperty in ontology[property_uri:RDF.type:]
        is_described = TRUE in ontology[property_uri:RATIO.described:]
        is_deletable = FALSE not in ontology[property_uri:RATIO.deletable:]

        width = int(next(ontology[property_uri:RATIO.width:], 50))

        values = get_subgraph_knowledge(subgraph_id).properties[(individual_uri, property_uri)]
        # filter values from deleted triples:
        values = {i: values[i] for i in values if values[i] in knowledge[individual_uri:property_uri:]}

        if is_described:
            values = {i: Entity.from_knowledge(subgraph_id, values[i], is_deletable)
                      for i in values if str(values[i]) != ''}
        elif type_ == 'ObjectProperty':
            values = {i: Option.from_knowledge(subgraph_id, values[i])
                      for i in values if str(values[i]) != ''}

        one_of = next(ontology[range_class_uri:OWL.oneOf:], None)
        if type_ == 'ObjectProperty' and not is_described:
            options = [Option.from_knowledge(subgraph_id, uri) for uri in get_tokens(ontology, range_class_uri)]
            # options added by the user:
            options += [Option.from_knowledge(subgraph_id, uri) for uri in get_tokens(knowledge, range_class_uri)]
            options.sort(key=lambda option: option.label)
        elif one_of is not None:
            options = construct_list(ontology, one_of)
        elif range_class_uri == XSD.boolean:
            options = [TRUE, FALSE]
        else:
            options = None

        is_add_option_allowed = type_ == 'ObjectProperty' and not is_range_described

        return cls(property_uri, label, comment, type_, is_described, is_deletable, is_functional,
                   range_class_uri, range_label, order, width, values, is_add_option_allowed, options)

    @classmethod
    def new(cls, subgraph_id, property_uri):
        knowledge = get_subgraph_knowledge(subgraph_id).graph
        ontology = get_ontology().graph

        label = next(ontology[property_uri:RDFS.label:], None)
        if label is None:
            label = get_uri_suffix(property_uri)

        comment = next(ontology[property_uri:RDFS.comment:], None)

        order = int(next(ontology.objects(property_uri, RATIO.order), 0))

        if RATIO.Subheading in ontology.objects(property_uri, RDF.type):
            return cls.subheading(property_uri, label, comment, order)

        range_class_uri = next(ontology[property_uri:RDFS.range:])
        if type(range_class_uri) == BNode:
            range_label = 'Literal'
        else:
            range_label = next(ontology[range_class_uri:RDFS.label:], None)
            if range_label is None:
                range_label = get_uri_suffix(range_class_uri)

        is_range_described = any(TRUE in ontology[p:RATIO.described:] for p in ontology[:RDFS.range:range_class_uri])

        type_ = 'ObjectProperty' if OWL.ObjectProperty in ontology.objects(property_uri, RDF.type) \
            else 'DatatypeProperty'
        is_functional = OWL.FunctionalProperty in ontology[property_uri:RDF.type:]
        is_described = TRUE in ontology[property_uri:RATIO.described:]
        is_deletable = FALSE not in ontology[property_uri:RATIO.deletable:]

        width = int(next(ontology[property_uri:RATIO.width:], 50))

        values = dict()

        one_of = next(ontology[range_class_uri:OWL.oneOf:], None)
        if type_ == 'ObjectProperty' and not is_described:
            options = [Option.from_knowledge(subgraph_id, uri) for uri in get_tokens(ontology, range_class_uri)]
            # options added by the user:
            options += [Option.from_knowledge(subgraph_id, uri) for uri in get_tokens(knowledge, range_class_uri)]
            options.sort(key=lambda option: option.label)
        elif one_of is not None:
            options = construct_list(ontology, one_of)
        elif range_class_uri == XSD.boolean:
            options = [TRUE, FALSE]
        else:
            options = None

        is_add_option_allowed = type_ == 'ObjectProperty' and not is_range_described

        return cls(property_uri, label, comment, type_, is_described, is_deletable, is_functional,
                   range_class_uri, range_label, order, width, values, is_add_option_allowed, options)

    @classmethod
    def subheading(cls, property_uri, label, comment, order):
        return cls(property_uri, label, comment, 'Subheading', False, False, True,
                   None, None, order, None, dict(), False, [])


class Option:
    def __init__(self, uri, label, class_uri, is_custom, comment=None):
        self.uri = uri
        self.label = label
        self.class_uri = class_uri
        self.is_custom = is_custom
        self.comment = comment

    # Factory
    @classmethod
    def from_knowledge(cls, subgraph_id, uri):
        """Searches for an individual with the given URI and a type defined in the ontology."""

        knowledge = get_subgraph_knowledge(subgraph_id).graph
        ontology = get_ontology().graph

        if uri in ontology.subjects():
            graph = ontology
        elif uri in knowledge.subjects():
            graph = knowledge
        else:
            raise ValueError('{} was not found in the ontology or the knowledge.'.format(uri))

        label = next(graph[uri:RDFS.label:], None)
        if label is None:
            label = get_uri_suffix(uri)

        comment = next(graph[uri:RDFS.comment:], None)

        class_uri = None
        for o in graph[uri:RDF.type:]:
            if o in ontology[:RDF.type:OWL.Class]:  # A class defined in the graph
                class_uri = o
                break
        if class_uri is None:
            raise KeyError('No type found for option ' + str(uri))

        is_custom = TRUE in knowledge[uri:RATIO.isCustom:]

        return cls(uri, label, class_uri, is_custom, comment)


class Entity:
    """Represents a owl:NamedIndividual"""
    def __init__(self, uri, label, comment, class_uri, class_label, fields, is_deletable):
        self.uri = uri
        self.label = label
        self.comment = comment
        self.class_uri = class_uri
        self.class_label = class_label
        self.fields = fields  # fields s.t. field.property_uri rdfs:domain self.uri
        self.is_deletable = is_deletable

    # Factories
    @classmethod
    def from_knowledge(cls, subgraph_id, uri, is_deletable):
        knowledge = get_subgraph_knowledge(subgraph_id).graph
        ontology = get_ontology().graph

        # todo would be nicer with sparql query but that's very slow for some reason
        # maybe consider using a real triple store?
        # rdflib works with sleepycat: https://github.com/RDFLib/rdflib/blob/master/examples/sleepycat_example.py
        # I'd need BerkeleyDB and bsddb3 (python bindings for BerkeleyDB)
        class_uri = None
        for o in knowledge[uri:RDF.type:]:
            if o in ontology[:RDF.type:OWL.Class]:  # A class defined in the ontology
                class_uri = o
                break
        if class_uri is None:
            raise ValueError('No type found for individual ' + str(uri))

        label = next(knowledge[uri:RDFS.label:], None)
        if label is None:
            label = get_uri_suffix(uri)

        comment = next(ontology[class_uri:RDFS.comment:], None)

        class_label = next(ontology[class_uri:RDFS.label:], None)
        if class_label is None:
            class_label = get_uri_suffix(class_uri)

        fields = [
            Field.from_knowledge(subgraph_id, uri, property_uri)
            for property_uri in ontology[:RDFS.domain:class_uri]
        ]
        fields.sort(key=lambda field: field.order)

        # todo just for debugging, should be tested when uploading a new ontology
        if [f.order for f in fields] != list(range(1, len(fields) + 1)):
            print('There is an error in the order of the fields of {}'.format(uri))
            print([(f.order, f.label) for f in fields])

        return cls(uri, label, comment, class_uri, class_label, fields, is_deletable)

    @classmethod
    def new(cls, subgraph_id, class_uri, uri, label, is_deletable):
        ontology = get_ontology().graph

        class_label = next(ontology[class_uri:RDFS.label:], None)
        if class_label is None:
            class_label = get_uri_suffix(class_uri)

        comment = next(ontology[class_uri:RDFS.comment:], None)

        fields = [
            Field.new(subgraph_id, property_uri)
            for property_uri in ontology.subjects(RDFS.domain, class_uri)
        ]
        fields.sort(key=lambda field: field.order)

        # todo just for debugging, should be tested when uploading a new ontology
        if [f.order for f in fields] != list(range(1, len(fields)+1)):
            print('There is an error in the order of the fields of {}'.format(uri))
            print([(f.order, f.label) for f in fields])

        return cls(uri, label, comment, class_uri, class_label, fields, is_deletable)

