-- Initialize the database.
-- Drop any existing data and create empty tables.

DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS subgraph;
DROP TABLE IF EXISTS access;
DROP TABLE IF EXISTS knowledge;
DROP TABLE IF EXISTS ontology;
DROP TABLE IF EXISTS namespace;

CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL,
  uri TEXT NOT NULL
);

CREATE TABLE subgraph (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  finished BIT NOT NULL,
  deleted BIT NOT NULL
);

CREATE TABLE access (
  user_id INTEGER NOT NULL,
  subgraph_id INTEGER NOT NULL,
  FOREIGN KEY (user_id) REFERENCES user (id),
  FOREIGN KEY (subgraph_id) REFERENCES subgraph (id)
);

-- RDF triples that represent knowledge about a certain subgraph
CREATE TABLE knowledge (
  subgraph_id INTEGER NOT NULL,
  subject TEXT NOT NULL,
  predicate TEXT NOT NULL,
  object TEXT NOT NULL,
  property_index INTEGER,
  deleted TEXT,             -- contains occasion of deletion if deleted, else NULL
  FOREIGN KEY (subgraph_id) REFERENCES subgraph (id)
);

-- RDF triples that represent the ontology
CREATE TABLE ontology (
  subject TEXT NOT NULL,
  predicate TEXT NOT NULL,
  object TEXT NOT NULL
);

CREATE TABLE namespace (
  prefix TEXT,
  uri TEXT NOT NULL
);