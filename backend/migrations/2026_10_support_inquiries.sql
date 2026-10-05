-- Student questions submitted from the public About / Contact form.
-- Apply this migration before deploying the API code that writes to this table.
-- The contact endpoint uses the same shared limiter as the auth routes.
CREATE TABLE IF NOT EXISTS api_rate_limits (
    scope VARCHAR(64) NOT NULL,
    subject_hash CHAR(64) NOT NULL,
    window_started_at TIMESTAMPTZ NOT NULL,
    request_count INTEGER NOT NULL CHECK (request_count > 0),
    PRIMARY KEY (scope, subject_hash)
);

CREATE INDEX IF NOT EXISTS ix_api_rate_limits_window_started_at
    ON api_rate_limits (window_started_at);

CREATE TABLE IF NOT EXISTS support_inquiries (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(254) NOT NULL,
    subject VARCHAR(160) NOT NULL,
    message TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'new'
        CHECK (status IN ('new', 'resolved')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_support_inquiries_created_at
    ON support_inquiries (created_at DESC, id DESC);

CREATE INDEX IF NOT EXISTS ix_support_inquiries_status
    ON support_inquiries (status, created_at DESC);
