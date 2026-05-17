# Migrations

Two equivalent representations of the schema (Section 4) are kept in sync:

- **`001_initial_schema.sql`** — plain SQL, the verbatim Section 4 schema.
  Fastest path on Supabase: paste into the SQL editor, or
  `psql "$DATABASE_URL" -f backend/migrations/001_initial_schema.sql`.
- **`../alembic/`** — Alembic project. Revision `0001` creates the same
  schema; all schema changes from Step 2 onward are new Alembic revisions
  (`alembic revision --autogenerate -m "..."` against the models).

Apply with Alembic once `DATABASE_URL` is set (run from `backend/`):

```
.\.venv\Scripts\python.exe -m alembic upgrade head
```

Preview the SQL without a database connection:

```
.\.venv\Scripts\python.exe -m alembic upgrade head --sql
```
