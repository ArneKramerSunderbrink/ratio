INSERT INTO user (username, password)
VALUES
  ('test', 'pbkdf2:sha256:50000$TCI4GzcX$0de171a4f4dac32e3364c7ddc7c14f3e2fa61f2d17574483f7ffbb431b4acb2f'),
  ('other', 'pbkdf2:sha256:50000$kJPKsz6N$d2d4784f1b030a9761f5ccaeeaca413f27f2ecb76d6168407af962ddce849f79');

INSERT INTO subgraph (name)
VALUES
  ('subgraph1');

INSERT INTO access (user_id, subgraph_id)
VALUES
  (1, 1);

INSERT INTO knowledge (subgraph_id, author_id, created, subject, predicate, object)
VALUES
  (1, 1, '2020-01-01 00:00:00', 'Fritz', 'loves', 'Franz');