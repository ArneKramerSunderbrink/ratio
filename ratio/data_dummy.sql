-- add dummy data to fill the db for viewing in development mode and for testing

INSERT INTO user (username, password)
VALUES
  ('test', 'pbkdf2:sha256:50000$TCI4GzcX$0de171a4f4dac32e3364c7ddc7c14f3e2fa61f2d17574483f7ffbb431b4acb2f'),
  ('other', 'pbkdf2:sha256:50000$kJPKsz6N$d2d4784f1b030a9761f5ccaeeaca413f27f2ecb76d6168407af962ddce849f79');

INSERT INTO subgraph (name, root, finished, deleted)
VALUES
  ('subgraph1', 'http://www.semanticweb.org/root/ontologies/2018/6/ctro#CT_1', 0, 0),
  ('subgraph2', 'http://www.semanticweb.org/root/ontologies/2018/6/ctro#CT_2', 1, 0),
  ('subgraph3', 'http://www.semanticweb.org/root/ontologies/2018/6/ctro#CT_3', 0, 0),
  ('deleted', 'http://www.semanticweb.org/root/ontologies/2018/6/ctro#CT_4', 1, 1);

INSERT INTO access (user_id, subgraph_id)
VALUES
  (1, 1),
  (1, 2),
  (1, 4),
  (2, 2),
  (2, 3);

-- todo better do this in turtle like the ontology
INSERT INTO knowledge (subgraph_id, subject, predicate, object, object_is_uri)
VALUES
  (1, 'http://www.semanticweb.org/root/ontologies/2018/6/ctro#CT_1', 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type', 'http://www.w3.org/2002/07/owl#NamedIndividual', 1),
  (1, 'http://www.semanticweb.org/root/ontologies/2018/6/ctro#CT_1', 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type', 'http://www.semanticweb.org/root/ontologies/2018/6/ctro#ClinicalTrial', 1),
  (1, 'http://www.semanticweb.org/root/ontologies/2018/6/ctro#CT_1', 'http://www.w3.org/2000/01/rdf-schema#label', 'Clinical Trial 1', 0),
  (2, 'http://www.semanticweb.org/root/ontologies/2018/6/ctro#CT_2', 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type', 'http://www.w3.org/2002/07/owl#NamedIndividual', 1),
  (2, 'http://www.semanticweb.org/root/ontologies/2018/6/ctro#CT_2', 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type', 'http://www.semanticweb.org/root/ontologies/2018/6/ctro#ClinicalTrial', 1),
  (1, 'http://www.semanticweb.org/root/ontologies/2018/6/ctro#CT_2', 'http://www.w3.org/2000/01/rdf-schema#label', 'Clinical Trial 2', 0),
  (3, 'http://www.semanticweb.org/root/ontologies/2018/6/ctro#CT_3', 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type', 'http://www.w3.org/2002/07/owl#NamedIndividual', 1),
  (3, 'http://www.semanticweb.org/root/ontologies/2018/6/ctro#CT_3', 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type', 'http://www.semanticweb.org/root/ontologies/2018/6/ctro#ClinicalTrial', 1),
  (1, 'http://www.semanticweb.org/root/ontologies/2018/6/ctro#CT_3', 'http://www.w3.org/2000/01/rdf-schema#label', 'Clinical Trial 3', 0),
  (4, 'http://www.semanticweb.org/root/ontologies/2018/6/ctro#CT_4', 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type', 'http://www.w3.org/2002/07/owl#NamedIndividual', 1),
  (4, 'http://www.semanticweb.org/root/ontologies/2018/6/ctro#CT_4', 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type', 'http://www.semanticweb.org/root/ontologies/2018/6/ctro#ClinicalTrial', 1),
  (1, 'http://www.semanticweb.org/root/ontologies/2018/6/ctro#CT_4', 'http://www.w3.org/2000/01/rdf-schema#label', 'Clinical Trial 4', 0);
