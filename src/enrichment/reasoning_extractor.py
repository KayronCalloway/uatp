"""
Reasoning Extractor
==================

This module provides AI-native extraction of reasoning steps from unstructured conversation text.
It uses a lightweight LLM call to synthesize structured logic from "messy" human/AI dialogue.

NOTE: This feature is EXPERIMENTAL. Enable by setting ENABLE_AI_ENRICHMENT=true
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ReasoningExtractor:
    """
    Extracts structured reasoning from unstructured text using an LLM.

    EXPERIMENTAL FEATURE - Requires ENABLE_AI_ENRICHMENT=true
    """

    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model
        self.enabled = os.getenv("ENABLE_AI_ENRICHMENT", "false").lower() == "true"
        self.llm_client = None

        if not self.enabled:
            logger.info(
                "🔬 AI Enrichment disabled (set ENABLE_AI_ENRICHMENT=true to enable)"
            )
            return

        # Initialize real LLM client
        self._initialize_llm_client()

    def _initialize_llm_client(self):
        """Initialize the LLM client with fallback logic."""

        # Helper to check if key is a placeholder
        def is_placeholder(key):
            if not key:
                return True
            placeholders = ["your-", "goes-here", "placeholder", "xxx", "sk-xxx"]
            return any(p in key.lower() for p in placeholders)

        try:
            # Try OpenAI first (most reliable for structured output)
            openai_key = os.getenv("OPENAI_API_KEY")
            if openai_key and not is_placeholder(openai_key):
                from openai import AsyncOpenAI

                self.llm_client = AsyncOpenAI(api_key=openai_key)
                self.provider = "openai"
                logger.info(f"🤖 AI Enrichment enabled using OpenAI ({self.model})")
                return
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAI client: {e}")

        try:
            # Fallback to Anthropic
            anthropic_key = os.getenv("ANTHROPIC_API_KEY")
            if anthropic_key and not is_placeholder(anthropic_key):
                import anthropic

                self.llm_client = anthropic.AsyncAnthropic(api_key=anthropic_key)
                self.provider = "anthropic"
                self.model = "claude-3-haiku-20240307"  # Fast, cheap model
                logger.info(f"🤖 AI Enrichment enabled using Anthropic ({self.model})")
                return
        except Exception as e:
            logger.warning(f"Failed to initialize Anthropic client: {e}")

        # Use local rule-based extraction as fallback (no API key needed)
        logger.info("🧠 AI Enrichment using local rule-based extraction (no API key)")
        self.provider = "local"
        self.llm_client = None  # Not needed for local extraction
        # Keep enabled=True so we can use local extraction

    async def extract_reasoning(
        self, user_input: str, ai_response: str, context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Extract reasoning steps and calculate a revised significance score.

        Args:
            user_input: The user's message
            ai_response: The AI's response (potentially unstructured)
            context: Optional context

        Returns:
            Dict with 'steps' (List) and 'suggested_score' (float)
        """
        # Check if feature is enabled
        if not self.enabled:
            logger.debug("AI enrichment disabled")
            return {"steps": [], "suggested_score": 0.0}

        # Use local extraction if no LLM client available
        if self.provider == "local" or not self.llm_client:
            return self._extract_local(user_input, ai_response, context)

        try:
            # Construct the prompt for the "Reasoning Agent"
            prompt = self._construct_prompt(user_input, ai_response)

            # Call the real LLM
            response_text = await self._call_llm(prompt)

            # Parse the JSON response
            reasoning_data = self._parse_response(response_text)

            # Enrich with timestamps and weights (v7 format)
            steps = []
            for idx, item in enumerate(reasoning_data.get("steps", []), start=1):
                steps.append(
                    {
                        "step_id": idx,
                        "operation": "ai_extraction",
                        "reasoning": item.get("description", "Unknown step"),
                        "evidence": item.get("evidence", ""),
                        "conclusion": item.get("conclusion", ""),
                        "confidence": 0.9,  # High confidence for AI-extracted reasoning
                        "weight": 0.8,
                        "step_type": "ai_extracted_reasoning",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                )

            # Calculate suggested score based on reasoning density
            # Simple heuristic: deeper reasoning = higher value
            base_score = 0.5
            if len(steps) > 0:
                base_score += min(len(steps) * 0.1, 0.45)  # Cap boost at +0.45

            return {"steps": steps, "suggested_score": round(base_score, 2)}

        except Exception as e:
            logger.error(f"❌ Reasoning extraction failed: {e}", exc_info=True)
            return {"steps": [], "suggested_score": 0.0}

    def _construct_prompt(self, user_input: str, ai_response: str) -> str:
        return f"""
        Analyze the following AI conversation and extract the underlying reasoning chain.
        Return ONLY valid JSON with a list of "steps".

        USER: {user_input}
        AI: {ai_response}

        Output format:
        {{
            "steps": [
                {{
                    "description": "Step description",
                    "evidence": "Quote from text",
                    "conclusion": "Inference made"
                }}
            ]
        }}
        """

    async def _call_llm(self, prompt: str) -> str:
        """
        Call the configured LLM provider with the reasoning extraction prompt.

        Returns:
            JSON string with extracted reasoning steps
        """
        try:
            if self.provider == "openai":
                return await self._call_openai(prompt)
            elif self.provider == "anthropic":
                return await self._call_anthropic(prompt)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
        except Exception as e:
            logger.error(f"LLM call failed: {e}", exc_info=True)
            # Return empty result on failure
            return json.dumps({"steps": []})

    async def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API with structured output support."""
        response = await self.llm_client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a reasoning analysis expert. Extract logical steps from conversations and return only valid JSON.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,  # Lower temperature for more consistent extraction
            max_tokens=1000,
            response_format={"type": "json_object"},  # Enforce JSON output
        )
        return response.choices[0].message.content

    async def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic API with JSON mode."""
        message = await self.llm_client.messages.create(
            model=self.model,
            max_tokens=1000,
            temperature=0.3,
            system="You are a reasoning analysis expert. Extract logical steps from conversations and return only valid JSON.",
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text

    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Parse strict JSON from the response."""
        try:
            # Clean up potential markdown code blocks
            clean_text = response_text.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_text)
        except json.JSONDecodeError:
            logger.warning("Failed to parse LLM JSON response")
            return {"steps": []}

    def _extract_local(
        self, user_input: str, ai_response: str, context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Local rule-based reasoning extraction without needing an API key.
        Less sophisticated than LLM extraction but provides basic enrichment.
        """
        import re

        steps = []
        step_id = 0

        # Pattern-based extraction of reasoning indicators
        reasoning_patterns = [
            # Code-related reasoning
            (
                r"(?:let me|I'll|I will)\s+(fix|update|modify|create|implement|add|remove|change)\s+(.+?)(?:\.|$)",
                "code_modification",
            ),
            (
                r"(?:the\s+)?(?:error|issue|bug|problem)\s+(?:is|was|seems to be)\s+(.+?)(?:\.|$)",
                "problem_identification",
            ),
            (
                r"(?:this|that|it)\s+(?:works|works because|is because)\s+(.+?)(?:\.|$)",
                "explanation",
            ),
            # Decision patterns
            (
                r"(?:we should|I recommend|the best approach)\s+(.+?)(?:\.|$)",
                "recommendation",
            ),
            (
                r"(?:instead of|rather than)\s+(.+?),?\s*(?:we|I)\s+(.+?)(?:\.|$)",
                "alternative_choice",
            ),
            # Analysis patterns
            (r"(?:looking at|examining|analyzing)\s+(.+?)(?:,|\.)", "analysis"),
            (r"(?:found|discovered|noticed)\s+(.+?)(?:\.|$)", "discovery"),
            # Causal reasoning
            (r"(?:because|since|due to)\s+(.+?)(?:,|\.)", "causal_reasoning"),
            (r"(?:therefore|thus|so|hence)\s+(.+?)(?:\.|$)", "conclusion"),
        ]

        combined_text = f"{user_input}\n{ai_response}".lower()

        for pattern, step_type in reasoning_patterns:
            matches = re.findall(pattern, combined_text, re.IGNORECASE)
            for match in matches[:2]:  # Limit to 2 matches per pattern
                step_id += 1
                description = match if isinstance(match, str) else " ".join(match)
                description = description.strip()[:200]  # Truncate long descriptions

                if len(description) > 10:  # Only meaningful extractions
                    steps.append(
                        {
                            "step_id": step_id,
                            "operation": "local_extraction",
                            "reasoning": description,
                            "evidence": f"Pattern match: {step_type}",
                            "conclusion": f"Identified {step_type.replace('_', ' ')}",
                            "confidence": 0.7,  # Lower confidence for rule-based
                            "weight": 0.6,
                            "step_type": step_type,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                    )

        # Detect code blocks and technical content
        code_blocks = re.findall(r"```[\s\S]*?```", ai_response)
        if code_blocks:
            step_id += 1
            steps.append(
                {
                    "step_id": step_id,
                    "operation": "local_extraction",
                    "reasoning": f"Code implementation with {len(code_blocks)} code block(s)",
                    "evidence": f"Detected {len(code_blocks)} code snippets",
                    "conclusion": "Technical implementation provided",
                    "confidence": 0.85,
                    "weight": 0.8,
                    "step_type": "code_implementation",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )

        # Calculate significance score
        base_score = 0.4  # Lower base for rule-based
        if len(steps) > 0:
            base_score += min(len(steps) * 0.08, 0.4)  # Cap boost at +0.4
        if code_blocks:
            base_score += 0.1  # Bonus for code

        logger.debug(f"🧠 Local extraction: {len(steps)} steps, score={base_score:.2f}")

        return {
            "steps": steps[:10],  # Limit to 10 steps
            "suggested_score": round(min(base_score, 0.95), 2),
            "extraction_method": "local_rule_based",
        }
