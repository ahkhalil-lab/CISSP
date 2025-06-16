from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "cissp-secret-key"

DATABASE = os.path.join(os.path.dirname(__file__), 'cissp.db')


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


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


@app.route('/exam', methods=['GET', 'POST'])
def exam():
    if request.method == 'POST':
        num_q = int(request.form.get('num_questions', 10))
        conn = get_db_connection()
        cur = conn.execute('SELECT * FROM questions ORDER BY RANDOM() LIMIT ?', (num_q,))
        questions = cur.fetchall()
        conn.close()
        session['questions'] = [dict(q) for q in questions]
        session['current'] = 0
        session['score'] = 0
        return redirect(url_for('take_exam'))
    return render_template('exam.html')


@app.route('/take_exam', methods=['GET', 'POST'])
def take_exam():
    questions = session.get('questions')
    current = session.get('current', 0)
    score = session.get('score', 0)

    if questions is None:
        return redirect(url_for('exam'))

    if request.method == 'POST':
        selected = request.form.get('answer')
        if selected == questions[current]['correct_option']:
            score += 1
        session['score'] = score
        current += 1
        session['current'] = current
        if current >= len(questions):
            conn = get_db_connection()
            conn.execute('INSERT INTO results (date, score, total) VALUES (?, ?, ?)',
                         (datetime.utcnow(), score, len(questions)))
            conn.commit()
            conn.close()
            return redirect(url_for('exam_result'))

    question = questions[current]
    return render_template('take_exam.html', question=question, current=current+1, total=len(questions))


@app.route('/exam_result')
def exam_result():
    score = session.get('score', 0)
    total = len(session.get('questions', []))
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
    app.run(debug=True)
