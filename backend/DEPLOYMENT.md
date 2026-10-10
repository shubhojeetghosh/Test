# Backend deployment and one-time data setup

## Supabase Storage

Create a **private** Storage bucket named `exam-media` and set both the global and bucket maximum file size to 50 MB (subject to your Supabase plan). Apply `migrations/2026_10_lock_down_public_storage.sql` to enforce the private bucket, file size, and image/audio MIME allowlist in Storage itself. Keep the service-role key only in the backend environment; do not add it to frontend files or a `NEXT_PUBLIC_` variable. The backend issues short-lived signed links for private media and short-lived signed upload links so browser uploads go directly to Storage. See Supabase's [signed URL](https://supabase.com/docs/reference/python/storage-from-createsignedurls) and [signed upload URL](https://supabase.com/docs/reference/python/storage-from-createsigneduploadurl) documentation.

Set these variables on the Vercel **backend** project (Root Directory: `backend`) and in a local `backend/.env`:

```text
DATABASE_URL=postgresql+psycopg://...
SECRET_KEY=<unique random secret, at least 32 bytes>
# Optional during JWT signing key rotation; remove after old sessions expire.
SECRET_KEY_PREVIOUS=<previous secret during rotation only>
SUPABASE_URL=https://<project-ref>.supabase.co
SUPABASE_SERVICE_ROLE_KEY=<server-only key>
SUPABASE_MEDIA_BUCKET=exam-media
SMTP_HOST=...
SMTP_PORT=587
SMTP_USERNAME=...
SMTP_PASSWORD=...
SMTP_FROM_EMAIL=...
ZEROBOUNCE_API_KEY=...
CORS_ORIGINS=https://<frontend-project>.vercel.app
```

Admin sign-in uses the admin email address and password. Browser sessions use
HttpOnly, Secure, SameSite cookies; the frontend Vercel project proxies API
requests through `/backend/*` so these cookies stay first-party. Deploy the
frontend rewrite and backend together. Never restore JWT access tokens to
browser storage.

Use a unique randomly generated `SECRET_KEY` of at least 32 bytes. To rotate it,
set the new value in `SECRET_KEY` and the old value in `SECRET_KEY_PREVIOUS`,
redeploy both backend instances together, wait at least three hours, then remove
`SECRET_KEY_PREVIOUS` and redeploy. Keep the same secret across student and admin
auth settings.

Never commit `backend/.env`. The `.env.example` file contains placeholders only.
Student registration uses ZeroBounce's real-time mailbox validation before sending an OTP. Set `ZEROBOUNCE_API_KEY` on the backend Vercel project; if it is missing or the validation service is unavailable, registration fails closed and no OTP is sent. Only addresses returned with status `valid` proceed to the OTP step.

## PostgreSQL migration

Back up the database first. Open [`migrations/2026_10_set_scoped_attempts_and_questions.sql`](migrations/2026_10_set_scoped_attempts_and_questions.sql), run the two duplicate-check queries, and resolve any rows they return. Then apply the schema/index statements in order. The `CREATE INDEX CONCURRENTLY` statements must each run outside a transaction; use a PostgreSQL client in autocommit mode and run them separately. Do not rerun the initial duplicate-check result as an update statement.

The migration adds set IDs to attempts and replaces the old exam-wide question-number uniqueness rule with a per-set rule. Existing attempts remain set-less and retain legacy behavior; newly started attempts are set-scoped.

For student set purchase requests and admin set unlocks, apply
[`migrations/2026_10_student_set_access_requests.sql`](migrations/2026_10_student_set_access_requests.sql)
to the production database before using checkout or the admin access controls.

For student profile photo uploads, apply
[`migrations/2026_10_student_profile_photo.sql`](migrations/2026_10_student_profile_photo.sql)
before deploying the profile API changes. Profile images use the existing private
`exam-media` Supabase Storage bucket under the `profiles/` prefix.

Apply [`migrations/2026_10_enable_public_rls.sql`](migrations/2026_10_enable_public_rls.sql)
to the production database to deny direct Supabase Data API access to public
tables. This project performs application-level student/admin authorization in
FastAPI using a private database connection. Keep that connection string
server-only and use a controlled database role that owns the app tables or has
the required RLS bypass privileges; this migration intentionally does not force
RLS on that backend role.

## Existing image/audio migration

After Storage and the database are configured, run a dry run from the `backend` directory:

```text
python scripts/migrate_embedded_media_to_supabase.py
```

If the counts look right, add `--apply`. The script updates only rows containing a data URL, commits each migrated row after the Storage upload succeeds, and reports failures for manual follow-up. Keep the database backup until the migrated media has been checked in the deployed exam flow.

## Current delivery envelope

Each set is currently limited to 2,000 questions because an exam attempt and its review are loaded as a full set. Student list reads are paginated in blocks of 200. This is a code limit, not a promise of a specific concurrent-user count. Concurrent capacity still depends on the PostgreSQL plan/connection pool, Vercel limits, Storage bandwidth, and measured load tests. Use a pooled PostgreSQL connection URL for serverless deployments and keep `DB_POOL_SIZE`/`DB_MAX_OVERFLOW` within the database provider's connection budget.
