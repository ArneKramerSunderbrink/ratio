-- add dummy data to fill the db for viewing in development mode and for testing

INSERT INTO user (username, password, admin, uri)
VALUES
  ('guest', 'pbkdf2:sha256:150000$F2w0oD35$d7b907e93f82a3498f68581121ceb335e4309e6e279189e339c8c2d18b104a16', 0, '<http://www.example.org/ratio-tool#User_1>'),
  ('osanchez', 'pbkdf2:sha256:50000$TCI4GzcX$0de171a4f4dac32e3364c7ddc7c14f3e2fa61f2d17574483f7ffbb431b4acb2f', 1, '<http://www.example.org/ratio-tool#User_2>'),
  ('akramersunderbrink', 'pbkdf2:sha256:50000$TCI4GzcX$0de171a4f4dac32e3364c7ddc7c14f3e2fa61f2d17574483f7ffbb431b4acb2f', 1, '<http://www.example.org/ratio-tool#User_3'),
  ('pcimiano', 'pbkdf2:sha256:50000$TCI4GzcX$0de171a4f4dac32e3364c7ddc7c14f3e2fa61f2d17574483f7ffbb431b4acb2f', 1, '<http://www.example.org/ratio-tool#User_4>');

