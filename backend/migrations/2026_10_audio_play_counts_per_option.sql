-- Keep question-level audio and each answer-option clip on independent
-- two-play counters. The existing unique index on only
-- (attempt_id, question_id) makes every option after the first collide.
DROP INDEX IF EXISTS uq_audio_play_attempt_question;

CREATE UNIQUE INDEX IF NOT EXISTS uq_audio_play_logs_question_audio
    ON audio_play_logs (attempt_id, question_id)
    WHERE option_id IS NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_audio_play_logs_option_audio
    ON audio_play_logs (attempt_id, question_id, option_id)
    WHERE option_id IS NOT NULL;
