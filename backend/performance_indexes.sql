-- Run these statements separately using a PostgreSQL connection in
-- autocommit mode. CONCURRENTLY avoids blocking normal reads and writes
-- while the indexes are built.

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_questions_set_status_number
    ON questions (set_id, status, question_number);

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_exam_sessions_user_exam_id
    ON exam_sessions (user_id, exam_id, id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_audio_play_logs_attempt_question
    ON audio_play_logs (attempt_id, question_id);
