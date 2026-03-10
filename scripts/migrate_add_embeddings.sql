-- Migration: Add embeddings support to capsules table
-- Uses JSONB arrays for portability (no pgvector required)
-- Date: 2026-01-02

-- Add embedding column (1536 dimensions for OpenAI text-embedding-3-small)
ALTER TABLE capsules ADD COLUMN IF NOT EXISTS embedding JSONB;

-- Add embedding metadata
ALTER TABLE capsules ADD COLUMN IF NOT EXISTS embedding_model VARCHAR(100);
ALTER TABLE capsules ADD COLUMN IF NOT EXISTS embedding_created_at TIMESTAMP WITH TIME ZONE;

-- Create index on embedding existence for fast filtering
CREATE INDEX IF NOT EXISTS idx_capsules_has_embedding
ON capsules ((embedding IS NOT NULL));

-- Note: Cosine similarity will be computed in Python due to plpgsql library issue
-- The embedder module handles similarity search efficiently

-- Verify migration
SELECT 'Migration complete: embedding columns added to capsules table' as status;
