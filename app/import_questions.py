import json
import sqlite3
import os
import sys

DB_PATH = os.path.join(os.path.dirname(__file__), 'cissp.db')

if len(sys.argv) < 2:
    print('Usage: python import_questions.py questions.json')
    sys.exit(1)

json_file = sys.argv[1]

with open(json_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

conn = sqlite3.connect(DB_PATH)
for q in data:
    conn.execute('''INSERT INTO questions
                    (domain, question, option_a, option_b, option_c, option_d, correct_option, explanation)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                 (q['domain'], q['question'], q['option_a'], q['option_b'],
                  q['option_c'], q['option_d'], q['correct_option'], q.get('explanation', '')))
conn.commit()
conn.close()
print('Imported', len(data), 'questions.')
