# Testing

```
pytest                                          # 195 tests, about 7 minutes
pytest --cov=app --cov-report=term-missing      # with line coverage
```

## Approach

- **Real database schema, no PostgreSQL needed.** Every test gets a fresh SQLite database built
  by running the real Alembic migrations (`tests/conftest.py`), so the schema under test is exactly
  the one deployed. `test_schema.py` fails if a model is changed without a matching migration.
- **Through the API.** Route tests call endpoints with FastAPI's `TestClient` and a real session
  cookie, logged in as an actual admin, technician or customer, so authentication and role checks
  are exercised on every call rather than bypassed.
- **AI components tested for logic, not accuracy.** Unit tests replace each model with a small
  deterministic stand-in to check ranking, thresholds and fallbacks quickly and repeatably. How
  accurate the real models are is measured separately by `ml/evaluate.py`; see
  [evaluation.md](evaluation.md).

## What is covered

| File | Tests | Covers |
|---|---|---|
| `test_auth.py` | 44 | Registration validation, phone or email login, password rules, sessions, logout, deactivation ending a live session |
| `test_requests.py` | 62 | Creating complaints, staff raising requests for customers, urgency on create, listing per role, assignment, forward-only status, ownership checks, suggestions, notifications on changes |
| `test_reports.py` | 15 | Report extraction preview, saving, one report per request, who may read or write it |
| `test_users.py` | 15 | Admin-only staff creation and validation, activation, not deactivating yourself |
| `test_knowledge_base.py` | 13 | Admin-only create, edit and delete; category and blank-field validation |
| `test_notifications.py` | 10 | Own notifications only, unread count, mark one or all read |
| `test_failure_prediction.py` | 8 | Risk thresholds, fallbacks, prediction log, latest risk on equipment |
| `test_analytics.py` | 7 | Admin-only access, zero-filled empty state, status/urgency/category counts, 30-day window, resolution times and workload, latest-prediction risk |
| `test_report_extraction.py` | 6 | Issue, action, parts and duration rules |
| `test_troubleshooting.py` | 5 | Ranking, similarity cut-off, empty knowledge base, model failure |
| `test_model_loading.py` | 5 | A missing or corrupt model file falls back safely instead of crashing |
| `test_urgency.py` | 3 | Model prediction and medium fallback |
| `test_schema.py` | 2 | Migrations create every table and match the models |

## Coverage

Line coverage of `app/` is **98%** (1,143 statements, 21 not run). Every route module except
two is at 100%, as are the models, schemas, accounts, security and all AI components except one
branch. What isn't run:

| Lines | Why |
|---|---|
| `database.py` 38-42 | The production `get_db`; tests swap in their own SQLite session |
| `main.py` 22, 73-82 | The default-secret-key warning and serving the built frontend, which needs `npm run build` |
| `troubleshooting.py` 31-33 | Loading the real sentence-transformer, replaced by a stand-in in unit tests (exercised by `ml/evaluate.py`) |
| `auth.py` 73-77 | Two simultaneous sign-ups with the same phone or email; the message logic is tested directly in `TestConflictingField` |
| `users.py` 55-57 | The same race when two staff accounts are created with one email at the same moment |

## Manual checks

Before a demo, with the backend and frontend running, walk through the complaint-to-resolution
flow in [architecture.md](architecture.md#41-complaint-to-resolution) once per role: register a
customer, add equipment, check for a quick fix, raise a complaint, assign it as admin, record
readings, dictate a report and resolve it as the technician, then read the report and the
notifications as the customer. Speech-to-text needs Chrome or Edge.
