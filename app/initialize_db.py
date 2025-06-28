import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'cissp.db')

schema = '''
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    domain TEXT NOT NULL,
    question TEXT NOT NULL,
    option_a TEXT NOT NULL,
    option_b TEXT NOT NULL,
    option_c TEXT NOT NULL,
    option_d TEXT NOT NULL,
    correct_option TEXT NOT NULL,
    explanation TEXT
);

CREATE TABLE IF NOT EXISTS results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    score INTEGER NOT NULL,
    total INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS exam_state (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    data TEXT NOT NULL
);
'''

conn = sqlite3.connect(DB_PATH)
conn.executescript(schema)
conn.commit()
conn.close()
print('Database initialized at', DB_PATH)
