-- add dummy data to fill the db for viewing in development mode and for testing

INSERT INTO user (username, password)
VALUES
  ('test', 'pbkdf2:sha256:50000$TCI4GzcX$0de171a4f4dac32e3364c7ddc7c14f3e2fa61f2d17574483f7ffbb431b4acb2f'),
  ('other', 'pbkdf2:sha256:50000$kJPKsz6N$d2d4784f1b030a9761f5ccaeeaca413f27f2ecb76d6168407af962ddce849f79');

INSERT INTO subgraph (name, root, finished, deleted)
VALUES
  ('Clinical trial 1', 'http://www.semanticweb.org/root/ontologies/2018/6/ctro#Pub_1', 0, 0),
  ('Clinical trial 2', 'http://www.semanticweb.org/root/ontologies/2018/6/ctro#Pub_2', 1, 0),
  ('Clinical trial 3', 'http://www.semanticweb.org/root/ontologies/2018/6/ctro#Pub_3', 0, 0),
  ('deleted', 'http://www.semanticweb.org/root/ontologies/2018/6/ctro#Pub_4', 1, 1);

INSERT INTO access (user_id, subgraph_id)
VALUES
  (1, 1),
  (1, 2),
  (1, 4),
  (2, 2),
  (2, 3);
