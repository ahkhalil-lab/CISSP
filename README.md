# CISSP Study Web App


This project provides a small Flask web application to help you practice for the CISSP exam. It supports flashcards, mock exams with per-question feedback, question management, and progress tracking. Questions are stored in an SQLite database so it can run locally without extra services.


## Features

- Random flashcards for quick review

- Create mock exams with scoring and explanations after each answer
During an exam you select how many questions to attempt and which domains to draw from. The application now compresses the question list so you can practice hundreds of questions in one sitting. After each answer you will immediately see whether you were correct along with the explanation before moving on.
- Add, edit, or delete questions

- Track exam results over time

## Setup

1. Create a Python environment (Python 3.8+ recommended).
2. Install Flask:
   ```bash
   pip install Flask
   ```
3. Initialize the database:
   ```bash
   python app/initialize_db.py
   ```
4. (Optional) Import your questions from a JSON file:
   ```bash
   python app/import_questions.py questions.json
   ```
   A template file `questions.json.template` is included to show the expected format.
5. Run the application:
   ```bash
   python app/app.py
   ```
6. Open your browser to `http://localhost:5000`.


Once running, use the **Questions** link in the navigation bar to view all questions.
From there you can edit or delete entries.
During an exam you select how many questions to attempt and which domains to draw from. After each answer you will immediately see whether you were correct along with the explanation before moving on.

## Question JSON Format

Each question should include a domain, text, four answer options, the correct option (A/B/C/D) and an optional explanation. Example:

```json
[
  {
    "domain": "Security and Risk Management",
    "question": "What is the primary purpose of a security policy?",
    "option_a": "To define technical controls",
    "option_b": "To outline management's intent",
    "option_c": "To implement physical security",
    "option_d": "To configure firewalls",
    "correct_option": "B",
    "explanation": "A security policy is a high-level statement of management's intent and goals."
  }
]
```

## Notes

This project is intended for personal study use. If you share questions or other content, ensure that you have the rights to do so.
