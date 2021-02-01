"""Defines how knowledge is structured in python.
Specifically the translation of an rdf ontology into Python classes
"""

# todo fix the messy class system: make a parent graph class with children ontology and subgraph knowledge
# todo encapsulate more functions into that classes
# todo maybe make a single api class for the rest of the system to interact with
# todo maybe fields don't actually have a list of child entities but a function to build them only when needed

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
TRUE = Literal('True', datatype=XSD.boolean)
FALSE = Literal('False', datatype=XSD.boolean)


def parse_n3_term(s):
    """Translates a n3 string s to an rdflib.URIRef, rdflib.Literal or rdflib.BNode.

    Only used to parse rows in the database stored using .n3(), not for parsing general rdf files!
    """

    if s.startswith('<') and s.endswith('>'):
        return URIRef(s[1:-1])
    elif s.startswith('"'):
        _, value, suffix = s.split('"""' if s.startswith('"""') else '"')
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


def get_tokens(graph, class_):
    classes = {class_}
    results = set()
    while classes:
        c = classes.pop()
        classes.update(graph.subjects(RDFS.subClassOf, c))
        results.update(graph.subjects(RDF.type, c))
    return results


class Ontology:
    """Wrapper for rdflib.Graph that connects it to the database."""
    def __init__(self):
        self.graph = Graph()

        db = get_db()
        for row in db.execute('SELECT * FROM ontology').fetchall():
            self.graph.add(row_to_rdf(row))

        for row in db.execute('SELECT * FROM namespace').fetchall():
            self.graph.namespace_manager.bind(row['prefix'], parse_n3_term(row['uri']))

    def load_rdf_file(self, file, rdf_format='turtle'):
        self.graph = Graph()
        self.graph.parse(file=file, format=rdf_format)

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
        return next(self.graph.objects(RATIO.Configuration, RATIO.hasBase))


def get_ontology():
    """Get the Ontology.
    The connection is unique for each request and will be reused if this is called again.
    """
    if 'ontology' not in g:
        g.ontology = Ontology()

    return g.ontology


