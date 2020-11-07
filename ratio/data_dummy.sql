-- add dummy data to fill the db for viewing in development mode and for testing

INSERT INTO user (username, password)
VALUES
  ('test', 'pbkdf2:sha256:50000$TCI4GzcX$0de171a4f4dac32e3364c7ddc7c14f3e2fa61f2d17574483f7ffbb431b4acb2f'),
  ('other', 'pbkdf2:sha256:50000$kJPKsz6N$d2d4784f1b030a9761f5ccaeeaca413f27f2ecb76d6168407af962ddce849f79');

INSERT INTO subgraph (name, finished, deleted)
VALUES
  ('subgraph1', 0, 0),
  ('subgraph2', 1, 0),
  ('subgraph3', 0, 0),
  ('deleted', 1, 1);

INSERT INTO access (user_id, subgraph_id)
VALUES
  (1, 1),
  (1, 2),
  (1, 4),
  (2, 2),
  (2, 3);

INSERT INTO knowledge (subgraph_id, author_id, subject, predicate, object)
VALUES
  (1, 1, 'Fritz', 'loves', 'Franz');