#!/usr/bin/env python3
"""
Base Hook for Live Capture Integrations
========================================

Abstract base class for all platform-specific capture hooks.
Eliminates code duplication across OpenAI, Cursor, Windsurf, Anthropic, etc.

This module provides common functionality for:
- Session management
- Metadata enhancement
- Interaction capture
- Error handling and logging
- Automatic user detection

Platform-specific hooks only need to implement:
- Platform-specific metadata
- Platform-specific initialization parameters
"""

import logging
import os
import subprocess
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.live_capture.real_time_capsule_generator import capture_live_interaction

logger = logging.getLogger(__name__)

# Optional rich capture integration (graceful degradation)
try:
    from src.live_capture.rich_capture_integration import RichCaptureEnhancer

    _RICH_CAPTURE_AVAILABLE = True
except ImportError:
    RichCaptureEnhancer = None  # type: ignore
    _RICH_CAPTURE_AVAILABLE = False
    logger.info("Rich capture integration not available - using basic capture")

# Feedback loop integration flag
_FEEDBACK_LOOP_ENABLED = False  # Disabled - feedback module not implemented


@dataclass
class ConversationMessage:
    """Represents a single message in a conversation."""

    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime
    message_id: str
    session_id: str
    token_count: Optional[int] = None
    model_info: Optional[str] = None

    # RL signal fields - capture implicit feedback about response quality
    signal_type: str = (
        "neutral"  # correction|requery|refinement|acceptance|abandonment|neutral
    )
    references_previous: bool = False  # Whether message references previous context
    sentiment_delta: float = 0.0  # -1.0 to 1.0 change from previous message


@dataclass
class ConversationSession:
    """Represents a complete conversation session."""

    session_id: str
    user_id: str
    start_time: datetime
    platform: str = "unknown"
    end_time: Optional[datetime] = None
    messages: List[ConversationMessage] = None
    significance_score: float = 0.0
    total_tokens: int = 0
    topics: List[str] = None
    capsule_created: bool = False

    def __post_init__(self):
        if self.messages is None:
            self.messages = []
        if self.topics is None:
            self.topics = []