class SubgraphKnowledge:
    """Manages knowledge about certain subgraph."""

    def __init__(self, subgraph_id):
        self.graph = Graph()
        self.id = subgraph_id

        db = get_db()

        rows = db.execute(
            'SELECT subject, predicate, object FROM knowledge WHERE subgraph_id = ?',
            (subgraph_id,)
        ).fetchall()
        for row in rows:
            self.graph.add(row_to_rdf(row))

        for row in db.execute('SELECT * FROM namespace').fetchall():
            self.graph.namespace_manager.bind(row['prefix'], parse_n3_term(row['uri']))

        self.root_uri = URIRef(db.execute('SELECT root FROM subgraph WHERE id = ?', (subgraph_id,)).fetchone()['root'])
        self.root = None

    def get_root(self):
        if self.root is None:
            self.root = build_entity_from_knowledge(get_ontology().graph, self.graph, self.root_uri)
        return self.root

    def get_entity(self, entity_uri):
        if type(entity_uri) == str:
            entity_uri = URIRef(entity_uri)

        stack = [self.get_root()]
        while stack:
            e = stack.pop()
            if e.uri == entity_uri:
                return e
            if isinstance(e, Entity):
                stack += [e2 for f in e.fields for e2 in f.values
                          if f.is_object_property and e2 is not None]

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

    def new_value(self, entity_uri, property_uri):
        entity = self.get_entity(entity_uri)
        field = self.get_field(entity_uri, property_uri)
        index = len(field.values)

        property_uri_index = URIRef(str(field.property_uri) + '_' + str(index))
        self.graph.add((entity.uri, property_uri_index, Literal('')))
        db = get_db()
        db.execute(
            'INSERT INTO knowledge (subgraph_id, subject, predicate, object) VALUES (?, ?, ?, ?)',
            (self.id, entity.uri.n3(), property_uri_index.n3(), Literal('').n3())
        )
        db.commit()

        self.root = None  # forces a rebuild of the root entity from the updated graph on the next request

        return index

    def change_value(self, entity_uri, property_uri, index, value):
        entity = self.get_entity(entity_uri)
        field = self.get_field(entity_uri, property_uri)

        validity, value = field.check_value(value)
        if validity:
            return validity

        property_uri_index = URIRef(str(property_uri) + '_' + str(index))
        self.graph.remove((entity.uri, property_uri_index, None))
        self.graph.add((entity.uri, property_uri_index, value))
        db = get_db()
        db.execute(
            'DELETE FROM knowledge WHERE subgraph_id = ? AND subject = ? AND predicate = ?',
            (self.id, entity.uri.n3(), property_uri_index.n3())
        )
        db.execute(
            'INSERT INTO knowledge (subgraph_id, subject, predicate, object) VALUES (?, ?, ?, ?)',
            (self.id, entity.uri.n3(), property_uri_index.n3(), value.n3())
        )
        db.commit()

        self.root = None  # forces a rebuild of the root entity from the updated graph on the next request

    def new_individual(self, class_uri, label, parent_uri, property_uri):
        class_uri = URIRef(class_uri)
        parent_uri = URIRef(parent_uri)
        property_uri = URIRef(property_uri)
        field = self.get_field(parent_uri, property_uri)
        index = len(field.values)

        property_uri_index = URIRef(str(field.property_uri) + '_' + str(index))

        # find an unique uri
        class_list = []
        stack = [self.get_root()]
        while stack:
            e = stack.pop()
            if e.class_uri == class_uri:
                class_list.append(int(e.uri.split('_')[-1]))
            if isinstance(e, Entity):
                stack += [e2 for f in e.fields for e2 in f.values
                          if f.is_object_property and e2 is not None]

        # todo I also have to check if there are deleted objects in memory that could be reanimated

        nr = next(i for i in range(1, max(class_list)+2) if i not in class_list)

        # construct a unique uri
        uri = URIRef('{}{}_{}_{}'.format(
            get_ontology().get_base(),
            class_uri.n3(get_ontology().graph.namespace_manager).split(':')[-1],  # try to remove the prefix
            self.id,
            nr
        ))

        #if label is None:  # todo would be nice to propose this default label in the frontend
        #    class_label = get_ontology().graph.objects(class_uri, RDFS.label)
        #    try:
        #        class_label = next(class_label)
        #    except StopIteration:
        #        # default label
        #        class_label = class_uri.n3(get_ontology().graph.namespace_manager).split(':')[-1]
        #    label = '{} {}'.format(class_label, nr)

        entity = build_empty_entity(get_ontology().graph, class_uri, uri, label)

        # new triples
        triples = [
            (parent_uri, property_uri_index, uri),
            (uri, RDF.type, OWL.NamedIndividual),
            (uri, RDF.type, class_uri),
            (uri, RDFS.label, Literal(label, datatype=XSD.string))
        ]

        # add triples to graph
        for t in triples:
            self.graph.add(t)

        # save add triples to database
        db = get_db()
        db.executemany(
            'INSERT INTO knowledge (subgraph_id, subject, predicate, object) VALUES (?, ?, ?, ?)',
            [(self.id, s.n3(), p.n3(), o.n3()) for s, p, o in triples]
        )
        db.commit()

        self.root = None  # forces a rebuild of the root entity from the updated graph on the next request

        return entity, index

    def delete_individual_recursive(self, uri):
        if type(uri) == str:
            uri = URIRef(uri)

        db = get_db()
        db_cursor = db.cursor()

        stack = {uri}
        while stack:
            u = stack.pop()
            stack.update((
                o for p, o in self.graph[u::] if o in self.graph.subjects()
            ))
            # remove links from parents
            self.graph.remove((None, None, u))
            db_cursor.execute(
                'INSERT INTO deleted_knowledge (subgraph_id, occasion, subject, predicate, object)'
                '   SELECT :subgraph_id, :occasion, subject, predicate, object FROM knowledge'
                '   WHERE subgraph_id = :subgraph_id AND object = :entity',
                {'subgraph_id': self.id, 'occasion': uri.n3(), 'entity': u.n3()}
            )
            db_cursor.execute(
                'DELETE FROM knowledge WHERE subgraph_id = :subgraph_id AND object = :entity',
                {'subgraph_id': self.id, 'entity': uri.n3()}
            )
            # remove links to children
            self.graph.remove((u, None, None))
            db_cursor.execute(
                'INSERT INTO deleted_knowledge (subgraph_id, occasion, subject, predicate, object)'
                '   SELECT :subgraph_id, :occasion, subject, predicate, object FROM knowledge'
                '   WHERE subgraph_id = :subgraph_id AND subject = :entity',
                {'subgraph_id': self.id, 'occasion': uri.n3(), 'entity': u.n3()}
            )
            db_cursor.execute(
                'DELETE FROM knowledge WHERE subgraph_id = :subgraph_id AND subject = :entity',
                {'subgraph_id': self.id, 'entity': u.n3()}
            )
        db.commit()

        self.root = None  # forces a rebuild of the root entity from the updated graph on the next request

    def undo_delete_individual(self, uri):
        if type(uri) == str:
            uri = URIRef(uri)

        db = get_db()
        db_cursor = db.cursor()

        rows = db_cursor.execute(
            'SELECT subject, predicate, object FROM deleted_knowledge'
            '   WHERE subgraph_id = :subgraph_id AND occasion = :occasion',
            {'subgraph_id': self.id, 'occasion': uri.n3()}
        ).fetchall()
        for row in rows:
            self.graph.add(row_to_rdf(row))

        db_cursor.execute(
            'INSERT INTO knowledge (subgraph_id, subject, predicate, object)'
            '   SELECT :subgraph_id, subject, predicate, object FROM deleted_knowledge'
            '   WHERE subgraph_id = :subgraph_id AND occasion = :occasion',
            {'subgraph_id': self.id, 'occasion': uri.n3()}
        )
        db_cursor.execute(
            'DELETE FROM deleted_knowledge WHERE subgraph_id = :subgraph_id AND occasion = :occasion',
            {'subgraph_id': self.id, 'occasion': uri.n3()}
        )
        db.commit()

        self.root = None  # forces a rebuild of the root entity from the updated graph on the next request

    def load_rdf_file(self, file, rdf_format='turtle'):
        self.graph = Graph()
        self.graph.parse(file=file, format=rdf_format)

        db = get_db()
        db.execute('DELETE FROM knowledge WHERE subgraph_id = ?', (self.id,))
        for subject, predicate, object_ in self.graph[::]:
            db.execute('INSERT INTO knowledge (subgraph_id, subject, predicate, object)'
                       ' VALUES (?, ?, ?, ?)',
                       (self.id, subject.n3(), predicate.n3(), object_.n3()))
        db.commit()

        self.root = None  # forces a rebuild of the root entity from the updated graph on the next request


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
                 is_object_property, is_described, show_label, is_functional,
                 range_uri, range_label, order, width, values, options=None):
        self.property_uri = property_uri
        self.label = label
        self.comment = comment
        self.is_object_property = is_object_property
        self.is_described = is_described
        self.show_label = show_label
        self.is_functional = is_functional
        self.range_uri = range_uri
        self.range_label = range_label
        self.order = order
        self.width = width
        self.values = values
        self.options = options

    def check_value(self, value):
        """Checks if the value is valid and transforms it into a corresponding rdflib.Literal
        Returns a pair of a validity message and the Literal
        If the value is valid the validity message is an emptystring.
        If the value is not valid instead of the literal, None is returned
        """
        if value == '':
            # Empty values are allowed but will be deleted on reloading the page
            pass
        elif self.is_object_property and self.options:
            uri = URIRef(value)
            if uri in (o.uri for o in self.options):
                return '', uri
            else:
                return 'Choose an option from the list.', None
        elif self.options:
            lit = Literal(value)
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
        elif self.range_uri == XSD.positiveInteger:
            try:
                i = int(value)
            except (ValueError, SyntaxError):
                return '{} is not a valid integer.'.format(value), None
            if i < 0:
                return '{} is not a positive value.'.format(value), None
        else:
            print('Unknown Datatype: {}'.format(self.range_uri))
        return '', Literal(value, datatype=self.range_uri)


