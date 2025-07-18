# CISSP Study Web App

This project provides a small Flask web application to help you practice for the CISSP exam. It supports flashcards, mock exams with per-question feedback, question management, and progress tracking. Questions are stored in an SQLite database so it can run locally without extra services.

## Features

- Random flashcards for quick review
- Create mock exams with scoring and explanations after each answer
- Choose which security domains to include when starting an exam
- Add, edit, or delete questions
- Track exam results over time
- Responsive layout works well on mobile devices
- Generate practice exams with ChatGPT
- Resume a saved exam if you close the browser

## Setup

1. Create a Python environment (Python 3.8+ recommended).
2. Install dependencies:
   ```bash
   pip install Flask openai python-dotenv
   ```
3. Initialize the database:
   ```bash
   python app/initialize_db.py
   ```
4. Create a `.env` file and set your OpenAI API key (and optional model name):
   ```bash
   cp .env.example .env
   # edit .env to add your key and optionally change OPENAI_MODEL
   ```
5. (Optional) Import your questions from a JSON file:
   ```bash
   python app/import_questions.py questions.json
   ```
   A template file `questions.json.template` is included to show the expected format.
6. Run the application (you can specify a different model with `--model`):
   ```bash
   # default model comes from OPENAI_MODEL or gpt-4o
   python app/app.py
   # or override
   python app/app.py --model gpt-3.5-turbo
   ```
7. Open your browser to `http://localhost:5000`.

Once running, use the **Questions** link in the navigation bar to view all questions.
From there you can edit or delete entries.
During an exam you select how many questions to attempt and which domains to draw from. The application now compresses the question list so you can practice hundreds of questions in one sitting. If the selected domains contain fewer questions than requested, the exam automatically uses all available questions. After each answer you will immediately see whether you were correct along with the explanation before moving on. If you close your browser in the middle of an exam, just return to the exam page to resume or cancel the saved session.

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

The `correct_option` should normally be the letter `A`, `B`, `C`, or `D`, but values like `option_a` are also recognized.

## Notes

This project is intended for personal study use. If you share questions or other content, ensure that you have the rights to do so.

## AI Question Generation

If you provide an OpenAI API key in `.env`, the **AI Exam** page lets you enter a prompt and automatically generate a short practice exam using ChatGPT. Questions are kept in memory and scored like regular exams. The model defaults to `gpt-4o` but can be changed via the `OPENAI_MODEL` variable or the `--model` option.