class BaseHook(ABC):
    """
    Abstract base class for platform capture hooks.

    Provides common functionality:
    - Session ID generation
    - Platform detection
    - Standardized capture flow
    - Error handling
    - Logging

    Subclasses must implement:
    - get_platform_specific_metadata(): Platform-specific metadata dict
    - get_platform_emoji(): Emoji for logging (e.g., "" for OpenAI)
    """

    # Valid platform enum
    VALID_PLATFORMS = [
        "cursor",
        "claude-code",
        "openai",
        "anthropic",
        "windsurf",
        "antigravity",
        "custom",
        "legacy_unknown",
    ]

    def __init__(
        self,
        platform: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        use_rich_capture: bool = True,
    ):
        """
        Initialize base hook.

        Args:
            platform: Platform name (e.g., "openai", "cursor", "anthropic")
            user_id: User identifier (auto-detected if not provided)
            session_id: Optional custom session ID (auto-generated if not provided)
            use_rich_capture: Enable rich metadata capture (default: True)
        """
        # Detect/validate platform
        self.platform, self.is_platform_hint = self._detect_platform(platform)
        self.user_id = user_id or self._detect_user()
        self.session_id = session_id or f"{self.platform}_session_{int(time.time())}"
        self.use_rich_capture = use_rich_capture

        # Track session for rich capture
        self._interaction_count = 0
        self._session_start_time = datetime.now(timezone.utc)

        # Log initialization
        emoji = self.get_platform_emoji()
        logger.info(f"{emoji} {self.platform.title()} Live Capture initialized")
        logger.info(f"   User ID: {self.user_id}")
        logger.info(f"   Session ID: {self.session_id}")
        logger.info(f"   Platform: {self.platform} (detected)")
        logger.info(f"   Rich Capture: {'enabled' if use_rich_capture else 'disabled'}")

        # Allow subclasses to add custom initialization logging
        self._log_platform_specific_init()

    def _detect_user(self) -> str:
        """
        Automatically detect user identifier from environment.

        Detection strategy:
        1. Check environment variables (USER, USERNAME)
        2. Check git config (user.name)
        3. Fall back to system login name
        4. Default to "unknown_user" if all else fails

        Returns:
            User identifier string
        """
        # Check environment variables
        user = os.getenv("USER") or os.getenv("USERNAME")
        if user and user != "unknown":
            logger.debug(f"User detected from environment: {user}")
            return user

        # Check git config
        try:
            result = subprocess.run(
                ["git", "config", "user.name"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if result.returncode == 0 and result.stdout.strip():
                git_user = result.stdout.strip()
                logger.debug(f"User detected from git config: {git_user}")
                return git_user
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            logger.debug(f"Git config check failed: {e}")

        # Fall back to system login
        try:
            login_user = os.getlogin()
            if login_user:
                logger.debug(f"User detected from system login: {login_user}")
                return login_user
        except Exception as e:
            logger.debug(f"System login check failed: {e}")

        # Final fallback
        logger.warning("Could not detect user, using 'unknown_user'")
        return "unknown_user"

    def _detect_platform(self, provided_platform: str) -> tuple[str, bool]:
        """
        Detect and validate platform identifier.

        Detection strategy:
        1. If provided platform is valid and not 'unknown', use it
        2. Check environment variables for platform indicators
        3. Check process name/parent process
        4. Check class attributes from subclass
        5. Fall back to 'custom' (NOT 'unknown')

        Args:
            provided_platform: Platform name provided to constructor

        Returns:
            Tuple of (Validated platform name from VALID_PLATFORMS, is_hint boolean)
        """
        # If provided platform is valid and not 'unknown', use it
        if (
            provided_platform
            and provided_platform in self.VALID_PLATFORMS
            and provided_platform != "unknown"
        ):
            logger.debug(f"Using provided platform: {provided_platform}")
            return provided_platform, False

        # Check environment variables
        platform_env_vars = {
            "CURSOR_SESSION": "cursor",
            "CURSOR_IDE": "cursor",
            "WINDSURF_SESSION": "windsurf",
            "WINDSURF_IDE": "windsurf",
            "CLAUDE_CODE_SESSION": "claude-code",
            "ANTHROPIC_SESSION": "anthropic",
            "OPENAI_SESSION": "openai",
        }

        for env_var, platform_name in platform_env_vars.items():
            if os.getenv(env_var):
                logger.debug(
                    f"Platform detected from env var {env_var}: {platform_name}"
                )
                return platform_name, False

        # Check process name (This is a WEAK heuristic, so we flag it as a hint)
        try:
            import psutil

            current_process = psutil.Process()
            parent = current_process.parent()

            if parent:
                parent_name = parent.name().lower()
                logger.debug(f"Parent process name: {parent_name}")

                # Map process names to platforms
                process_mappings = {
                    "cursor": "cursor",
                    "code": "claude-code",  # VS Code / Claude Code
                    "windsurf": "windsurf",
                    "python": None,  # Skip Python - too generic
                }

                for process_keyword, platform_name in process_mappings.items():
                    if platform_name and process_keyword in parent_name:
                        logger.debug(
                            f"Platform detected from process name hint: {platform_name}"
                        )
                        return platform_name, True

        except ImportError:
            logger.debug("psutil not available for process detection")
        except Exception as e:
            logger.debug(f"Process detection failed: {e}")

        # Check if subclass has platform_name attribute
        if hasattr(self, "platform_name"):
            detected = self.platform_name
            if detected in self.VALID_PLATFORMS:
                logger.debug(f"Platform detected from class attribute: {detected}")
                return detected, False

        # If provided platform was 'unknown', use 'legacy_unknown' for backfill tracking
        if provided_platform == "unknown":
            logger.debug("Marking unknown platform as 'legacy_unknown'")
            return "legacy_unknown", False

        # Final fallback: 'custom' (not 'unknown')
        logger.info("Could not detect platform, using 'custom'")
        return "custom", False

    @abstractmethod
    def get_platform_specific_metadata(self, **kwargs) -> Dict[str, Any]:
        """
        Get platform-specific metadata.

        Subclasses must implement this to provide platform-specific
        metadata fields (e.g., API version, workspace path, etc.).

        Args:
            **kwargs: Platform-specific parameters

        Returns:
            Dict of platform-specific metadata
        """
        pass

    @abstractmethod
    def get_platform_emoji(self) -> str:
        """
        Get platform emoji for logging.

        Returns:
            Emoji string (e.g., "" for OpenAI, "" for Cursor)
        """
        pass

    def _log_platform_specific_init(self) -> None:  # noqa: B027
        """
        Optional: Log platform-specific initialization info.

        Subclasses can override to add custom logging.
        Default implementation does nothing.
        """
        pass

    async def capture_interaction(
        self,
        user_input: str,
        assistant_response: str,
        model: str,
        interaction_type: str = "general",
        **platform_kwargs,
    ) -> Optional[str]:
        """
        Capture an interaction and create capsule if significant.

        This is the main capture method used by all platforms.
        Common logic handled here, platform-specific metadata from subclass.

        Args:
            user_input: User's message
            assistant_response: AI's response
            model: Model used (e.g., "gpt-4", "claude-3.5-sonnet")
            interaction_type: Type of interaction
            **platform_kwargs: Platform-specific parameters

        Returns:
            Capsule ID if created, None if not significant
        """
        try:
            # AUTO-OUTCOME: Process user_input as potential follow-up to previous response
            if _FEEDBACK_LOOP_ENABLED and user_input:
                try:
                    follow_up_result = await self.process_user_follow_up(user_input)
                    if follow_up_result.get("outcome_inferred"):
                        logger.info(
                            f" Auto-outcome from follow-up: {follow_up_result.get('inferred_outcome')}"
                        )
                except Exception as e:
                    logger.debug(f"Follow-up processing skipped: {e}")

            # Get platform-specific metadata from subclass
            platform_metadata = self.get_platform_specific_metadata(**platform_kwargs)

            # Build complete metadata
            metadata = {
                "interaction_type": interaction_type,
                "model": model,
                **platform_metadata,
                **platform_kwargs,  # Include any additional kwargs
            }

            # Use agent_hint for unverified platform provenance (e.g. process name heuristics)
            if getattr(self, "is_platform_hint", False):
                metadata["platform"] = "unknown"
                metadata["agent_hint"] = self.platform
            else:
                metadata["platform"] = self.platform

            # Choose capture path based on rich_capture flag
            if self.use_rich_capture:
                capsule_id = await self._capture_with_rich_metadata(
                    user_input=user_input,
                    assistant_response=assistant_response,
                    model=model,
                    metadata=metadata,
                    **platform_kwargs,
                )
            else:
                # Fallback to standard capture
                capsule_id = await capture_live_interaction(
                    session_id=self.session_id,
                    user_message=user_input,
                    ai_response=assistant_response,
                    user_id=self.user_id,
                    platform=self.platform,
                    model=model,
                    metadata=metadata,
                )

            # Log success
            if capsule_id:
                emoji = self.get_platform_emoji()
                logger.info(
                    f"{emoji} {self.platform.title()} interaction encapsulated: {capsule_id}"
                )
                logger.info(f"   Model: {model}")
                logger.info(f"   Type: {interaction_type}")
                if self.use_rich_capture:
                    logger.info(
                        "   Enrichment: confidence + uncertainty + critical path"
                    )

                # Allow subclass to add custom success logging
                self._log_platform_specific_success(capsule_id, **platform_kwargs)

                # Wire into feedback loop for outcome tracking
                if _FEEDBACK_LOOP_ENABLED:
                    await self._register_with_feedback_loop(
                        capsule_id=capsule_id,
                        response_text=assistant_response,
                        model=model,
                        interaction_type=interaction_type,
                    )

            return capsule_id

        except Exception as e:
            logger.error(
                f"[ERROR] {self.platform.title()} interaction capture failed: {e}"
            )
            return None

    async def _capture_with_rich_metadata(
        self,
        user_input: str,
        assistant_response: str,
        model: str,
        metadata: Dict[str, Any],
        **platform_kwargs,
    ) -> Optional[str]:
        """
        Capture interaction with rich metadata using RichCaptureEnhancer.

        This method converts the interaction into a ConversationSession format
        and uses RichCaptureEnhancer to create a capsule with:
        - Confidence explanations with factor breakdown
        - Uncertainty quantification (epistemic + aleatoric + Bayesian)
        - Critical path analysis
        - Court-admissible enrichment
        - Improvement recommendations
        - FULL CONTEXT PRESERVATION (system prompts, conversation history)

        Args:
            user_input: User's message
            assistant_response: AI's response
            model: Model used
            metadata: Complete metadata dict
            **platform_kwargs: Platform-specific parameters

        Returns:
            Capsule ID if created, None otherwise
        """
        try:
            # Increment interaction count
            self._interaction_count += 1
            current_time = datetime.now(timezone.utc)

            # Extract token counts if available
            usage_info = platform_kwargs.get("usage_info", {})
            user_tokens = usage_info.get("prompt_tokens", len(user_input.split()))
            assistant_tokens = usage_info.get(
                "completion_tokens", len(assistant_response.split())
            )

            # FULL CONTEXT PRESERVATION (Context Amnesia fix)
            # Extract conversation_context and system_prompt from kwargs
            conversation_context = platform_kwargs.get("conversation_context")
            system_prompt = platform_kwargs.get("system_prompt")

            # Build messages list - include full conversation history if available
            messages = []

            # Add system prompt as first message if present
            if system_prompt:
                messages.append(
                    ConversationMessage(
                        role="system",
                        content=system_prompt,
                        timestamp=current_time,
                        message_id=f"{self.session_id}_msg_{self._interaction_count}_system",
                        session_id=self.session_id,
                        token_count=len(system_prompt.split()),
                        model_info=None,
                    )
                )

            # Add full conversation history if available
            if conversation_context:
                for i, msg in enumerate(conversation_context):
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    if role != "system":  # System already added above
                        messages.append(
                            ConversationMessage(
                                role=role,
                                content=content,
                                timestamp=current_time,
                                message_id=f"{self.session_id}_msg_{self._interaction_count}_ctx{i}",
                                session_id=self.session_id,
                                token_count=len(content.split()),
                                model_info=model if role == "assistant" else None,
                            )
                        )
            else:
                # Fallback: just the current interaction
                messages.append(
                    ConversationMessage(
                        role="user",
                        content=user_input,
                        timestamp=current_time,
                        message_id=f"{self.session_id}_msg_{self._interaction_count}_user",
                        session_id=self.session_id,
                        token_count=user_tokens,
                        model_info=None,
                    )
                )

            # Always add the current assistant response
            messages.append(
                ConversationMessage(
                    role="assistant",
                    content=assistant_response,
                    timestamp=current_time,
                    message_id=f"{self.session_id}_msg_{self._interaction_count}_assistant",
                    session_id=self.session_id,
                    token_count=assistant_tokens,
                    model_info=model,
                )
            )

            # Extract topics from interaction
            topics = self._extract_topics_from_interaction(
                user_input, assistant_response, metadata
            )

            # Calculate significance score
            significance_score = self._calculate_significance_score(
                user_input, assistant_response, metadata
            )

            # Calculate total tokens including context
            total_tokens = sum(m.token_count or 0 for m in messages)

            # Create conversation session
            session = ConversationSession(
                session_id=self.session_id,
                user_id=self.user_id,
                start_time=self._session_start_time,
                platform=self.platform,
                end_time=current_time,
                messages=messages,
                significance_score=significance_score,
                total_tokens=total_tokens,
                topics=topics,
                capsule_created=False,
            )

            # FULL CONTEXT PRESERVATION: Build prompt_context for capsule payload
            # This ensures we never lose the RAG/system context that was shown to the LLM
            prompt_context = {
                "has_system_prompt": system_prompt is not None,
                "system_prompt_chars": len(system_prompt) if system_prompt else 0,
                "has_conversation_history": conversation_context is not None,
                "conversation_history_count": len(conversation_context)
                if conversation_context
                else 0,
                "total_messages_captured": len(messages),
                "total_context_chars": sum(len(m.content) for m in messages),
            }

            # Store prompt_context in metadata for capsule enrichment
            metadata["prompt_context"] = prompt_context
            if system_prompt:
                metadata["system_prompt"] = system_prompt
            if conversation_context:
                metadata["conversation_context"] = conversation_context

            # Use RichCaptureEnhancer to create capsule with rich metadata
            if not _RICH_CAPTURE_AVAILABLE or RichCaptureEnhancer is None:
                raise ImportError("RichCaptureEnhancer not available")

            logger.info(
                f"Creating rich capsule with enhanced metadata for {self.platform}..."
            )
            capsule_data = (
                RichCaptureEnhancer.create_capsule_from_session_with_rich_metadata(
                    session=session,
                    user_id=self.user_id,
                )
            )

            # Store capsule using the CapsuleCreator
            from src.filters.capsule_creator import get_capsule_creator

            get_capsule_creator()

            # Create capsule through the creator (which handles storage)
            capsule_id = capsule_data["capsule_id"]

            # Store the rich capsule data
            await self._store_rich_capsule(capsule_data)

            # --- Inject enrichments that RichCaptureEnhancer doesn't produce ---

            # Economics: token usage and cost data from platform_kwargs
            usage_data = platform_kwargs.get("usage_info") or {}
            if usage_data:
                input_tok = usage_data.get("prompt_tokens", 0) or usage_data.get(
                    "input_tokens", 0
                )
                output_tok = usage_data.get("completion_tokens", 0) or usage_data.get(
                    "output_tokens", 0
                )
                cache_read = usage_data.get("cache_read_input_tokens", 0)
                cache_write = usage_data.get("cache_creation_input_tokens", 0)
                total_input = input_tok + cache_read
                capsule_data["payload"]["economics"] = {
                    "input_tokens": input_tok,
                    "output_tokens": output_tok,
                    "cache_read_tokens": cache_read,
                    "cache_write_tokens": cache_write,
                    "total_tokens": input_tok + output_tok + cache_read,
                    "cache_hit_rate": round(cache_read / max(1, total_input), 4),
                    "model": model,
                    "billing_provider": metadata.get("platform", self.platform),
                }

            # Extended thinking: if the platform provides raw chain-of-thought
            thinking = platform_kwargs.get("thinking") or platform_kwargs.get(
                "reasoning"
            )
            if thinking:
                capsule_data["payload"]["extended_thinking"] = {
                    "turns": [
                        {
                            "thinking": thinking[:10000],
                            "thinking_length": len(thinking),
                            "response_length": len(assistant_response),
                            "had_tool_calls": False,
                        }
                    ],
                    "total_thinking_chars": len(thinking),
                    "total_response_chars": len(assistant_response),
                    "thinking_to_response_ratio": round(
                        len(thinking) / max(1, len(assistant_response)), 2
                    ),
                    "turns_with_thinking": 1,
                    "turns_total": 1,
                }

            # Tool call graph: if the platform provides structured tool calls
            tool_calls = platform_kwargs.get("tool_calls")
            if tool_calls and isinstance(tool_calls, list):
                from collections import Counter

                tool_counts = Counter(
                    t.get("name") or t.get("tool") for t in tool_calls
                )
                capsule_data["payload"]["tool_call_graph"] = {
                    "invocations": tool_calls,
                    "tool_frequency": dict(tool_counts.most_common()),
                    "total_tool_calls": len(tool_calls),
                    "unique_tools": len(tool_counts),
                }

            # Ollama-specific: eval_count, eval_duration, total_duration
            eval_count = metadata.get("eval_count") or platform_kwargs.get("eval_count")
            eval_duration = metadata.get("eval_duration") or platform_kwargs.get(
                "eval_duration"
            )
            total_duration = metadata.get("total_duration") or platform_kwargs.get(
                "total_duration"
            )
            if eval_count or eval_duration:
                econ = capsule_data["payload"].setdefault("economics", {})
                if eval_count:
                    econ["eval_tokens"] = eval_count
                if eval_duration:
                    econ["eval_duration_ns"] = eval_duration
                    econ["tokens_per_second"] = (
                        round((eval_count or 0) / (eval_duration / 1e9), 1)
                        if eval_duration and eval_count
                        else None
                    )
                if total_duration:
                    econ["total_duration_ns"] = total_duration

            logger.info(f"Rich capsule created: {capsule_id}")
            logger.info(
                f"   Confidence: {capsule_data['payload'].get('overall_confidence', 'N/A')}"
            )
            logger.info(
                f"   Reasoning steps: {len(capsule_data['payload'].get('reasoning_steps', []))}"
            )

            return capsule_id

        except Exception as e:
            logger.error(f"Rich capture failed, falling back to standard capture: {e}")
            # Fallback to standard capture on error
            return await capture_live_interaction(
                session_id=self.session_id,
                user_message=user_input,
                ai_response=assistant_response,
                user_id=self.user_id,
                platform=self.platform,
                model=model,
                metadata=metadata,
            )

    def _extract_topics_from_interaction(
        self, user_input: str, assistant_response: str, metadata: Dict[str, Any]
    ) -> List[str]:
        """Extract topics from interaction content."""
        topics = []
        content = (user_input + " " + assistant_response).lower()

        # Technical topics
        tech_keywords = {
            "python": "Python Programming",
            "javascript": "JavaScript Development",
            "typescript": "TypeScript Development",
            "react": "React Framework",
            "api": "API Development",
            "database": "Database Design",
            "algorithm": "Algorithms",
            "machine learning": "Machine Learning",
            "ai": "Artificial Intelligence",
            "security": "Security",
            "authentication": "Authentication",
            "testing": "Testing",
            "debugging": "Debugging",
        }

        for keyword, topic in tech_keywords.items():
            if keyword in content:
                topics.append(topic)

        # Add interaction type as topic
        interaction_type = metadata.get("interaction_type", "general")
        if interaction_type != "general":
            topics.append(interaction_type.replace("_", " ").title())

        return topics[:5]  # Limit to top 5 topics

    def _calculate_significance_score(
        self, user_input: str, assistant_response: str, metadata: Dict[str, Any]
    ) -> float:
        """Calculate significance score for the interaction."""
        score = 0.5  # Base score

        # Length factors
        if len(user_input) > 100:
            score += 0.1
        if len(assistant_response) > 200:
            score += 0.1

        # Code presence
        if "```" in assistant_response or "def " in assistant_response:
            score += 0.15

        # Complexity indicators
        complexity_keywords = [
            "algorithm",
            "implement",
            "architecture",
            "design",
            "optimize",
            "debug",
            "analyze",
            "system",
        ]
        content_lower = (user_input + " " + assistant_response).lower()
        for keyword in complexity_keywords:
            if keyword in content_lower:
                score += 0.05

        return min(score, 1.0)

    async def _store_rich_capsule(self, capsule_data: Dict[str, Any]) -> None:
        """Store rich capsule to database."""
        try:
            # Try to store in PostgreSQL if available
            import json
            from datetime import datetime

            try:
                import asyncpg

                from src.core.config import DATABASE_URL

                if "postgresql" in DATABASE_URL:
                    conn = await asyncpg.connect(
                        DATABASE_URL.replace("postgresql://", "postgresql://").replace(
                            "postgresql+asyncpg://", "postgresql://"
                        )
                    )

                    # Insert capsule
                    await conn.execute(
                        """
                        INSERT INTO capsules (capsule_id, capsule_type, version, timestamp, status, verification, payload)
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                        ON CONFLICT (capsule_id) DO NOTHING
                    """,
                        capsule_data["capsule_id"],
                        capsule_data["type"],
                        capsule_data["version"],
                        datetime.fromisoformat(
                            capsule_data["timestamp"].replace("Z", "+00:00")
                        ),
                        capsule_data["status"],
                        json.dumps(capsule_data["verification"]),
                        json.dumps(capsule_data["payload"]),
                    )

                    await conn.close()
                    logger.info(
                        f"Stored rich capsule to PostgreSQL: {capsule_data['capsule_id']}"
                    )
                else:
                    logger.warning(
                        "PostgreSQL not configured, capsule data prepared but not persisted"
                    )
            except Exception as db_error:
                logger.warning(
                    f"PostgreSQL storage failed: {db_error}, capsule data prepared"
                )

        except Exception as e:
            logger.error(f"Failed to store rich capsule: {e}")

    def _log_platform_specific_success(self, capsule_id: str, **kwargs) -> None:  # noqa: B027
        """
        Optional: Log platform-specific success info.

        Subclasses can override to add custom logging after successful capture.
        Default implementation does nothing.

        Args:
            capsule_id: ID of created capsule
            **kwargs: Platform-specific parameters
        """
        pass

    async def _register_with_feedback_loop(
        self,
        capsule_id: str,
        response_text: str,
        model: str,
        interaction_type: str,
    ) -> None:
        """
        Register capsule with feedback loop for outcome tracking.

        This enables:
        - Automatic outcome inference from follow-up messages
        - Calibration updates when outcomes are known
        - Routing uncertain cases to human review

        Args:
            capsule_id: ID of the created capsule
            response_text: AI's response text
            model: Model used
            interaction_type: Type of interaction
        """
        try:
            from src.feedback import get_feedback_loop

            feedback_loop = get_feedback_loop()

            # Calculate a rough confidence based on response characteristics
            # In production, this would come from the capsule's actual confidence
            confidence = self._estimate_response_confidence(response_text)

            # Determine domain from interaction type
            domain = self._map_interaction_to_domain(interaction_type)

            # Register with feedback loop
            await feedback_loop.on_capsule_created(
                capsule_id=capsule_id,
                response_text=response_text[:2000],  # Truncate for efficiency
                confidence=confidence,
                user_id=self.user_id,
                domain=domain,
                conversation_id=self.session_id,
                request_immediate_feedback=False,  # Don't interrupt flow by default
            )

            logger.debug(f"Capsule {capsule_id} registered with feedback loop")

        except Exception as e:
            # Don't fail capture if feedback loop has issues
            logger.warning(f"Feedback loop registration failed: {e}")

    def _estimate_response_confidence(self, response_text: str) -> float:
        """
        Estimate confidence for a response based on text characteristics.

        This is a fallback when actual confidence isn't available.
        Real capsules should have proper confidence from the analysis.

        Args:
            response_text: The AI's response

        Returns:
            Estimated confidence (0.0 to 1.0)
        """
        confidence = 0.5  # Base confidence

        # Longer, more detailed responses tend to be more confident
        if len(response_text) > 500:
            confidence += 0.1
        if len(response_text) > 1000:
            confidence += 0.1

        # Code blocks suggest concrete solutions
        if "```" in response_text:
            confidence += 0.15

        # Hedging language reduces confidence
        hedging = ["might", "perhaps", "maybe", "possibly", "I think", "not sure"]
        for hedge in hedging:
            if hedge.lower() in response_text.lower():
                confidence -= 0.05

        # Certainty language increases confidence
        certainty = ["definitely", "certainly", "absolutely", "exactly"]
        for cert in certainty:
            if cert.lower() in response_text.lower():
                confidence += 0.05

        return max(0.1, min(0.95, confidence))

    def _map_interaction_to_domain(self, interaction_type: str) -> str:
        """Map interaction type to calibration domain."""
        domain_map = {
            "code_generation": "coding",
            "code_review": "coding",
            "debugging": "coding",
            "explanation": "explanation",
            "question_answer": "qa",
            "general": "general",
        }
        return domain_map.get(interaction_type, "general")

    async def process_user_follow_up(self, message: str) -> Dict[str, Any]:
        """
        Process a user's follow-up message for outcome inference.

        Call this when the user sends another message after receiving
        an AI response. The feedback loop will analyze the message
        to infer whether the previous response was helpful.

        Args:
            message: User's follow-up message

        Returns:
            Dict with inference results
        """
        try:
            from src.feedback import get_feedback_loop

            feedback_loop = get_feedback_loop()
            result = await feedback_loop.on_follow_up_message(
                message=message,
                user_id=self.user_id,
                conversation_id=self.session_id,
            )
            return result

        except Exception as e:
            logger.warning(f"Follow-up processing failed: {e}")
            return {"status": "error", "message": str(e)}

    def get_session_stats(self) -> Dict[str, Any]:
        """
        Get statistics for the current session.

        Returns:
            Dict with session information
        """
        return {
            "platform": self.platform,
            "user_id": self.user_id,
            "session_id": self.session_id,
        }


class SimplePlatformHook(BaseHook):
    """
    Simple implementation of BaseHook for quick platform integration.

    Use this for simple platforms that don't need custom behavior.
    Just provide platform name, emoji, and optional metadata.

    Example:
        hook = SimplePlatformHook(
            platform="my_platform",
            user_id="user123",
            emoji="",
            metadata_provider=lambda **kwargs: {"custom_field": kwargs.get("field")}
        )
    """

    def __init__(
        self,
        platform: str,
        user_id: str,
        emoji: str = "",
        metadata_provider: Optional[callable] = None,
        **kwargs,
    ):
        self.emoji = emoji
        self.metadata_provider = metadata_provider or (lambda **kw: {})
        super().__init__(platform, user_id, **kwargs)

    def get_platform_emoji(self) -> str:
        return self.emoji

    def get_platform_specific_metadata(self, **kwargs) -> Dict[str, Any]:
        return self.metadata_provider(**kwargs)
