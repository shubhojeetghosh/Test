-- Store the private Supabase Storage object reference for each student's photo.
ALTER TABLE users
    ADD COLUMN IF NOT EXISTS profile_photo_url TEXT;
