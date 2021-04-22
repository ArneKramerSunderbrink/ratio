-- add dummy data to fill the db for viewing in development mode and for testing

INSERT INTO user (username, password)
VALUES
  ('osanchez', 'pbkdf2:sha256:50000$TCI4GzcX$0de171a4f4dac32e3364c7ddc7c14f3e2fa61f2d17574483f7ffbb431b4acb2f'),
  ('akramersunderbrink', 'pbkdf2:sha256:50000$TCI4GzcX$0de171a4f4dac32e3364c7ddc7c14f3e2fa61f2d17574483f7ffbb431b4acb2f'),
  ('pcimiano', 'pbkdf2:sha256:50000$TCI4GzcX$0de171a4f4dac32e3364c7ddc7c14f3e2fa61f2d17574483f7ffbb431b4acb2f');

INSERT INTO subgraph (name, finished, deleted)
VALUES
  ('RELY-Connolly(2009)', 1, 0),
  ('nothing', 0, 1),
  ('ROCKET-AF-Patel(2011)', 1, 0),
  ('ARISTOTLE-Granger(2011)', 1, 0),
  ('ENGAGE-Giugliano(2013)', 1, 0),
  ('ERISTA-AF-Rutherford(2020)', 0, 0),
  ('ENSURE-AF-Goette(2016)', 1, 0),
  ('Asprin vs. Dolormin', 0, 0),
  -- for Philipp
  ('RELY-Connolly(2009)', 1, 0),
  ('ROCKET-AF-Patel(2011)', 1, 0),
  ('ARISTOTLE-Granger(2011)', 1, 0),
  ('ENGAGE-Giugliano(2013)', 1, 0),
  ('ERISTA-AF-Rutherford(2020)', 0, 0),
  ('ENSURE-AF-Goette(2016)', 1, 0),
  ('Asprin vs. Dolormin', 0, 0);

INSERT INTO access (user_id, subgraph_id)
VALUES
  (1, 1),
  (1, 3),
  (1, 4),
  (1, 5),
  (1, 6),
  (1, 7),
  (1, 8),
  -- for Philipp
  (3, 9),
  (3, 10),
  (3, 11),
  (3, 12),
  (3, 13),
  (3, 14),
  (3, 15);
