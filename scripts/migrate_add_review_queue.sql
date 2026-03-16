-- Migration: Add outcome review queue table for human-in-the-loop feedback
-- Part of the hybrid auto-outcome detection system

-- Create review queue table
CREATE TABLE IF NOT EXISTS outcome_review_queue (
    id VARCHAR(255) PRIMARY KEY,
    capsule_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Inference details (what the auto-system guessed)
    inferred_status VARCHAR(50),
    inference_confidence FLOAT,
    inference_method VARCHAR(100),
    inference_signals JSONB,
    inference_scores JSONB,

    -- Context for reviewer
    original_message TEXT,
    follow_up_message TEXT,
    conversation_context JSONB,

    -- Review metadata
    priority VARCHAR(50) DEFAULT 'medium',
    status VARCHAR(50) DEFAULT 'pending',
    assigned_to VARCHAR(255),
    assigned_at TIMESTAMP WITH TIME ZONE,

    -- Review result
    reviewed_at TIMESTAMP WITH TIME ZONE,
    reviewed_by VARCHAR(255),
    human_status VARCHAR(50),
    human_confidence FLOAT,
    review_notes TEXT,

    -- Feedback for model improvement
    inference_was_correct BOOLEAN,
    feedback_used_for_training BOOLEAN DEFAULT FALSE
);

-- Indexes for efficient queue operations
CREATE INDEX IF NOT EXISTS idx_review_queue_status
    ON outcome_review_queue(status);

CREATE INDEX IF NOT EXISTS idx_review_queue_priority_confidence
    ON outcome_review_queue(priority, inference_confidence)
    WHERE status = 'pending';

CREATE INDEX IF NOT EXISTS idx_review_queue_capsule
    ON outcome_review_queue(capsule_id);

CREATE INDEX IF NOT EXISTS idx_review_queue_created
    ON outcome_review_queue(created_at DESC);

-- For training data export
CREATE INDEX IF NOT EXISTS idx_review_queue_training
    ON outcome_review_queue(feedback_used_for_training)
    WHERE status = 'completed' AND human_status IS NOT NULL;

-- Add comment
COMMENT ON TABLE outcome_review_queue IS
    'Human-in-the-loop review queue for uncertain outcome inferences.
     Part of the hybrid auto-outcome detection system with active learning.';

-- Verify
SELECT 'Review queue migration complete' AS status;
