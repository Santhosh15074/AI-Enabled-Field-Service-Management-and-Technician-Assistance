# AI-Enabled Field Service Management and Technician Assistance

MCA IV Semester project, Anna University CDE. Santhosh Kumar R (2436MCA0024). Guide: Dr. Vidya K.

A web application for Admins, Customers and Technicians. It classifies complaints, suggests
troubleshooting steps, turns spoken reports into structured records and predicts equipment failures.

- **Backend:** Python, FastAPI JSON API, SQLAlchemy, PostgreSQL, scikit-learn
- **Frontend:** React, TypeScript, Vite, Tailwind CSS, shadcn/ui

## Project layout

```
app/                FastAPI backend (JSON API under /api)
  models.py         database tables (SQLAlchemy)
  routes/           API endpoints
frontend/           React app
  src/pages/        one file per screen
  src/components/   layout and shared pieces; ui/ holds shadcn/ui components
alembic/            database migrations
ml/
  train_*.py        train the urgency and failure-risk models
  evaluate.py       evaluates all four AI components, writes docs/evaluation/
  eval_data/        hand-labelled test sets for troubleshooting and report extraction
  data/raw/         downloaded datasets (not committed)
  models/           trained .joblib files (not committed)
scripts/            dataset download and account creation
tests/              pytest suite
docs/
  architecture.md   components, workflows, data model, API reference, security
  evaluation.md     how well each AI component works, and its limitations
  testing.md        test approach, what's covered, coverage report
  evaluation/       generated metrics and charts
```

## Setup (Windows)

1. **Create the virtual environment and install packages.**

   ```
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt -r requirements-ml.txt
   ```

2. **Create the database.** PostgreSQL 18 runs locally as the `postgresql-x64-18` service.

   ```
   "C:\Program Files\PostgreSQL\18\bin\createdb.exe" -U postgres aitechnician
   ```

3. **Configure.** Copy `.env.example` to `.env`. Put the `postgres` password into `DATABASE_URL` and
   set `SECRET_KEY` to the output of `python -c "import secrets; print(secrets.token_hex(32))"`.

4. **Create the tables.**

   ```
   alembic upgrade head
   ```

5. **Create the first admin.** Public sign-up only creates customers.

   ```
   python scripts/create_user.py --role admin --name "Your Name" --email admin@example.com
   python scripts/create_user.py --role technician --name "Ravi" --email ravi@example.com --skill-area Electrical
   ```

6. **Download the datasets, then train the urgency and failure-risk models.** Neither trained
   file is committed (see `ml/models/.gitkeep`), so a fresh clone needs this once; without them,
   every service request defaults to medium urgency and every reading to moderate risk.

   ```
   python scripts/download_datasets.py
   python ml/train_urgency_classifier.py
   python ml/train_failure_model.py
   ```

7. **Install the frontend packages** (Node.js 20 or later).

   ```
   cd frontend
   npm install
   ```

The troubleshooting assistant's model (`sentence-transformers/all-MiniLM-L6-v2`) downloads itself
from Hugging Face the first time it's used, then caches locally — so the first "Check for a quick
fix" or technician "Suggested fix" click after a fresh install takes a bit longer and needs
internet access; every one after that is instant and offline.

## Running

**While developing**, run the backend and frontend in two terminals, then open http://localhost:5180.

```
uvicorn app.main:app --reload          # terminal 1, in the project folder
cd frontend && npm run dev             # terminal 2
```

The frontend reloads instantly as you edit. It forwards every `/api` request to the backend on port 8000.

**For a demo**, build the frontend once and let FastAPI serve everything from http://localhost:8000:

```
cd frontend && npm run build
cd .. && uvicorn app.main:app
```

API documentation is at http://localhost:8000/api/docs.

## Tests

```
pytest
pytest --cov=app --cov-report=term-missing     # with line coverage
```

Tests build a temporary SQLite database with the same Alembic migrations, so they don't need PostgreSQL. What's
covered and why is in [docs/testing.md](docs/testing.md).

## Evaluation

After training both models (setup step 6):

```
python ml/evaluate.py
```

This measures the urgency classifier and failure model on their held-out test splits, and the
troubleshooting assistant and report extraction on the hand-labelled sets in `ml/eval_data/`, then
rewrites `docs/evaluation/results.md` and its charts. Discussion of the results is in
[docs/evaluation.md](docs/evaluation.md); the system design is in
[docs/architecture.md](docs/architecture.md).

## Changing the database

After editing `app/models.py`, generate and apply a migration:

```
alembic revision --autogenerate -m "describe the change"
alembic upgrade head
```

`tests/test_schema.py` fails if a model changes without a migration.

## Build phases

| Phase | Scope | Status |
|---|---|---|
| 0 | Setup: repository, environment, database, datasets | Done |
| 1 | Database schema, login, roles, sessions, dashboards | Done |
| 2 | Service requests: equipment, complaints, assignment, status history | Done |
| 3 | Complaint classifier | Done |
| 4 | Troubleshooting assistant | Done |
| 5 | Report generation | Done |
| 6 | Failure prediction | Done |
| 7 | Dashboards, analytics and notifications | Done |
| 8 | Testing, evaluation and documentation | Done |
