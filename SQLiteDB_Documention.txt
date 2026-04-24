CREATE TABLE scores (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  cps REAL NOT NULL,
  clarg_used TEXT,
  FOREIGN KEY (user_id) REFERENCES users (id)
)
CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  hash TEXT NOT NULL,
  profile_picture BLOB,
  clargs_owned JSON,
  clicktotal INTEGER
)
