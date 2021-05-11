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
        try:
            value, suffix = fullmatch(r'(?:"""|")((?:(?:[^"]|\\")*[^\\])?)(?:"""|")([^"]*)', s).group(1, 2)
        except AttributeError:
            raise ValueError('{} cannot be parsed'.format(s))
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


# todo the general graph functions in a graph parent class
def get_label(graph, uri):
    if type(uri) == str:
        uri = URIRef(uri)

    if type(uri) == BNode:
        return 'Literal'
    label = next(graph[uri:RDFS.label:], None)
    if label is None:
        label = get_uri_suffix(uri)
    return label


def get_subclasses(graph, class_uri):
    if type(class_uri) == str:
        class_uri = URIRef(class_uri)

    stack = {class_uri}
    subclasses = set()
    while stack:
        c = stack.pop()
        stack.update(graph[:RDFS.subClassOf:c])
        subclasses.update(graph[:RDFS.subClassOf:c])
    return subclasses


def get_superclasses(graph, class_uri):
    if type(class_uri) == str:
        class_uri = URIRef(class_uri)

    stack = {class_uri}
    superclasses = set()
    while stack:
        c = stack.pop()
        stack.update(graph[c:RDFS.subClassOf:])
        superclasses.update(graph[c:RDFS.subClassOf:])
    return superclasses


