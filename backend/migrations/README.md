# Migrations

Alembic migrations are the database schema source of truth.

- `eb584a4dd816_initial_schema.py` creates the eight Task 02 tables, constraints,
  indexes, and PostgreSQL enum types.
- Its downgrade removes both tables and enum types, so a clean up/down/up round
  trip succeeds.

Run `uv run alembic upgrade head` from `backend/`. Only run a downgrade against a
disposable database because it removes stored rows.
