# AssetFlow

IT asset management API built with FastAPI and SQLAlchemy.

## Run the backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

- Web UI: http://127.0.0.1:8000/ui/ (served from `frontend/`; plain HTML/CSS/JS with no build step, and it follows the system's light/dark setting)
- Interactive API docs: http://127.0.0.1:8000/docs

The SQLite database is created at `backend/assetflow.db`. Set `ASSETFLOW_DATABASE_URL` to use a different database.

## Endpoints

| Resource  | Endpoints |
|-----------|-----------|
| Assets    | `GET/POST /assets`, `GET/PUT/DELETE /assets/{id}` |
| Employees | `GET/POST /employees`, `GET/PUT/DELETE /employees/{id}` |
| Users     | `GET /users` (read-only; never returns password hashes) |

Duplicate `asset_tag`, `serial_number` or employee `email` returns **409 Conflict**.

## Tests

```bash
cd backend
pytest
```
