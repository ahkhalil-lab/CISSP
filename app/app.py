from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import datetime
import os
import json
import zlib
import base64
from dotenv import load_dotenv
import openai

load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')
openai_model = os.getenv('OPENAI_MODEL', 'gpt-4o')

app = Flask(__name__)
app.secret_key = "cissp-secret-key"

DATABASE = os.path.join(os.path.dirname(__file__), 'cissp.db')


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def store_question_ids(question_ids):
    """Compress and store the question ID list in the session."""
    raw = json.dumps(question_ids).encode()
    blob = base64.b64encode(zlib.compress(raw)).decode()
    session['question_blob'] = blob


def load_question_ids():
    """Load and decompress the question ID list from the session."""
    blob = session.get('question_blob')
    if not blob:
        return None
    try:
        raw = zlib.decompress(base64.b64decode(blob))
        return json.loads(raw.decode())
    except Exception:
        return None


def normalize_option(value):
    """Convert stored answer options to a single letter."""
    if value is None:
        return None
    val = str(value).strip()
    lower = val.lower()
    if len(val) == 1 and val.upper() in "ABCD":
        return val.upper()
    if lower.startswith("option_") and lower[-1] in "abcd":
        return lower[-1].upper()
    return val.upper()

def generate_ai_questions(prompt, count):
    """Call ChatGPT to generate a list of question dictionaries."""
    if not openai.api_key:
        raise RuntimeError('OpenAI API key not configured')
    messages = [
        {
            'role': 'system',
            'content': (
                'You are a CISSP exam question generator. '
                'Respond in JSON array format with objects containing '
                'domain, question, option_a, option_b, option_c, option_d, '
                'correct_option, and explanation.'
            ),
        },
        {
            'role': 'user',
            'content': f'Create {count} questions about: {prompt}'
        },
    ]
    resp = openai.chat.completions.create(model=openai_model, messages=messages)
    text = resp.choices[0].message.content
    return json.loads(text)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/flashcards')
def flashcards():
    conn = get_db_connection()
    cur = conn.execute('SELECT * FROM questions ORDER BY RANDOM() LIMIT 1')
    question = cur.fetchone()
    conn.close()
    return render_template('flashcards.html', question=question)


@app.route('/ai_exam', methods=['GET', 'POST'])
def ai_exam():
    if request.method == 'POST':
        prompt = request.form['prompt']
        num_q = int(request.form.get('num_questions', 5))
        try:
            questions = generate_ai_questions(prompt, num_q)
        except Exception as e:
            flash(f'Failed to generate questions: {e}')
            return redirect(url_for('ai_exam'))
        session['ai_questions'] = questions
        session['current'] = 0
        session['score'] = 0
        return redirect(url_for('take_ai_exam'))
    return render_template('ai_exam.html')


@app.route('/exam', methods=['GET', 'POST'])
def exam():
    conn = get_db_connection()
    cur = conn.execute('SELECT DISTINCT domain FROM questions ORDER BY domain')
    domains = [row['domain'] for row in cur.fetchall()]
    if request.method == 'POST':
        num_q = int(request.form.get('num_questions', 10))
        selected_domains = request.form.getlist('domains') or domains
        placeholders = ','.join('?' for _ in selected_domains)

        count_query = f'SELECT COUNT(*) FROM questions WHERE domain IN ({placeholders})'
        available = conn.execute(count_query, selected_domains).fetchone()[0]

        if available == 0:
            conn.close()
            flash('No questions found for the selected domains.')
            return redirect(url_for('exam'))

        if num_q > available:
            flash(f'Only {available} questions available; starting exam with {available}.')
            num_q = available

        query = f'SELECT id FROM questions WHERE domain IN ({placeholders}) ORDER BY RANDOM() LIMIT ?'
        cur = conn.execute(query, (*selected_domains, num_q))
        question_ids = [row['id'] for row in cur.fetchall()]
        conn.close()
        session.pop('question_blob', None)
        store_question_ids(question_ids)
        session['current'] = 0
        session['score'] = 0
        return redirect(url_for('take_exam'))
    conn.close()
    return render_template('exam.html', domains=domains)


@app.route('/take_exam')
def take_exam():
    question_ids = load_question_ids()
    current = session.get('current', 0)

    if not question_ids or current >= len(question_ids):
        flash('No active exam. Please start again.')
        return redirect(url_for('exam'))

    conn = get_db_connection()
    qid = question_ids[current]
    question = conn.execute('SELECT * FROM questions WHERE id=?', (qid,)).fetchone()
    conn.close()
    return render_template('take_exam.html', question=question,
                           current=current + 1, total=len(question_ids),
                           action_url=url_for('answer_question'))


@app.route('/answer_question', methods=['POST'])
def answer_question():
    question_ids = load_question_ids()
    current = session.get('current', 0)
    score = session.get('score', 0)

    if not question_ids or current >= len(question_ids):
        return redirect(url_for('exam'))

    selected = normalize_option(request.form.get('answer'))
    conn = get_db_connection()
    qid = question_ids[current]
    question = conn.execute('SELECT * FROM questions WHERE id=?', (qid,)).fetchone()
    correct_option = normalize_option(question.get('correct_option'))
    correct = False
    if selected is not None and correct_option is not None:
        correct = selected == correct_option
        if correct:
            score += 1
    session['score'] = score
    session['current'] = current + 1
    session['last_question_id'] = qid
    session['last_selected'] = selected

    done = session['current'] >= len(question_ids)
    if done:
        conn.execute('INSERT INTO results (date, score, total) VALUES (?, ?, ?)',
                     (datetime.utcnow(), score, len(question_ids)))
        conn.commit()
    conn.close()

    return redirect(url_for('review_question'))


