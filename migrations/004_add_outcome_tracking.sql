-- Migration: Add outcome tracking tables
-- Date: 2025-12-05
-- Description: Track actual outcomes of capsules to validate predictions and calibrate confidence

-- Outcomes table
CREATE TABLE IF NOT EXISTS capsule_outcomes (
    id SERIAL PRIMARY KEY,
    capsule_id VARCHAR NOT NULL,
    predicted_outcome TEXT,
    actual_outcome TEXT NOT NULL,
    outcome_quality_score FLOAT CHECK (outcome_quality_score BETWEEN 0 AND 1),
    outcome_timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    validation_method VARCHAR(50),  -- 'user_feedback', 'automated_test', 'system_metric'
    validator_id VARCHAR,  -- Who validated (user ID, system name)
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Foreign key (soft reference, capsule might not exist yet)
    CONSTRAINT fk_capsule
        FOREIGN KEY (capsule_id)
        REFERENCES capsules(capsule_id)
        ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_outcomes_capsule_id ON capsule_outcomes(capsule_id);
CREATE INDEX IF NOT EXISTS idx_outcomes_timestamp ON capsule_outcomes(outcome_timestamp);
CREATE INDEX IF NOT EXISTS idx_outcomes_quality ON capsule_outcomes(outcome_quality_score);
CREATE INDEX IF NOT EXISTS idx_outcomes_validation_method ON capsule_outcomes(validation_method);

-- Confidence calibration table
CREATE TABLE IF NOT EXISTS confidence_calibration (
    id SERIAL PRIMARY KEY,
    domain VARCHAR(100),  -- Problem domain (backend-api, frontend-ui, etc.)
    confidence_bucket FLOAT CHECK (confidence_bucket BETWEEN 0 AND 1),
    predicted_count INTEGER DEFAULT 0,
    actual_success_count INTEGER DEFAULT 0,
    calibration_error FLOAT,
    recommended_adjustment FLOAT,
    sample_capsule_ids VARCHAR[],  -- Sample of capsules in this bucket
    last_updated TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(domain, confidence_bucket)
);

CREATE INDEX IF NOT EXISTS idx_calibration_domain ON confidence_calibration(domain);
CREATE INDEX IF NOT EXISTS idx_calibration_bucket ON confidence_calibration(confidence_bucket);

-- Reasoning patterns table
CREATE TABLE IF NOT EXISTS reasoning_patterns (
    pattern_id VARCHAR PRIMARY KEY,
    pattern_type VARCHAR(50),  -- 'sequence', 'decision_tree', 'failure_mode', etc.
    pattern_name VARCHAR(200),
    pattern_description TEXT,
    pattern_structure JSONB,  -- Detailed pattern structure
    success_rate FLOAT CHECK (success_rate BETWEEN 0 AND 1),
    usage_count INTEGER DEFAULT 0,
    applicable_domains VARCHAR[],
    example_capsule_ids VARCHAR[],
    confidence_impact FLOAT,  -- How much this pattern affects confidence
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_patterns_type ON reasoning_patterns(pattern_type);
CREATE INDEX IF NOT EXISTS idx_patterns_domain ON reasoning_patterns USING GIN(applicable_domains);
CREATE INDEX IF NOT EXISTS idx_patterns_success_rate ON reasoning_patterns(success_rate);

-- Comments for documentation
COMMENT ON TABLE capsule_outcomes IS 'Tracks actual outcomes of capsule predictions for validation and learning';
COMMENT ON TABLE confidence_calibration IS 'Calibration data to improve confidence predictions over time';
COMMENT ON TABLE reasoning_patterns IS 'Discovered patterns in successful and failed reasoning';

COMMENT ON COLUMN capsule_outcomes.outcome_quality_score IS 'Quality score 0-1, where 1 means prediction was perfect';
COMMENT ON COLUMN capsule_outcomes.validation_method IS 'How the outcome was validated: user_feedback, automated_test, system_metric';

COMMENT ON COLUMN confidence_calibration.calibration_error IS 'Difference between predicted and actual success rate';
COMMENT ON COLUMN confidence_calibration.recommended_adjustment IS 'Suggested adjustment to future confidence scores';

COMMENT ON COLUMN reasoning_patterns.confidence_impact IS 'How much this pattern should adjust confidence (+/- value)';
