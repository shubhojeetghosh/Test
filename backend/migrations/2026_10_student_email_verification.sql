-- Student registration email verification.
-- Safe to run more than once; preserves all existing users and OTP records.
ALTER TABLE users
    ADD COLUMN IF NOT EXISTS email_verified BOOLEAN NOT NULL DEFAULT TRUE;

ALTER TABLE password_reset_otps
    ADD COLUMN IF NOT EXISTS purpose VARCHAR(30) NOT NULL DEFAULT 'password_reset';

CREATE INDEX IF NOT EXISTS ix_password_reset_otps_user_purpose_used
    ON password_reset_otps (user_id, purpose, used);
