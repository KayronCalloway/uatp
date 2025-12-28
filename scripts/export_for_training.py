#!/usr/bin/env python3
"""
Export Capsules for Fine-Tuning
================================

Exports capsules to JSONL format suitable for:
- Fine-tuning language models
- Training confidence calibration models
- Building retrieval datasets

Formats supported:
- conversation: User/Assistant turns (for chat fine-tuning)
- reasoning: Step-by-step reasoning traces
- calibration: Confidence vs outcome pairs
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.models.capsule import CapsuleModel


DATABASE_URL = "postgresql+asyncpg://uatp_user@localhost:5432/uatp_capsule_engine"


class TrainingExporter:
    """Export capsules in various training formats."""

    def __init__(self):
        self.engine = create_async_engine(DATABASE_URL, echo=False)
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def fetch_capsules(
        self,
        min_steps: int = 1,
        min_confidence: float = 0.0,
        outcome_filter: Optional[str] = None,
        platform_filter: Optional[str] = None,
    ) -> List[CapsuleModel]:
        """Fetch capsules with optional filters."""
        async with self.async_session() as session:
            query = select(CapsuleModel)

            if outcome_filter:
                query = query.where(CapsuleModel.outcome_status == outcome_filter)

            result = await session.execute(query)
            capsules = result.scalars().all()

            # Filter in Python for JSON fields
            filtered = []
            for c in capsules:
                payload = c.payload or {}
                steps = payload.get("reasoning_steps", [])
                confidence = payload.get("confidence", 0)
                platform = (payload.get("session_metadata") or {}).get("platform", "")

                if len(steps) >= min_steps and confidence >= min_confidence:
                    if platform_filter is None or platform == platform_filter:
                        filtered.append(c)

            return filtered

    def format_conversation(self, capsule: CapsuleModel) -> List[Dict[str, Any]]:
        """
        Format as conversation turns for chat fine-tuning.

        Output format (OpenAI/Anthropic compatible):
        {"messages": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
        """
        payload = capsule.payload or {}
        steps = payload.get("reasoning_steps", [])
        session_meta = payload.get("session_metadata", {})

        messages = []
        for step in steps:
            if isinstance(step, dict):
                role = (
                    "user"
                    if step.get("operation") in ("query", "request")
                    else "assistant"
                )
                content = step.get("reasoning", "")
                if content:
                    messages.append({"role": role, "content": content})

        if not messages:
            return []

        # Build training example
        example = {
            "messages": messages,
            "metadata": {
                "capsule_id": capsule.capsule_id,
                "platform": session_meta.get("platform", "unknown"),
                "confidence": payload.get("confidence"),
                "outcome": capsule.outcome_status,
                "topics": session_meta.get("topics", []),
            },
        }

        return [example]

    def format_reasoning(self, capsule: CapsuleModel) -> List[Dict[str, Any]]:
        """
        Format as reasoning traces for chain-of-thought training.

        Output format:
        {"prompt": "...", "reasoning_steps": [...], "conclusion": "...", "confidence": 0.85}
        """
        payload = capsule.payload or {}
        steps = payload.get("reasoning_steps", [])

        if not steps:
            return []

        # Extract step content
        step_data = []
        for step in steps:
            if isinstance(step, dict):
                step_data.append(
                    {
                        "step": step.get("step_id", step.get("step")),
                        "reasoning": step.get("reasoning", ""),
                        "confidence": step.get("confidence", 0.7),
                        "operation": step.get("operation", "analysis"),
                    }
                )

        example = {
            "prompt": payload.get("prompt", ""),
            "reasoning_steps": step_data,
            "conclusion": payload.get("final_answer", ""),
            "overall_confidence": payload.get("confidence"),
            "uncertainty_analysis": payload.get("uncertainty_analysis"),
            "critical_path": payload.get("critical_path_analysis", {}).get(
                "critical_steps"
            ),
            "metadata": {
                "capsule_id": capsule.capsule_id,
                "outcome": capsule.outcome_status,
                "user_rating": capsule.user_feedback_rating,
            },
        }

        return [example]

    def format_calibration(self, capsule: CapsuleModel) -> List[Dict[str, Any]]:
        """
        Format for confidence calibration training.

        Output format:
        {"features": {...}, "predicted_confidence": 0.85, "actual_outcome": "success"}
        """
        if not capsule.outcome_status:
            return []  # Need outcome for calibration

        payload = capsule.payload or {}
        steps = payload.get("reasoning_steps", [])
        session_meta = payload.get("session_metadata", {})
        uncertainty = payload.get("uncertainty_analysis", {})

        # Extract features for calibration model
        features = {
            "num_steps": len(steps),
            "avg_step_confidence": sum(
                s.get("confidence", 0.7) for s in steps if isinstance(s, dict)
            )
            / max(len(steps), 1),
            "has_code": any(
                "```" in s.get("reasoning", "") for s in steps if isinstance(s, dict)
            ),
            "has_questions": any(
                "?" in s.get("reasoning", "") for s in steps if isinstance(s, dict)
            ),
            "epistemic_uncertainty": uncertainty.get("epistemic_uncertainty", 0),
            "aleatoric_uncertainty": uncertainty.get("aleatoric_uncertainty", 0),
            "platform": session_meta.get("platform", "unknown"),
            "conversation_depth": session_meta.get("conversation_depth", 1),
            "topics": session_meta.get("topics", []),
        }

        # Map outcome to numeric
        outcome_map = {"success": 1.0, "partial": 0.5, "failure": 0.0, "unknown": None}
        actual = outcome_map.get(capsule.outcome_status)

        if actual is None:
            return []

        example = {
            "features": features,
            "predicted_confidence": payload.get("confidence", 0.5),
            "actual_outcome": capsule.outcome_status,
            "actual_outcome_numeric": actual,
            "user_rating": capsule.user_feedback_rating,
            "capsule_id": capsule.capsule_id,
        }

        return [example]

    async def export(
        self,
        output_path: str,
        format_type: str = "conversation",
        min_steps: int = 1,
        min_confidence: float = 0.0,
        outcome_filter: Optional[str] = None,
        platform_filter: Optional[str] = None,
    ) -> int:
        """Export capsules to JSONL file."""
        capsules = await self.fetch_capsules(
            min_steps=min_steps,
            min_confidence=min_confidence,
            outcome_filter=outcome_filter,
            platform_filter=platform_filter,
        )

        format_funcs = {
            "conversation": self.format_conversation,
            "reasoning": self.format_reasoning,
            "calibration": self.format_calibration,
        }

        format_func = format_funcs.get(format_type)
        if not format_func:
            raise ValueError(f"Unknown format: {format_type}")

        count = 0
        with open(output_path, "w") as f:
            for capsule in capsules:
                examples = format_func(capsule)
                for example in examples:
                    f.write(json.dumps(example, default=str) + "\n")
                    count += 1

        return count


async def main():
    parser = argparse.ArgumentParser(
        description="Export capsules for fine-tuning",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Export all as conversation format
  python export_for_training.py -o training.jsonl -f conversation

  # Export successful outcomes for calibration
  python export_for_training.py -o calibration.jsonl -f calibration --outcome success

  # Export reasoning traces with high confidence
  python export_for_training.py -o reasoning.jsonl -f reasoning --min-confidence 0.7
        """,
    )

    parser.add_argument(
        "-o",
        "--output",
        default="training_export.jsonl",
        help="Output file path (default: training_export.jsonl)",
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=["conversation", "reasoning", "calibration"],
        default="conversation",
        help="Export format (default: conversation)",
    )
    parser.add_argument(
        "--min-steps",
        type=int,
        default=1,
        help="Minimum reasoning steps required (default: 1)",
    )
    parser.add_argument(
        "--min-confidence",
        type=float,
        default=0.0,
        help="Minimum confidence score (default: 0.0)",
    )
    parser.add_argument(
        "--outcome",
        choices=["success", "failure", "partial", "pending", "unknown"],
        help="Filter by outcome status",
    )
    parser.add_argument(
        "--platform",
        help="Filter by platform (e.g., claude-code, google_antigravity)",
    )

    args = parser.parse_args()

    print(f"Exporting capsules to {args.output}")
    print(f"  Format: {args.format}")
    print(f"  Min steps: {args.min_steps}")
    print(f"  Min confidence: {args.min_confidence}")
    if args.outcome:
        print(f"  Outcome filter: {args.outcome}")
    if args.platform:
        print(f"  Platform filter: {args.platform}")

    exporter = TrainingExporter()
    count = await exporter.export(
        output_path=args.output,
        format_type=args.format,
        min_steps=args.min_steps,
        min_confidence=args.min_confidence,
        outcome_filter=args.outcome,
        platform_filter=args.platform,
    )

    print(f"\n✅ Exported {count} examples to {args.output}")

    # Show sample
    print("\n📄 Sample (first 3 lines):")
    with open(args.output) as f:
        for i, line in enumerate(f):
            if i >= 3:
                break
            data = json.loads(line)
            # Truncate for display
            preview = json.dumps(data, default=str)[:200]
            print(f"  {preview}...")


if __name__ == "__main__":
    asyncio.run(main())
