-- Student purchase requests and admin-granted set access.
-- Apply this migration to the production database before deploying code that
-- handles checkout requests or unlocks paid sets.

CREATE TABLE IF NOT EXISTS student_exam_access (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    exam_set_id INTEGER NOT NULL REFERENCES exam_sets(id) ON DELETE CASCADE,
    unlocked_by INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    unlocked_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_student_exam_set_access UNIQUE (student_id, exam_set_id)
);

CREATE TABLE IF NOT EXISTS student_set_purchase_requests (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    exam_set_id INTEGER NOT NULL REFERENCES exam_sets(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    requested_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    handled_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    handled_at TIMESTAMP WITHOUT TIME ZONE,
    CONSTRAINT uq_student_set_purchase_request UNIQUE (student_id, exam_set_id)
);

CREATE INDEX IF NOT EXISTS ix_student_set_purchase_requests_pending
    ON student_set_purchase_requests (status, requested_at)
    WHERE status = 'PENDING';
