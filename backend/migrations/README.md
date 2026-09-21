# Migrations

Alembic migrations are the database schema source of truth.

- `eb584a4dd816_initial_schema.py` creates the eight Task 02 tables, constraints,
  indexes, and PostgreSQL enum types.
- Its downgrade removes both tables and enum types, so a clean up/down/up round
  trip succeeds.
- `382806336a30_add_import_metadata_and_rule_timezone.py` adds duplicate counts,
  detected CSV fields, and the rule timezone needed by the import API.

Run `uv run alembic upgrade head` from `backend/`. Only run a downgrade against a
disposable database because it removes stored rows.

Run `uv run alembic check` after model changes to detect schema drift.