class Option:
    def __init__(self, uri, label, class_uri, defined_by):
        self.uri = uri
        self.label = label
        self.class_uri = class_uri
        self.defined_by = defined_by


def build_option(ontology, uri):
    label = ontology.objects(uri, RDFS.label)
    try:
        label = next(label)
    except StopIteration:
        label = uri.n3(get_ontology().graph.namespace_manager).split(':')[-1]

    # todo would be nicer with sparql but unfortunately sparql query are very slow with rdflib
    # maybe consider using a real triple store?
    # rdflib works with sleepycat: https://github.com/RDFLib/rdflib/blob/master/examples/sleepycat_example.py
    # I'd need BerkeleyDB and bsddb3 (python bindings for BerkeleyDB)
    class_uri = None
    for o in ontology.objects(uri, RDF.type):
        if o in ontology.subjects(RDF.type, OWL.Class):  # A class defined in the ontology
            class_uri = o
            break
    if class_uri is None:
        raise KeyError('No type found for individual ' + str(uri))

    defined_by = ontology.objects(uri, RDFS.isDefinedBy)

    return Option(uri, label, class_uri, defined_by)


def build_empty_field(ontology, property_uri, range_class_uri):
    label = ontology.objects(property_uri, RDFS.label)
    try:
        label = next(label)
    except StopIteration:
        label = property_uri.n3(get_ontology().graph.namespace_manager).split(':')[-1]

    comment = ontology.objects(property_uri, RDFS.comment)
    try:
        comment = next(comment)
    except StopIteration:
        comment = None

    if type(range_class_uri) == BNode:
        range_label = 'Literal'
    else:
        range_label = ontology.objects(range_class_uri, RDFS.label)
        try:
            range_label = next(range_label)
        except StopIteration:
            range_label = range_class_uri.n3(get_ontology().graph.namespace_manager).split(':')[-1]

    # if false, the field belongs to a owl:DatatypeProperty
    is_object_property = OWL.ObjectProperty in ontology.objects(property_uri, RDF.type)
    is_functional = OWL.FunctionalProperty in ontology.objects(property_uri, RDF.type)
    is_described = TRUE in ontology.objects(property_uri, RATIO.described)
    show_label = FALSE not in ontology.objects(property_uri, RATIO.show_label)

    try:
        order = next(ontology.objects(property_uri, RATIO.order)).value
    except StopIteration:
        order = 0

    try:
        width = next(ontology.objects(property_uri, RATIO.width)).value
    except StopIteration:
        width = 50

    values = []  # todo add empty value to start with?

    one_of = list(ontology.objects(range_class_uri, OWL.oneOf))
    if is_object_property and not is_described:
        options = list(build_option(ontology, uri) for uri in ontology.subjects(RDF.type, range_class_uri))
        # todo: get individuals in subclasses of range_class also
        options.sort(key=lambda option: option.label)
    elif one_of:
        options = construct_list(ontology, one_of[0])
    elif range_class_uri == XSD.boolean:
        options = ['true', 'false']
    else:
        options = None

    return Field(property_uri, label, comment, is_object_property, is_described, show_label, is_functional,
                 range_class_uri, range_label, order, width, values, options)


