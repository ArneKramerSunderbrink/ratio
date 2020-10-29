-- Initialize the database.
-- Drop any existing data and create empty tables.

DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS subgraph;
DROP TABLE IF EXISTS access;
DROP TABLE IF EXISTS knowledge;

CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL
);

CREATE TABLE subgraph (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT UNIQUE NOT NULL,
  finished BIT NOT NULL,
  deleted BIT NOT NULL
);

CREATE TABLE access (
  user_id INTEGER NOT NULL,
  subgraph_id INTEGER NOT NULL,
  FOREIGN KEY (user_id) REFERENCES user (id),
  FOREIGN KEY (subgraph_id) REFERENCES subgraph (id)
);

-- RDF triples with additional information about
-- the subgraph of the knowledge base, e.g. specifying that it's knowledge about a specific clinical trial,
-- and the author who added the triple to the knowledgebase
CREATE TABLE knowledge (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  subgraph_id INTEGER NOT NULL,
  author_id INTEGER NOT NULL,
  subject TEXT NOT NULL,
  predicate TEXT NOT NULL,
  object TEXT NOT NULL,
  FOREIGN KEY (subgraph_id) REFERENCES subgraph (id)
  FOREIGN KEY (author_id) REFERENCES user (id)
);