def get_tokens(graph, class_uri):
    if type(class_uri) == str:
        class_uri = URIRef(class_uri)

    classes = {class_uri}
    classes.update(get_subclasses(graph, class_uri))
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

        # todo check if the graph works: build root
        #  check if property orders: [f.order for f in fields] != list(range(1, len(fields) + 1))

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

    # Provide information about the things described by the ontology
    def get_label(self, uri):
        return get_label(self.graph, uri)

    def get_comment(self, uri):
        if type(uri) == str:
            uri = URIRef(uri)

        return next(self.graph[uri:RDFS.comment:], None)

    def get_tokens(self, class_uri):
        return get_tokens(self.graph, class_uri)

    # Information specific to properties
    def get_property_order(self, uri):
        if type(uri) == str:
            uri = URIRef(uri)

        return int(next(self.graph[uri:RATIO.order:], 0))

    def get_property_type(self, uri):
        if type(uri) == str:
            uri = URIRef(uri)

        if RATIO.Subheading in self.graph[uri:RDF.type:]:
            return 'Subheading'
        elif OWL.ObjectProperty in self.graph[uri:RDF.type:]:
            return 'ObjectProperty'
        elif OWL.DatatypeProperty in self.graph[uri:RDF.type:]:
            return 'DatatypeProperty'
        else:
            raise ValueError('Now known type found for property {}'.format(uri))

    def get_property_range(self, uri):
        if type(uri) == str:
            uri = URIRef(uri)

        return next(self.graph[uri:RDFS.range:], None)

    def get_property_width(self, uri):
        if type(uri) == str:
            uri = URIRef(uri)

        return int(next(self.graph[uri:RATIO.width:], 50))

    def is_property_add_custom_option_allowed(self, uri):
        if type(uri) == str:
            uri = URIRef(uri)

        if self.get_property_type(uri) != 'ObjectProperty':
            return False
        else:
            # Are the range objects described by a user in the tool
            return not any(self.is_property_described(p) for p in self.graph[:RDFS.range:self.get_property_range(uri)])

    def is_property_deletable(self, uri):
        if type(uri) == str:
            uri = URIRef(uri)

        return FALSE not in self.graph[uri:RATIO.deletable:]

    def is_property_described(self, uri):
        if type(uri) == str:
            uri = URIRef(uri)

        return TRUE in self.graph[uri:RATIO.described:]

    def is_property_functional(self, uri):
        if type(uri) == str:
            uri = URIRef(uri)

        return OWL.FunctionalProperty in self.graph[uri:RDF.type:]

    def check_property_value(self, property_uri, value, subgraph_id):
        """Checks if the value is valid and transforms it into a corresponding rdflib Literal or URIRef
        Returns a pair of a validity message and the Literal/URIRef
        If the value is valid the validity message is an emptystring.
        If the value is not valid instead of the literal, None is returned
        """
        knowledge = get_subgraph_knowledge(subgraph_id)  # todo once custom options are global this can be removed
        type_ = self.get_property_type(property_uri)
        is_object_property = type_ == 'ObjectProperty'
        is_described = self.is_property_described(property_uri)
        range_uri = self.get_property_range(property_uri)

        # TODO custom options should be stored globally, than I can put all this into the Ontology class
        # todo create option list only when needed the the if-elif-chain below
        one_of = next(self.graph[range_uri:OWL.oneOf:], None)
        if is_object_property and not is_described:
            options = [Option.from_knowledge(subgraph_id, uri) for uri in self.get_tokens(range_uri)]
            # options added by the user:
            options += [Option.from_knowledge(subgraph_id, uri) for uri in knowledge.get_tokens(range_uri)]
            options.sort(key=lambda option: option.label)
        elif one_of is not None:
            options = construct_list(self.graph, one_of)
        elif range_uri == XSD.boolean:
            options = [TRUE, FALSE]
        else:
            options = None

        if value == '':
            # Empty values are allowed but will be deleted on reloading the page
            # (they are persisted in the db though because I have not found out what's the best occasion to delete
            # them yet..)
            return '', Literal(value)
        elif is_object_property and options:
            uri = value if type(value) == URIRef else URIRef(value)
            if uri in (o.uri for o in options):
                return '', uri
            else:
                return 'Choose an option from the list.', None
        elif is_object_property and is_described:
            # we trust that the individual has the correct class, namely self.range_uri
            uri = value if type(value) == URIRef else URIRef(value)
            return '', uri
        elif options:
            lit = Literal(value, datatype=XSD.boolean) if range_uri == XSD.boolean else Literal(value)
            if lit in options:
                return '', lit
            else:
                return 'Choose an option from the list.', None
        elif range_uri == RDFS.Literal:
            pass
        elif range_uri == XSD.string:
            pass
        elif range_uri == XSD.float:
            try:
                float(value)
            except (ValueError, SyntaxError):
                return '{} is not a valid float.'.format(value), None
        elif range_uri == XSD.integer:
            try:
                int(value)
            except (ValueError, SyntaxError):
                return '{} is not a valid integer.'.format(value), None
        elif range_uri == XSD.nonNegativeInteger:
            try:
                i = int(value)
            except (ValueError, SyntaxError):
                return '{} is not a valid integer.'.format(value), None
            if i < 0:
                return '{} is not a non-negative value.'.format(value), None
        elif range_uri == XSD.positiveInteger:
            try:
                i = int(value)
            except (ValueError, SyntaxError):
                return '{} is not a valid integer.'.format(value), None
            if i <= 0:
                return '{} is not a positive value.'.format(value), None
        else:
            return 'Unknown Datatype: {}'.format(range_uri), None
        return '', Literal(value, datatype=range_uri)

    # Information specific to classes
    def get_class_properties(self, uri):
        if type(uri) == str:
            uri = URIRef(uri)

        return self.graph[:RDFS.domain:uri]


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
        self.properties = defaultdict(dict)  # includes deleted! (There has to be a better name for this?)
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
        """Get a representation of the root of the subgraph and all its descendants
        This is used to provide the information for rendering to Jinja.
        Don't use it to check things like entity.label - knowledge.get_label(uri) is more efficient.
        """
        if self.root is None:
            root_uri = next(self.graph[:RATIO.isRoot:TRUE])
            self.root = Entity.from_knowledge(self.id, root_uri)
        return self.root

    def get_entity(self, entity_uri):
        """Get a representation of a owl:NamedIndividual
        This is used to provide the information about an individual for rendering to Jinja.
        Don't use it to check things like entity.label - knowledge.get_label(uri) is more efficient.
        """
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
        """Get a representation of an owl:ObjectProperty or owl:DatatypeProperty of an Entity
        This is used to provide the information about a field for rendering to Jinja.
        Don't use it to check things like field.label - ontology.get_label(property_uri) is more efficient.
        """
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

        validity, value = get_ontology().check_property_value(property_uri, value, self.id)
        if validity:
            # the check returned an error message
            return validity

        db = get_db()

        # delete previous value from graph
        prev_value = db.execute(
            'SELECT object FROM knowledge '
            '   WHERE subgraph_id = ? AND subject = ? AND predicate = ? AND property_index = ?',
            (self.id, entity_uri.n3(), property_uri.n3(), index)
        ).fetchone()['object']
        self.graph.remove((entity_uri, property_uri, parse_n3_term(prev_value)))

        # add new value to graph
        self.graph.add((entity_uri, property_uri, value))
        self.properties[(entity_uri, property_uri)][index] = value
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

    def new_individual(self, class_uri, label, get_option_fields=False):
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

        entity = Entity.new(self.id, class_uri, uri, label)

        # update triples
        triples = [
            (uri, RDF.type, OWL.NamedIndividual),
            (uri, RDF.type, class_uri),
            (uri, RDFS.label, label)
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

        if get_option_fields:
            # fields with a list of options where the new entity has to be added
            option_fields = self.get_fields(
                filter_function=lambda f: f.is_object_property and not f.is_described and f.range_uri == entity.class_uri)
            return entity, option_fields

        return entity

    def delete_individual_recursive(self, uri):
        if type(uri) == str:
            uri = URIRef(uri)

        db = get_db()
        db_cursor = db.cursor()

        stack = [uri]
        deleted = []
        while stack:
            u = stack.pop()
            deleted.append(str(u))
            stack += self.get_individual_children(u)

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
        ontology = get_ontology()
        classes = {class_uri}
        classes.update(get_superclasses(ontology, class_uri))
        properties = {p for c in classes for p in ontology[:RDFS.range:c]
                      if ontology.is_property_described(p)}

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

    def execute_ratio_instructions(self, instructions):
        # executes the instructions in a .ratio file
        # used to initialize a new subgraph
        prefixes = dict()
        names = dict()

        def parse_uri(s):
            try:
                prefix_label_, suffix, uri = \
                    fullmatch(r'(?:(?:([a-zA-Z0-9_)]+):([^,\s]+))|<([^>]+)>)', s)\
                    .group(1, 2, 3)
            except AttributeError:
                raise ValueError('URI "{}" could not be parsed.'.format(s))
            if uri is None:
                uri = prefixes[prefix_label_] + suffix
            return URIRef(uri)

        for line in instructions.splitlines():
            if not line or line.isspace() or line[0] == '#':
                continue

            elif line[0] == '@':
                # prefix definition
                try:
                    prefix_label, prefix = \
                        fullmatch(r'\s*@prefix\s*([a-zA-Z0-9_)]+):\s*<([^>]+)>\s*.\s*', line)\
                        .group(1, 2)
                except AttributeError:
                    raise ValueError('Line "{}" could not be parsed.'.format(line))
                prefixes[prefix_label] = prefix

            else:
                # a command
                try:
                    name, command, arguments = \
                        fullmatch(r'\s*([a-zA-Z0-9_)]+)\s*=\s*([a-zA-Z0-9_)]+)\((.*)\)\s*', line)\
                        .group(1, 2, 3)
                except AttributeError:
                    raise ValueError('Line "{}" could not be parsed.'.format(line))

                if command == 'root':
                    # a command to creat the root entity
                    try:
                        class_uri, label = \
                            fullmatch(r'\s*([^,\s]+)\s*,\s*"([^"]+)"\s*', arguments)\
                            .group(1, 2)
                    except AttributeError:
                        raise ValueError('Arguments "{}" could not be parsed.'.format(arguments))
                    class_uri = parse_uri(class_uri)
                    label = label.strip()
                    entity = self.new_individual(class_uri, label)
                    names[name] = entity.uri
                    self.graph.add((entity.uri, RATIO.isRoot, TRUE))
                    db = get_db()
                    db.execute(
                        'INSERT INTO knowledge (subgraph_id, subject, predicate, object) VALUES (?, ?, ?, ?)',
                        (self.id, entity.uri.n3(), RATIO.isRoot.n3(), TRUE.n3())
                    )
                    db.commit()

                elif command == 'add_individual':
                    # a command to create an individual and add it as a value
                    try:
                        class_uri, label, parent, property_uri = \
                            fullmatch(r'\s*([^,\s]+)\s*,\s*"([^"]+)"\s*,\s*([a-zA-Z0-9_)]+)\s*,\s*([^,\s]+)\s*',
                                      arguments)\
                            .group(1, 2, 3, 4)
                    except AttributeError:
                        raise ValueError('Arguments "{}" could not be parsed.'.format(arguments))
                    class_uri = parse_uri(class_uri)
                    label = label.strip()
                    property_uri = parse_uri(property_uri)
                    parent_uri = names[parent]
                    index = self.new_value(parent_uri, property_uri)
                    entity = self.new_individual(class_uri, label)
                    names[name] = entity.uri
                    self.change_value(parent_uri, property_uri, index, entity.uri)

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
            graph.remove((None, None, Literal('')))
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

    # Provide information about the things described by the knowledge graph
    def get_label(self, uri):
        return get_label(self.graph, uri)

    def get_property_values(self, individual_uri, property_uri):
        if type(individual_uri) == str:
            individual_uri = URIRef(individual_uri)
        if type(property_uri) == str:
            property_uri = URIRef(property_uri)

        values = self.properties[(individual_uri, property_uri)]
        # filter values from deleted triples:
        return {i: values[i] for i in values if values[i] in self.graph[individual_uri:property_uri:]}

    def get_tokens(self, class_uri):
        if type(class_uri) == str:
            class_uri = URIRef(class_uri)

        return get_tokens(self.graph, class_uri)

    def get_individual_class(self, uri):
        if type(uri) == str:
            uri = URIRef(uri)

        return next((type_ for type_ in self.graph[uri:RDF.type:] if type_ != OWL.NamedIndividual), None)

    def get_individual_children(self, uri):
        if type(uri) == str:
            uri = URIRef(uri)

        return [value
                for property_uri in get_ontology().get_class_properties(self.get_individual_class(uri))
                for value in self.get_property_values(uri, property_uri)]

    def is_individual_deletable(self, uri):
        if type(uri) == str:
            uri = URIRef(uri)

        ontology = get_ontology()

        if uri in self.graph[:RATIO.isRoot:TRUE]:
            return False
        parent_properties = self.graph.predicates(object=uri)
        return all(ontology.is_property_deletable(p) for p in parent_properties)


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
    """Represents a possible owl:ObjectProperty or owl:DatatypeProperty of an Entity
    This is used to provide the information about a field for rendering to Jinja.
    Don't use it to check things like field.label - ontology.get_label(property_uri) is more efficient.
    """
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
        knowledge = get_subgraph_knowledge(subgraph_id)
        ontology = get_ontology()

        # todo put those things that are common to new and from knowledge in init
        label = ontology.get_label(property_uri)
        comment = ontology.get_comment(property_uri)
        order = ontology.get_property_order(property_uri)
        type_ = ontology.get_property_type(property_uri)

        if type_ == 'Subheading':
            return cls.subheading(property_uri, label, comment, order)

        range_class_uri = ontology.get_property_range(property_uri)
        range_label = ontology.get_label(range_class_uri)

        is_functional = ontology.is_property_functional(property_uri)
        is_described = ontology.is_property_described(property_uri)
        is_deletable = ontology.is_property_deletable(property_uri)

        width = ontology.get_property_width(property_uri)

        values = knowledge.get_property_values(individual_uri, property_uri)

        if is_described:
            values = {i: Entity.from_knowledge(subgraph_id, values[i])
                      for i in values if str(values[i]) != ''}
        elif type_ == 'ObjectProperty':
            values = {i: Option.from_knowledge(subgraph_id, values[i])
                      for i in values if str(values[i]) != ''}

        # TODO custom options should be stored globally, than I can put all this into the Ontology class
        one_of = next(ontology.graph[range_class_uri:OWL.oneOf:], None)
        if type_ == 'ObjectProperty' and not is_described:
            options = [Option.from_knowledge(subgraph_id, uri) for uri in ontology.get_tokens(range_class_uri)]
            # options added by the user:
            options += [Option.from_knowledge(subgraph_id, uri) for uri in knowledge.get_tokens(range_class_uri)]
            options.sort(key=lambda option: option.label)
        elif one_of is not None:
            options = construct_list(ontology.graph, one_of)
        elif range_class_uri == XSD.boolean:
            options = [TRUE, FALSE]
        else:
            options = None

        is_add_option_allowed = ontology.is_property_add_custom_option_allowed(property_uri)

        return cls(property_uri, label, comment, type_, is_described, is_deletable, is_functional,
                   range_class_uri, range_label, order, width, values, is_add_option_allowed, options)

    @classmethod
    def new(cls, subgraph_id, property_uri):
        knowledge = get_subgraph_knowledge(subgraph_id)
        ontology = get_ontology()

        label = ontology.get_label(property_uri)
        comment = ontology.get_comment(property_uri)
        order = ontology.get_property_order(property_uri)
        type_ = ontology.get_property_type(property_uri)

        if type_ == 'Subheading':
            return cls.subheading(property_uri, label, comment, order)

        range_class_uri = ontology.get_property_range(property_uri)
        range_label = ontology.get_label(range_class_uri)

        is_functional = ontology.is_property_functional(property_uri)
        is_described = ontology.is_property_described(property_uri)
        is_deletable = ontology.is_property_deletable(property_uri)

        width = ontology.get_property_width(property_uri)

        values = dict()

        # TODO custom options should be stored globally, than I can put all this into the Ontology class
        one_of = next(ontology.graph[range_class_uri:OWL.oneOf:], None)
        if type_ == 'ObjectProperty' and not is_described:
            options = [Option.from_knowledge(subgraph_id, uri) for uri in ontology.get_tokens(range_class_uri)]
            # options added by the user:
            options += [Option.from_knowledge(subgraph_id, uri) for uri in knowledge.get_tokens(range_class_uri)]
            options.sort(key=lambda option: option.label)
        elif one_of is not None:
            options = construct_list(ontology.graph, one_of)
        elif range_class_uri == XSD.boolean:
            options = [TRUE, FALSE]
        else:
            options = None

        is_add_option_allowed = ontology.is_property_add_custom_option_allowed(property_uri)

        return cls(property_uri, label, comment, type_, is_described, is_deletable, is_functional,
                   range_class_uri, range_label, order, width, values, is_add_option_allowed, options)

    @classmethod
    def subheading(cls, property_uri, label, comment, order):
        return cls(property_uri, label, comment, 'Subheading', False, False, True,
                   None, None, order, None, dict(), False, [])


class Option:
    """Represents a possible owl:ObjectProperty or owl:DatatypeProperty of an Entity
    This is used to provide the information about an option for rendering to Jinja.
    Don't use it to check things like option.label - ontology.get_label(uri) is more efficient.
    """
    def __init__(self, uri, label, class_uri, is_custom, comment=None):
        self.uri = uri
        self.label = label
        self.class_uri = class_uri
        self.is_custom = is_custom
        self.comment = comment

    # Factory  todo: after I made custom options global, decide whether its better to simply put this in init
    @classmethod
    def from_knowledge(cls, subgraph_id, uri):
        """Searches for an individual with the given URI and a type defined in the ontology."""

        knowledge = get_subgraph_knowledge(subgraph_id).graph
        ontology = get_ontology()

        # TODO custom options should be stored globally, than I can put all this into the Ontology class
        if uri in ontology.graph.subjects():
            graph = ontology.graph
        elif uri in knowledge.subjects():
            graph = knowledge
        else:
            raise ValueError('{} was not found in the ontology or the knowledge.'.format(uri))

        label = ontology.get_label(uri)
        comment = ontology.get_comment(uri)

        class_uri = None
        for type_ in graph[uri:RDF.type:]:
            if type_ in ontology.graph[:RDF.type:OWL.Class]:  # A class defined in the graph
                class_uri = type_
                break
        if class_uri is None:
            raise KeyError('No type found for option ' + str(uri))

        is_custom = TRUE in knowledge[uri:RATIO.isCustom:]

        return cls(uri, label, class_uri, is_custom, comment)


class Entity:
    """Represents a owl:NamedIndividual
    This is used to provide the information about an individual for rendering to Jinja.
    Don't use it to check things like entity.label - knowledge.get_label(uri) is more efficient.
    """
    def __init__(self, uri, label, comment, class_uri, class_label, fields):
        self.uri = uri
        self.label = label
        self.comment = comment
        self.class_uri = class_uri
        self.class_label = class_label
        self.fields = fields  # fields s.t. field.property_uri rdfs:domain self.uri

    # Factories
    @classmethod
    def from_knowledge(cls, subgraph_id, uri):
        knowledge = get_subgraph_knowledge(subgraph_id)
        ontology = get_ontology()

        class_uri = knowledge.get_individual_class(uri)
        if class_uri is None:
            raise ValueError('No type found for individual ' + str(uri))

        label = knowledge.get_label(uri)

        # todo put those things that are common to new and from knowledge in init
        class_label = ontology.get_label(class_uri)
        comment = ontology.get_comment(class_uri)

        fields = [
            Field.from_knowledge(subgraph_id, uri, property_uri)
            for property_uri in ontology.get_class_properties(class_uri)
        ]
        fields.sort(key=lambda field: field.order)

        return cls(uri, label, comment, class_uri, class_label, fields)

    @classmethod
    def new(cls, subgraph_id, class_uri, uri, label):
        ontology = get_ontology()

        class_label = ontology.get_label(class_uri)
        comment = ontology.get_comment(class_uri)

        fields = [
            Field.new(subgraph_id, property_uri)
            for property_uri in ontology.get_class_properties(class_uri)
        ]
        fields.sort(key=lambda field: field.order)

        return cls(uri, label, comment, class_uri, class_label, fields)

