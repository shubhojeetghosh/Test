-- Enforce upload constraints in Supabase Storage itself. Signed upload URLs
-- bypass the FastAPI request body, so browser-side checks cannot be trusted.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM storage.buckets WHERE name = 'exam-media'
    ) THEN
        RAISE EXCEPTION 'Create the private exam-media bucket before applying this migration';
    END IF;
END $$;

UPDATE storage.buckets
SET
    public = FALSE,
    file_size_limit = 52428800,
    allowed_mime_types = ARRAY[
        'image/jpeg', 'image/png', 'image/webp',
        'audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/x-wav',
        'audio/ogg', 'audio/webm', 'audio/mp4', 'audio/aac'
    ]::text[]
WHERE name = 'exam-media';
