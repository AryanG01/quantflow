-- Migration 003: Fix sentiment_events.title nullable in composite PK
-- NULL values in a PK column make rows un-dedupable (NULL != NULL in SQL).
-- Setting DEFAULT '' + NOT NULL restores intended uniqueness semantics.
ALTER TABLE sentiment_events ALTER COLUMN title SET DEFAULT '';
UPDATE sentiment_events SET title = '' WHERE title IS NULL;
ALTER TABLE sentiment_events ALTER COLUMN title SET NOT NULL;
