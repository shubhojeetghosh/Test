-- Quiz scalability/schema migration (PostgreSQL / Supabase SQL Editor)
--
-- Before continuing, run the two duplicate checks below. If either returns
-- rows, correct those question numbers before building the unique indexes.
-- Run CREATE INDEX CONCURRENTLY statements one at a time; they cannot run
-- inside a transaction block.

-- Check duplicate question numbers within a set:
SELECT set_id, question_number, COUNT(*) AS duplicate_count
FROM questions
WHERE set_id IS NOT NULL
GROUP BY set_id, question_number
HAVING COUNT(*) > 1;

-- Check duplicate legacy question numbers on questions not assigned to a set:
SELECT exam_id, question_number, COUNT(*) AS duplicate_count
FROM questions
WHERE set_id IS NULL
GROUP BY exam_id, question_number
HAVING COUNT(*) > 1;

-- Apply the schema change after both checks return no rows.
ALTER TABLE exam_sessions
    ADD COLUMN IF NOT EXISTS set_id INTEGER
    REFERENCES exam_sets(id) ON DELETE SET NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_exam_sessions_user_exam_set_status_id
    ON exam_sessions (user_id, exam_id, set_id, status, id);

CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS uq_questions_set_number
    ON questions (set_id, question_number)
    WHERE set_id IS NOT NULL;

CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS uq_questions_unassigned_exam_number
    ON questions (exam_id, question_number)
    WHERE set_id IS NULL;

-- The legacy exam-wide unique constraint prevents the same question number
-- from being reused in different sets. Replace it with the partial indexes.
ALTER TABLE questions
    DROP CONSTRAINT IF EXISTS unique_question_number;

-- Supporting indexes used by paged reads and audio-play lookups.
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_questions_set_status_number
    ON questions (set_id, status, question_number);

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_audio_play_logs_attempt_question
    ON audio_play_logs (attempt_id, question_id);
