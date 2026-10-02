-- Expand stored score capacity so large question sets can be scored without
-- numeric overflow. This is safe for existing result values.
ALTER TABLE results
    ALTER COLUMN score TYPE NUMERIC(10, 2)
    USING score::NUMERIC(10, 2);
