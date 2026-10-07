-- Existing student rows predate OTP-gated registration and were marked
-- verified by the old database default. Require one email OTP before they
-- can log in or appear in admin student lists. Their IDs and exam records
-- remain unchanged.
UPDATE users
SET email_verified = FALSE
WHERE lower(role) = 'student'
  AND email_verified IS DISTINCT FROM FALSE;