def build_field_from_knowledge(ontology, knowledge, individual_uri, property_uri, range_class_uri):
    label = ontology.objects(property_uri, RDFS.label)
    try:
        label = next(label)
    except StopIteration:
        label = property_uri.n3(get_ontology().graph.namespace_manager).split(':')[-1]

    comment = ontology.objects(property_uri, RDFS.comment)
    try:
        comment = next(comment)
    except StopIteration:
        comment = None

    if type(range_class_uri) == BNode:
        range_label = 'Literal'
    else:
        range_label = ontology.objects(range_class_uri, RDFS.label)
        try:
            range_label = next(range_label)
        except StopIteration:
            range_label = range_class_uri.n3(get_ontology().graph.namespace_manager).split(':')[-1]

    # if false, the field belongs to a owl:DatatypeProperty
    is_object_property = OWL.ObjectProperty in ontology.objects(property_uri, RDF.type)
    is_functional = OWL.FunctionalProperty in ontology.objects(property_uri, RDF.type)
    is_described = TRUE in ontology.objects(property_uri, RATIO.described)
    show_label = FALSE not in ontology.objects(property_uri, RATIO.show_label)

    try:
        order = next(ontology.objects(property_uri, RATIO.order)).value
    except StopIteration:
        order = 0

    try:
        width = next(ontology.objects(property_uri, RATIO.width)).value
    except StopIteration:
        width = 50

    indices = [int(str(p)[len(str(property_uri))+1:])
               for p, o in knowledge[individual_uri::]
               if str(p).startswith(str(property_uri))]
    values = [next(knowledge[individual_uri:URIRef(str(property_uri) + '_' + str(i)):])
              if i in indices else None
              for i in range(max(indices, default=-1)+1)]

    if is_described:
        values = [None if (value is None or str(value) == '')
                  else build_entity_from_knowledge(ontology, knowledge, value)
                  for value in values]
    elif is_object_property:
        values = [None if (value is None or str(value) == '') else build_option(ontology, value)
                  for value in values]

    one_of = list(ontology.objects(range_class_uri, OWL.oneOf))
    if is_object_property and not is_described:
        options = list(build_option(ontology, uri) for uri in get_tokens(ontology, range_class_uri))
        options.sort(key=lambda option: option.label)
    elif one_of:
        options = construct_list(ontology, one_of[0])
    elif range_class_uri == XSD.boolean:
        options = ['true', 'false']
    else:
        options = None

    return Field(property_uri, label, comment, is_object_property, is_described, show_label, is_functional,
                 range_class_uri, range_label, order, width, values, options)


