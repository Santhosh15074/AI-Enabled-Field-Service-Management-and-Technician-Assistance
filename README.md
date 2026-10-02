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
  data/raw/         downloaded datasets (not committed)
  models/           trained .pkl files (not committed)
  notebooks/        training and evaluation
scripts/            dataset download and account creation
tests/              pytest suite
docs/               diagrams, evaluation results, report
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

6. **Download the datasets.**

   ```
   python scripts/download_datasets.py
   ```

7. **Install the frontend packages** (Node.js 20 or later).

   ```
   cd frontend
   npm install
   ```

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
```

Tests build a temporary SQLite database with the same Alembic migrations, so they don't need PostgreSQL.

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
| 2 | Service requests: equipment, complaints, assignment, status history | |
| 3 | Complaint classifier | |
| 4 | Troubleshooting assistant | |
| 5 | Report generation | |
| 6 | Failure prediction | |
| 7 | Dashboard and notifications | |
| 8 | Testing, evaluation and documentation | |
