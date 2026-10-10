-- Default-deny the Supabase Data API for every public table. This app accesses
-- PostgreSQL through its private FastAPI backend, not directly from browsers.
-- Keep DATABASE_URL and its database credentials on the backend only.
--
-- The backend DB role must be the trusted table owner or a controlled role
-- with BYPASSRLS. This migration deliberately does not FORCE RLS because the
-- backend performs user/admin authorization in FastAPI and does not pass a
-- Supabase Auth JWT into PostgreSQL. Applying FORCE RLS would break that app.
DO $$
DECLARE
    item RECORD;
BEGIN
    -- Remove existing table policies on these application tables. RLS with a
    -- permissive legacy policy would still expose rows through the Data API.
    FOR item IN
        SELECT schemaname, tablename, policyname
        FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename <> 'alembic_version'
    LOOP
        EXECUTE format(
            'DROP POLICY %I ON %I.%I',
            item.policyname, item.schemaname, item.tablename
        );
    END LOOP;

    FOR item IN
        SELECT schemaname, tablename
        FROM pg_tables
        WHERE schemaname = 'public'
          AND tablename <> 'alembic_version'
    LOOP
        EXECUTE format(
            'ALTER TABLE %I.%I ENABLE ROW LEVEL SECURITY',
            item.schemaname,
            item.tablename
        );
    END LOOP;
END $$;