class Entity:
    """Represents a owl:NamedIndividual"""
    def __init__(self, uri, label, comment, class_uri, class_label, fields):
        self.uri = uri
        self.label = label
        self.comment = comment
        self.class_uri = class_uri
        self.class_label = class_label
        self.fields = fields  # fields s.t. field.property_uri rdfs:domain self.uri


def build_empty_entity(ontology, class_uri, uri, label):
    class_label = ontology.objects(class_uri, RDFS.label)
    try:
        class_label = next(class_label)
    except StopIteration:
        class_label = class_uri.n3(get_ontology().graph.namespace_manager).split(':')[-1]

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
    fields.sort(key=lambda field: field.order)

    # todo just for debugging, should be tested when uploading a new ontology
    if [f.order for f in fields] != list(range(1, len(fields)+1)):
        print('There is an error in the order of the fields of {}'.format(uri))
        print([(f.order, f.label) for f in fields])

    return Entity(uri, label, comment, class_uri, class_label, fields)


def build_entity_from_knowledge(ontology, knowledge, uri):
    # would be nicer with sparql query but that's very slow for some reason
    class_uri = None
    for o in knowledge.objects(uri, RDF.type):
        if o in ontology.subjects(RDF.type, OWL.Class):  # A class defined in the ontology
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

    class_label = ontology.objects(class_uri, RDFS.label)
    try:
        class_label = next(class_label)
    except StopIteration:
        class_label = class_uri.n3(get_ontology().graph.namespace_manager).split(':')[-1]

    fields = [
        build_field_from_knowledge(ontology, knowledge, uri, property_uri, range_uri)
        for property_uri in ontology.subjects(RDFS.domain, class_uri)
        for range_uri in ontology.objects(property_uri, RDFS.range)
    ]
    fields.sort(key=lambda field: field.order)

    # todo just for debugging, should be tested when uploading a new ontology
    if [f.order for f in fields] != list(range(1, len(fields)+1)):
        print('There is an error in the order of the fields of {}'.format(uri))
        print([(f.order, f.label) for f in fields])

    return Entity(uri, label, comment, class_uri, class_label, fields)
