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
frontend/           React app for shops: owners, technicians, customers
  src/pages/        one file per screen
  src/components/   layout and shared pieces; ui/ holds shadcn/ui components
config-portal/      React app for Sollu operators: set up and configure shops (served at /config)
alembic/            database migrations
ml/
  train_*.py        train the urgency and failure-risk models
  evaluate.py       evaluates all four AI components, writes docs/evaluation/
  eval_data/        hand-labelled test sets for troubleshooting and report extraction
  data/raw/         downloaded datasets (not committed)
  models/           trained .joblib files (not committed)
scripts/            dataset download and the first operator login
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

5. **Create your operator login, then configure everything in the config portal.** Every account
   belongs to one shop and sees only that shop's technicians, customers and requests. Shops,
   their owners, plans and limits are set up by a Sollu operator in the config portal
   (`config-portal/`, served at `/config`), the only place configuration happens. The operator
   login is the one thing created from the command line:

   ```
   python scripts/create_operator.py --name "Your Name" --email you@example.com
   ```

   Customers sign up through their shop's own link (`/portal/register?shop=<slug>`). Data from
   before shops existed is in the shop with the slug `default`. Owners can still add their own
   technicians from the Users page, up to their plan's limit.

6. **Download the datasets, then train the urgency and failure-risk models.** Neither trained
   file is committed (see `ml/models/.gitkeep`), so a fresh clone needs this once; without them,
   every service request defaults to medium urgency and every reading to moderate risk.

   ```
   python scripts/download_datasets.py
   python ml/train_urgency_classifier.py
   python ml/train_failure_model.py
   ```

7. **Install the packages for both React apps** (Node.js 20 or later).

   ```
   cd frontend && npm install
   cd ..\config-portal && npm install
   ```

The troubleshooting assistant's model (`sentence-transformers/all-MiniLM-L6-v2`) downloads itself
from Hugging Face the first time it's used, then caches locally — so the first "Check for a quick
fix" or technician "Suggested fix" click after a fresh install takes a bit longer and needs
internet access; every one after that is instant and offline.

**Voice notes.** Technicians record the job on the report screen, in Tamil, English or both, and
the server turns it into text in the background. Recordings wait on the phone and upload
themselves when there's signal. Speech-to-text runs locally with faster-whisper (the `small` model,
about 460 MB, downloads on first use) until a hosted engine replaces it. On a laptop CPU it takes
roughly 3 minutes per minute of speech. The settings are in `.env.example`; recordings are kept in
`media/` (back it up with the database).

Browsers only allow the microphone on `https://` pages or `localhost`. To record from a real
phone, serve the app over HTTPS (a tunnel such as `cloudflared tunnel --url http://localhost:8000`
works for testing); over plain `http://192.168.x.x` the Record button is replaced by a message.

## Running

**While developing**, run the backend and the app you're working on in separate terminals. The shop
app is at http://localhost:5180 and the config portal at http://localhost:5181/config.

```
uvicorn app.main:app --reload          # terminal 1, in the project folder
cd frontend && npm run dev             # terminal 2: the shop app
cd config-portal && npm run dev        # terminal 3: the config portal
```

Both reload instantly as you edit, and forward every `/api` request to the backend on port 8000.

**For a demo**, build both once and let FastAPI serve everything from http://localhost:8000. The
config portal is at http://localhost:8000/config.

```
cd frontend && npm run build
cd ..\config-portal && npm run build
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
