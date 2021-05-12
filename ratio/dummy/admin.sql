-- add dummy data to fill the db for viewing in development mode and for testing

INSERT INTO user (username, password, uri)
VALUES
  ('osanchez', 'pbkdf2:sha256:50000$TCI4GzcX$0de171a4f4dac32e3364c7ddc7c14f3e2fa61f2d17574483f7ffbb431b4acb2f', '<http://www.example.org/ratio-tool#User_1>'),
  ('akramersunderbrink', 'pbkdf2:sha256:50000$TCI4GzcX$0de171a4f4dac32e3364c7ddc7c14f3e2fa61f2d17574483f7ffbb431b4acb2f', '<http://www.example.org/ratio-tool#User_2'),
  ('pcimiano', 'pbkdf2:sha256:50000$TCI4GzcX$0de171a4f4dac32e3364c7ddc7c14f3e2fa61f2d17574483f7ffbb431b4acb2f', '<http://www.example.org/ratio-tool#User_3>');

INSERT INTO subgraph (name, finished, deleted)
VALUES
  ('Test', 0, 0),
  ('Test2', 0, 0);

INSERT INTO access (user_id, subgraph_id)
VALUES
  (1, 1),
  (1, 2);
