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
  admin BIT NOT NULL,
  uri TEXT NOT NULL,
  deleted BIT NOT NULL DEFAULT 0
);

INSERT INTO user (username, password, admin, uri) VALUES (
  'admin',
  'pbkdf2:sha256:150000$f1G40PP3$d2452fd97994b486a1238f20941aa313439a7cadd3de7e494304f9fab27241cc',
  1,
  '<http://www.example.org/ratio-tool#User_1>'
);

CREATE TABLE subgraph (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  finished BIT NOT NULL DEFAULT 0,
  deleted BIT NOT NULL DEFAULT 0
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