@app.route('/review_question')
def review_question():
    qid = session.get('last_question_id')
    selected = session.get('last_selected')
    question_ids = load_question_ids()
    current = session.get('current', 0)

    if qid is None or question_ids is None:
        return redirect(url_for('exam'))

    conn = get_db_connection()
    question = conn.execute('SELECT * FROM questions WHERE id=?', (qid,)).fetchone()
    conn.close()
    correct_option = normalize_option(question.get('correct_option'))
    correct = False
    if selected is not None and correct_option is not None:
        correct = selected == correct_option
    done = current >= len(question_ids)
    next_url = url_for('exam_result') if done else url_for('take_exam')
    return render_template('review_question.html', question=question,
                           selected=selected, correct=correct,
                           correct_letter=correct_option,
                           next_url=next_url, current=current,
                           total=len(question_ids))


@app.route('/exam_result')
def exam_result():
    score = session.get('score', 0)
    question_ids = load_question_ids() or []
    session.pop('question_blob', None)
    total = len(question_ids)
    return render_template('exam_result.html', score=score, total=total)


@app.route('/take_ai_exam')
def take_ai_exam():
    questions = session.get('ai_questions')
    current = session.get('current', 0)
    if not questions or current >= len(questions):
        flash('No active AI exam. Please start again.')
        return redirect(url_for('ai_exam'))
    question = questions[current]
    return render_template('take_exam.html', question=question,
                           current=current + 1, total=len(questions),
                           action_url=url_for('answer_ai_question'))


@app.route('/answer_ai_question', methods=['POST'])
def answer_ai_question():
    questions = session.get('ai_questions')
    current = session.get('current', 0)
    score = session.get('score', 0)
    if not questions or current >= len(questions):
        return redirect(url_for('ai_exam'))
    selected = normalize_option(request.form.get('answer'))
    question = questions[current]
    correct_option = normalize_option(question.get('correct_option'))
    correct = False
    if selected is not None and correct_option is not None:
        correct = selected == correct_option
        if correct:
            score += 1
    session['score'] = score
    session['current'] = current + 1
    session['last_question'] = question
    session['last_selected'] = selected

    done = session['current'] >= len(questions)
    if done:
        conn = get_db_connection()
        conn.execute('INSERT INTO results (date, score, total) VALUES (?, ?, ?)',
                     (datetime.utcnow(), score, len(questions)))
        conn.commit()
        conn.close()

    return redirect(url_for('review_ai_question'))


@app.route('/review_ai_question')
def review_ai_question():
    question = session.get('last_question')
    selected = session.get('last_selected')
    questions = session.get('ai_questions')
    current = session.get('current', 0)

    if question is None or questions is None:
        return redirect(url_for('ai_exam'))

    correct_option = normalize_option(question.get('correct_option'))
    selected = normalize_option(selected)
    correct = False
    if selected is not None and correct_option is not None:
        correct = selected == correct_option
    done = current >= len(questions)
    next_url = url_for('ai_exam_result') if done else url_for('take_ai_exam')
    return render_template('review_question.html', question=question,
                           selected=selected, correct=correct,
                           correct_letter=correct_option,
                           next_url=next_url, current=current,
                           total=len(questions))


@app.route('/ai_exam_result')
def ai_exam_result():
    score = session.get('score', 0)
    questions = session.get('ai_questions') or []
    session.pop('ai_questions', None)
    total = len(questions)
    return render_template('exam_result.html', score=score, total=total)


@app.route('/progress')
def progress():
    conn = get_db_connection()
    cur = conn.execute('SELECT * FROM results ORDER BY date DESC')
    results = cur.fetchall()
    conn.close()
    return render_template('progress.html', results=results)


@app.route('/questions')
def question_list():
    """Display all questions for editing or deletion."""
    conn = get_db_connection()
    cur = conn.execute('SELECT id, domain, question FROM questions ORDER BY id ASC')
    questions = cur.fetchall()
    conn.close()
    return render_template('question_list.html', questions=questions)


@app.route('/question/delete/<int:question_id>', methods=['POST'])
def delete_question(question_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM questions WHERE id=?', (question_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('question_list'))


@app.route('/question/new', methods=['GET', 'POST'])
@app.route('/question/<int:question_id>', methods=['GET', 'POST'])
def question_form(question_id=None):
    conn = get_db_connection()
    if request.method == 'POST':
        data = (
            request.form['domain'],
            request.form['question'],
            request.form['option_a'],
            request.form['option_b'],
            request.form['option_c'],
            request.form['option_d'],
            request.form['correct_option'],
            request.form.get('explanation', '')
        )
        if question_id:
            conn.execute('''UPDATE questions SET domain=?, question=?, option_a=?, option_b=?,
                            option_c=?, option_d=?, correct_option=?, explanation=? WHERE id=?''',
                         data + (question_id,))
        else:
            conn.execute('''INSERT INTO questions (domain, question, option_a, option_b,
                            option_c, option_d, correct_option, explanation)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', data)
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    question = None
    if question_id:
        cur = conn.execute('SELECT * FROM questions WHERE id=?', (question_id,))
        question = cur.fetchone()
    conn.close()
    return render_template('question_form.html', question=question)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Run the CISSP study web app')
    parser.add_argument('--model', help='OpenAI model to use for AI exams')
    args = parser.parse_args()
    if args.model:
        openai_model = args.model
    app.run(debug=True)
