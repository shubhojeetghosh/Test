-- Shared rate limits for sensitive API routes across Vercel instances.
-- Safe to apply more than once. The subject is an HMAC, never raw user data.
CREATE TABLE IF NOT EXISTS api_rate_limits (
    scope VARCHAR(64) NOT NULL,
    subject_hash CHAR(64) NOT NULL,
    window_started_at TIMESTAMPTZ NOT NULL,
    request_count INTEGER NOT NULL CHECK (request_count > 0),
    PRIMARY KEY (scope, subject_hash)
);

CREATE INDEX IF NOT EXISTS ix_api_rate_limits_window_started_at
    ON api_rate_limits (window_started_at);

-- Periodically remove expired buckets (for example, daily via your database
-- scheduler) so old email hashes do not accumulate indefinitely.
-- DELETE FROM api_rate_limits
-- WHERE window_started_at < now() - interval '2 days';
