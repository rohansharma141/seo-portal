-- Addendum v1.1 — add metadata JSONB to audits (backlinks live in
-- audits.metadata['backlinks']). Build Doc §4.2 did not include this column;
-- the addendum assumed it existed, so it is added here.
--
-- Apply on Supabase after 001_initial_schema.sql, or via:
--   .\.venv\Scripts\python.exe -m alembic upgrade head   (revision 0002)

ALTER TABLE audits
    ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}';
