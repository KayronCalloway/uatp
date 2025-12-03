"""
Fixed Conversation significance analyzer with proper scoring for UATP system conversations.
"""

import asyncio
import json
import re
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional


async def analyze_conversation_significance(
    messages: List[Dict], context: Dict
) -> Dict:
    """
    Analyze the significance of a conversation to determine if it should be captured.
    Fixed version with proper scoring for technical conversations.

    Args:
        messages: List of conversation messages
        context: Context information about the conversation

    Returns:
        Dictionary with significance analysis results
    """

    # Check for explicit significance scores in metadata FIRST
    for msg in messages:
        metadata = msg.get("metadata", {})
        explicit_score = metadata.get("significance_score")
        if explicit_score is not None:
            try:
                explicit_score = float(explicit_score)
                if explicit_score > 0:
                    factors = [
                        f"Explicit significance score provided: {explicit_score}"
                    ]
                    reasoning_steps = [
                        {
                            "step_id": 0,
                            "operation": "explicit_significance_override",
                            "reasoning": f"Message contains explicit significance score: {explicit_score}",
                            "confidence": 1.0,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "metadata": {
                                "explicit_score": explicit_score,
                                "pattern_type": "metadata_override",
                            },
                        }
                    ]

                    return {
                        "significance_score": explicit_score,
                        "score": explicit_score,  # Both keys for compatibility
                        "should_create_capsule": explicit_score >= 0.6,
                        "confidence": 1.0,
                        "factors": factors,
                        "reasoning_steps": reasoning_steps,
                        "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
                        "analyzer_version": "fixed_2.1_metadata_aware",
                    }
            except (ValueError, TypeError):
                pass  # Continue with normal analysis

    # Initialize significance factors for normal analysis
    factors = []
    reasoning_steps = []
    base_score = 0.0

    # Extract text content from messages
    all_text = []
    user_messages = []
    ai_messages = []

    for msg in messages:
        content = msg.get("content", "")
        all_text.append(content)

        if msg.get("role") == "user":
            user_messages.append(content)
        elif msg.get("role") == "assistant":
            ai_messages.append(content)

    combined_text = " ".join(all_text)
    word_count = len(combined_text.split())

    # Factor 1: UATP System-specific patterns (HIGH VALUE)
    uatp_patterns = [
        r"\buatp\b",
        r"\buniversal\s+attribution\b",
        r"\btrust\s+protocol\b",
        r"\bcapsule\s+engine\b",
        r"\battribution\s+system\b",
        r"\bconversation\s+capture\b",
        r"\blive\s+capture\b",
        r"\bsignificance\s+score\b",
        r"\bcross.platform\b",
        r"\breal.time\s+monitoring\b",
    ]

    uatp_matches = sum(
        len(re.findall(pattern, combined_text, re.IGNORECASE))
        for pattern in uatp_patterns
    )
    if uatp_matches > 0:
        weight = min(0.4 + (uatp_matches * 0.1), 0.8)  # 0.4-0.8 for UATP content
        factors.append(f"UATP system discussion ({uatp_matches} references)")
        reasoning_steps.append(
            {
                "step_id": 1,
                "operation": "uatp_system_detection",
                "reasoning": f"UATP system discussion detected with {uatp_matches} specific references",
                "confidence": min(0.9, 0.7 + (uatp_matches * 0.05)),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metadata": {
                    "uatp_references": uatp_matches,
                    "pattern_type": "system_specific",
                },
            }
        )
        base_score += weight

    # Factor 2: Code generation detection (ENHANCED)
    code_patterns = [
        r"```[\s\S]*?```",  # Code blocks
        r"`[^`]+`",  # Inline code
        r"def\s+\w+\s*\(",  # Function definitions
        r"class\s+\w+",  # Class definitions
        r"import\s+\w+",  # Imports
        r"from\s+\w+\s+import",  # From imports
        r"<[^>]+>",  # HTML/XML tags
        r"function\s+\w+\s*\(",  # JavaScript functions
        r"async\s+def\b",  # Async functions
        r"await\s+\w+",  # Await calls
        r"\.py\b",  # Python files
        r"\.js\b",  # JavaScript files
    ]

    code_matches = sum(
        len(re.findall(pattern, combined_text, re.IGNORECASE))
        for pattern in code_patterns
    )
    if code_matches > 0:
        weight = min(0.3 + (code_matches * 0.05), 0.5)  # 0.3-0.5 for code content
        factors.append(f"Code generation detected ({code_matches} code elements)")
        reasoning_steps.append(
            {
                "step_id": 2,
                "operation": "code_detection",
                "reasoning": f"Code generation detected with {code_matches} code elements",
                "confidence": min(0.95, 0.8 + (code_matches * 0.02)),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metadata": {
                    "code_elements": code_matches,
                    "pattern_type": "programming",
                },
            }
        )
        base_score += weight

    # Factor 3: Technical problem-solving (ENHANCED)
    problem_patterns = [
        r"\bproblem\b",
        r"\bissue\b",
        r"\berror\b",
        r"\bbug\b",
        r"\bfix\b",
        r"\bsolve\b",
        r"\btroubleshoot\b",
        r"\bdebug\b",
        r"\bhelp\b",
        r"\bstuck\b",
        r"\bbroken\b",
        r"\bfailed\b",
        r"\bfailing\b",
        r"\bnot\s+working\b",
        r"\bhow\s+do\s+i\b",
        r"\bcan\s+you\s+fix\b",
        r"\bwhat\'s\s+wrong\b",
    ]

    problem_matches = sum(
        len(re.findall(pattern, combined_text, re.IGNORECASE))
        for pattern in problem_patterns
    )
    if problem_matches > 0:
        weight = min(
            0.25 + (problem_matches * 0.05), 0.4
        )  # 0.25-0.4 for problem-solving
        factors.append(
            f"Problem-solving discussion ({problem_matches} problem indicators)"
        )
        reasoning_steps.append(
            {
                "step_id": 3,
                "operation": "problem_solving_detection",
                "reasoning": f"Problem-solving discussion with {problem_matches} problem indicators",
                "confidence": min(0.9, 0.7 + (problem_matches * 0.03)),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metadata": {
                    "problem_indicators": problem_matches,
                    "pattern_type": "troubleshooting",
                },
            }
        )
        base_score += weight

    # Factor 4: Advanced technical depth (BOOSTED)
    technical_patterns = [
        r"\bapi\b",
        r"\balgorithm\b",
        r"\barchitecture\b",
        r"\bframework\b",
        r"\bdatabase\b",
        r"\boptimization\b",
        r"\bperformance\b",
        r"\bsecurity\b",
        r"\bscalability\b",
        r"\bintegration\b",
        r"\bsystem\b",
        r"\bengine\b",
        r"\bservice\b",
        r"\bmodule\b",
        r"\bcomponent\b",
        r"\bprocess\b",
        r"\btesting\b",
        r"\bmonitoring\b",
        r"\bdeployment\b",
        r"\bproduction\b",
        r"\bmicroservices\b",
        r"\bcontainerization\b",
        r"\bkubernetes\b",
        r"\bdocker\b",
        r"\bdevops\b",
        r"\bci/cd\b",
        r"\bautomation\b",
        r"\bschema\b",
        r"\bvalidation\b",
        r"\basync\b",
        r"\bconcurrency\b",
        r"\bparallel\b",
        r"\bthread\b",
        r"\bqueue\b",
        r"\bcache\b",
        r"\bmemory\b",
        r"\bcpu\b",
        r"\blatency\b",
        r"\bthroughput\b",
        r"\bload\s+balancing\b",
        r"\bfault\s+tolerance\b",
    ]

    technical_matches = sum(
        len(re.findall(pattern, combined_text, re.IGNORECASE))
        for pattern in technical_patterns
    )
    if technical_matches > 2:  # Lower threshold
        weight = min(
            0.2 + (technical_matches * 0.02), 0.4
        )  # 0.2-0.4 for technical content
        factors.append(f"High technical depth ({technical_matches} technical terms)")
        reasoning_steps.append(
            {
                "step_id": 4,
                "operation": "technical_depth_analysis",
                "reasoning": f"High technical depth with {technical_matches} technical terms",
                "confidence": min(0.95, 0.6 + (technical_matches * 0.01)),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metadata": {
                    "technical_terms": technical_matches,
                    "pattern_type": "technical_content",
                },
            }
        )
        base_score += weight

    # Factor 5: Conversation length and complexity
    if word_count > 100:
        length_weight = min(0.1 + (word_count / 1000 * 0.1), 0.2)  # 0.1-0.2 for length
        factors.append(f"Substantial conversation length ({word_count} words)")
        reasoning_steps.append(
            {
                "step_id": 5,
                "operation": "conversation_length_analysis",
                "reasoning": f"Substantial conversation with {word_count} words indicating depth",
                "confidence": min(0.8, 0.5 + (word_count / 1000 * 0.1)),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metadata": {
                    "word_count": word_count,
                    "pattern_type": "conversation_depth",
                },
            }
        )
        base_score += length_weight

    # Factor 6: Implementation and development patterns
    implementation_patterns = [
        r"\bimplement\b",
        r"\bdevelop\b",
        r"\bbuild\b",
        r"\bcreate\b",
        r"\bdesign\b",
        r"\barchitect\b",
        r"\brefactor\b",
        r"\boptimize\b",
        r"\bscale\b",
        r"\bdeploy\b",
        r"\blaunch\b",
        r"\brelease\b",
        r"\bversion\b",
        r"\bupgrade\b",
        r"\bmigrate\b",
    ]

    impl_matches = sum(
        len(re.findall(pattern, combined_text, re.IGNORECASE))
        for pattern in implementation_patterns
    )
    if impl_matches > 1:
        weight = min(
            0.15 + (impl_matches * 0.03), 0.3
        )  # 0.15-0.3 for implementation content
        factors.append(f"Implementation discussion ({impl_matches} development terms)")
        reasoning_steps.append(
            {
                "step_id": 6,
                "operation": "implementation_analysis",
                "reasoning": f"Implementation discussion with {impl_matches} development terms",
                "confidence": min(0.9, 0.6 + (impl_matches * 0.05)),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metadata": {
                    "implementation_terms": impl_matches,
                    "pattern_type": "development",
                },
            }
        )
        base_score += weight

    # Cap the maximum score at 1.0
    final_score = min(base_score, 1.0)

    # Determine if capsule should be created
    should_create_capsule = final_score >= 0.6

    # Calculate overall confidence
    confidence = min(0.95, 0.5 + (final_score * 0.4))

    return {
        "significance_score": final_score,
        "score": final_score,  # Both keys for compatibility
        "should_create_capsule": should_create_capsule,
        "confidence": confidence,
        "factors": factors,
        "reasoning_steps": reasoning_steps,
        "word_count": word_count,
        "technical_depth": technical_matches,
        "problem_solving": problem_matches,
        "code_content": code_matches,
        "uatp_relevance": uatp_matches,
        "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
        "analyzer_version": "fixed_2.1_metadata_aware",
    }
