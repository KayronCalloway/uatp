-- Migration: Add outcome tracking columns to capsules table
-- Run this against the PostgreSQL database

-- Add outcome tracking columns
ALTER TABLE capsules ADD COLUMN IF NOT EXISTS outcome_status VARCHAR;
ALTER TABLE capsules ADD COLUMN IF NOT EXISTS outcome_timestamp TIMESTAMP WITH TIME ZONE;
ALTER TABLE capsules ADD COLUMN IF NOT EXISTS outcome_notes TEXT;
ALTER TABLE capsules ADD COLUMN IF NOT EXISTS outcome_metrics JSONB;
ALTER TABLE capsules ADD COLUMN IF NOT EXISTS user_feedback_rating FLOAT;
ALTER TABLE capsules ADD COLUMN IF NOT EXISTS user_feedback_text TEXT;
ALTER TABLE capsules ADD COLUMN IF NOT EXISTS follow_up_capsule_ids JSONB;

-- Add index for outcome status queries
CREATE INDEX IF NOT EXISTS idx_capsules_outcome_status ON capsules(outcome_status);

-- Add index for finding capsules needing outcome review
CREATE INDEX IF NOT EXISTS idx_capsules_outcome_pending ON capsules(outcome_status)
    WHERE outcome_status IS NULL OR outcome_status = 'pending';

-- Add check constraint for valid outcome statuses
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_outcome_status'
    ) THEN
        ALTER TABLE capsules ADD CONSTRAINT chk_outcome_status
            CHECK (outcome_status IS NULL OR outcome_status IN ('success', 'failure', 'partial', 'pending', 'unknown'));
    END IF;
END $$;

-- Add check constraint for rating range
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_feedback_rating'
    ) THEN
        ALTER TABLE capsules ADD CONSTRAINT chk_feedback_rating
            CHECK (user_feedback_rating IS NULL OR (user_feedback_rating >= 1 AND user_feedback_rating <= 5));
    END IF;
END $$;

-- Comment on columns for documentation
COMMENT ON COLUMN capsules.outcome_status IS 'Outcome of the capsule: success, failure, partial, pending, unknown';
COMMENT ON COLUMN capsules.outcome_timestamp IS 'When the outcome was recorded';
COMMENT ON COLUMN capsules.outcome_notes IS 'Free-form notes about the outcome';
COMMENT ON COLUMN capsules.outcome_metrics IS 'Structured metrics like tests_passed, errors_fixed, time_saved';
COMMENT ON COLUMN capsules.user_feedback_rating IS 'User rating from 1-5';
COMMENT ON COLUMN capsules.user_feedback_text IS 'User feedback text';
COMMENT ON COLUMN capsules.follow_up_capsule_ids IS 'List of capsule IDs that followed up on this one';
