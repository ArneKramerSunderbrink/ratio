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
  finished BIT NOT NULL
);

CREATE TABLE access (
  user_id INTEGER NOT NULL,
  subgraph_id INTEGER NOT NULL,
  FOREIGN KEY (user_id) REFERENCES user (id),
  FOREIGN KEY (subgraph_id) REFERENCES subgraph (id)
);

-- RDF triples with additional information about
-- the subgraph of the knowledge base, e.g. specifying that it's knowledge about a specific clinical trial
-- the author who added the triple to the knowledgebase
-- and the time point of creation
CREATE TABLE knowledge (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  subgraph_id INTEGER NOT NULL,
  author_id INTEGER NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  subject TEXT NOT NULL,
  predicate TEXT NOT NULL,
  object TEXT NOT NULL,
  FOREIGN KEY (subgraph_id) REFERENCES subgraph (id)
  FOREIGN KEY (author_id) REFERENCES user (id)
);

-- Todo: remove for production, only for development, this should be done by an admin later
INSERT INTO user (username, password)
VALUES
  ('dev', 'pbkdf2:sha256:50000$TCI4GzcX$0de171a4f4dac32e3364c7ddc7c14f3e2fa61f2d17574483f7ffbb431b4acb2f');