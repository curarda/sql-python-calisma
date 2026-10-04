# SQL & Python Practice

An interactive practice app for SQL and Python (pandas). Each topic starts with a short explanation, then exercises follow. You write the code, run it, and get your answer checked with feedback.

**Live app (browser, installable on iPhone):** https://curarda.github.io/sql-python-practice/

## Who it is for

- Candidates preparing for SQL and Python technical tests, such as data and product internship interviews.
- Beginners who want guided exercises with immediate feedback.

## Why I built it

I built it to prepare for the technical exam of a product management internship. I wanted practice that checks my answers instantly, without needing a server or an account.

## What it does

- Topic explanations followed by graded exercises.
- Code runs in your browser (Python via Pyodide, with pandas), so nothing is sent to a server.
- Progress is saved in your browser only.
- Runs past 5 seconds are stopped so the page never freezes.
- The interface and feedback are in Turkish.

## Use on iPhone

1. Open the live link in **Safari**.
2. Tap Share → **Add to Home Screen**.

The first launch downloads the Python environment (Pyodide and pandas), which can take a few minutes. After that it works offline.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

The browser version is generated from `web/` and the root Python files into `docs/`; see the developer section in [README.tr.md](README.tr.md).

## Tech

Python, pandas, SQL, Streamlit (local version), Pyodide (browser version), pytest for tests.

The original Turkish documentation is in [README.tr.md](README.tr.md).
