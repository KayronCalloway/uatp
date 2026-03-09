#!/bin/bash
# Helper script to add rich reasoning capsules to PostgreSQL

# Usage: ./add_rich_capsule_to_postgres.sh

echo " Adding rich capsule to PostgreSQL..."

psql -d uatp_capsule_engine << 'SQL'
INSERT INTO capsules (capsule_id, capsule_type, version, timestamp, status, verification, payload)
VALUES (
  'caps_2025_12_05_pg_rich_002',
  'reasoning_trace',
  '7.0',
  NOW(),
  'sealed',
  '{"verified": true, "hash": "demo123", "signature": "sig123", "method": "ed25519", "signer": "Demo System"}',
  '{
    "prompt": "Example rich reasoning capsule",
    "reasoning_steps": [
      {
        "step_id": 1,
        "reasoning": "First step with measurements",
        "confidence": 0.98,
        "operation": "analysis",
        "confidence_basis": "measured data",
        "measurements": {
          "metric_a": 150,
          "metric_b": 3.5
        },
        "alternatives_considered": ["Option A", "Option B", "Option C"]
      },
      {
        "step_id": 2,
        "reasoning": "Second step with uncertainty",
        "confidence": 0.85,
        "operation": "decision",
        "uncertainty_sources": ["Limited data", "External factors"],
        "alternatives_considered": ["Approach X", "Approach Y"]
      }
    ],
    "final_answer": "Completed analysis",
    "confidence": 0.91,
    "model_used": "Claude Sonnet 4.5",
    "created_by": "UATP System"
  }'
);
SQL

echo "[OK] Rich capsule added!"
echo "   ID: caps_2025_12_05_pg_rich_002"
echo "   View at: http://localhost:3000 → Capsules → caps_2025_12_05_pg_rich_002"
