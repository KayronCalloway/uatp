"""
Enhanced Context Extraction for Live Capture
Extracts rich contextual metadata from conversations to understand WHY reasoning happened
"""

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class EnhancedContext:
    """Rich context metadata extracted from conversation."""

    # User context
    user_goal: Optional[str] = None
    prior_context: Optional[str] = None
    user_expertise: Optional[str] = None  # novice, intermediate, expert

    # Problem context
    problem_domain: Optional[str] = None  # backend-api, frontend-ui, database, etc.
    problem_type: Optional[str] = None  # bug-fix, feature, architecture, optimization
    constraints: Dict[str, Any] = None
    success_criteria: Optional[str] = None

    # Environmental context
    conversation_depth: int = 0
    code_changes_made: bool = False
    files_involved: List[str] = None
    tools_used: List[str] = None

    # Outcome expectations
    expected_outcome: Optional[str] = None
    risks_identified: List[str] = None

    def __post_init__(self):
        if self.constraints is None:
            self.constraints = {}
        if self.files_involved is None:
            self.files_involved = []
        if self.tools_used is None:
            self.tools_used = []
        if self.risks_identified is None:
            self.risks_identified = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            k: v
            for k, v in self.__dict__.items()
            if v is not None and v != [] and v != {}
        }


class EnhancedContextExtractor:
    """Extracts rich context from conversation sessions."""

    # Goal detection patterns
    GOAL_PATTERNS = {
        "learn": ["how do i", "how to", "how can i", "teach me", "explain"],
        "debug": ["fix", "bug", "error", "issue", "problem", "broken", "not working"],
        "optimize": ["optimize", "performance", "faster", "slow", "improve speed"],
        "architecture": [
            "should i",
            "recommend",
            "best practice",
            "design",
            "architecture",
        ],
        "implement": ["create", "build", "implement", "add", "make"],
        "understand": ["what is", "why does", "understand", "explain why"],
    }

    # Domain detection patterns
    DOMAIN_PATTERNS = {
        "frontend-ui": [
            "frontend",
            "ui",
            "react",
            "vue",
            "angular",
            "component",
            "css",
            "html",
        ],
        "backend-api": [
            "backend",
            "api",
            "server",
            "endpoint",
            "route",
            "fastapi",
            "flask",
        ],
        "database": [
            "database",
            "sql",
            "postgres",
            "mongodb",
            "query",
            "table",
            "schema",
        ],
        "devops": [
            "deploy",
            "docker",
            "kubernetes",
            "ci/cd",
            "pipeline",
            "infrastructure",
        ],
        "testing": ["test", "pytest", "unittest", "coverage", "mock"],
        "security": [
            "security",
            "auth",
            "authentication",
            "authorization",
            "encryption",
        ],
    }

    # Problem type patterns
    PROBLEM_TYPE_PATTERNS = {
        "bug-fix": ["fix", "bug", "error", "issue", "broken"],
        "feature": ["add", "create", "implement", "new feature"],
        "refactor": ["refactor", "clean up", "reorganize", "improve code"],
        "optimization": ["optimize", "performance", "speed up", "faster"],
        "architecture": ["design", "architecture", "structure", "organize"],
        "documentation": ["document", "docs", "readme", "comment"],
    }

    # Constraint patterns
    CONSTRAINT_PATTERNS = {
        "time_sensitive": ["urgent", "asap", "quickly", "right now", "immediately"],
        "backwards_compatible": [
            "backwards compatible",
            "breaking change",
            "compatibility",
        ],
        "production_system": ["production", "live", "prod", "in production"],
        "no_dependencies": ["no dependencies", "no external", "self-contained"],
        "simple_solution": ["simple", "minimal", "straightforward", "easy"],
    }

    # Technical term indicators (for expertise estimation)
    TECHNICAL_TERMS = [
        "async",
        "await",
        "promise",
        "callback",
        "closure",
        "decorator",
        "orm",
        "sql",
        "nosql",
        "acid",
        "transaction",
        "index",
        "rest",
        "graphql",
        "websocket",
        "http",
        "api",
        "container",
        "microservice",
        "serverless",
        "lambda",
        "redux",
        "state management",
        "lifecycle",
        "hooks",
        "algorithm",
        "complexity",
        "optimization",
        "cache",
    ]

    @classmethod
    def extract(cls, session: Any, messages: List[Any]) -> EnhancedContext:
        """
        Extract enhanced context from a conversation session.

        Args:
            session: ConversationSession object
            messages: List of ConversationMessage objects

        Returns:
            EnhancedContext with extracted metadata
        """
        context = EnhancedContext()

        if not messages:
            return context

        # Analyze first user message for primary intent
        first_user_msg = next((msg for msg in messages if msg.role == "user"), None)
        if first_user_msg:
            content = first_user_msg.content.lower()

            # Extract user goal
            context.user_goal = cls._extract_user_goal(content)

            # Extract problem domain
            context.problem_domain = cls._extract_domain(content)

            # Extract problem type
            context.problem_type = cls._extract_problem_type(content)

            # Estimate user expertise
            context.user_expertise = cls._estimate_expertise(
                first_user_msg.content, messages
            )

            # Extract success criteria
            context.success_criteria = cls._extract_success_criteria(messages)

        # Analyze all messages for environmental context
        context.conversation_depth = len(messages)
        context.code_changes_made = any("```" in msg.content for msg in messages)

        # Extract files involved
        context.files_involved = cls._extract_files(messages)

        # Extract tools used (from tool use patterns)
        context.tools_used = cls._extract_tools(messages)

        # Extract constraints
        all_content = " ".join(msg.content.lower() for msg in messages)
        context.constraints = cls._extract_constraints(all_content)

        # Extract expected outcome and risks
        context.expected_outcome = cls._extract_expected_outcome(messages)
        context.risks_identified = cls._extract_risks(messages)

        # Extract prior context from session topics
        if hasattr(session, "topics") and session.topics:
            context.prior_context = ", ".join(session.topics[:3])

        return context

    @classmethod
    def _extract_user_goal(cls, content: str) -> Optional[str]:
        """Extract primary user goal from content."""
        for goal, patterns in cls.GOAL_PATTERNS.items():
            if any(pattern in content for pattern in patterns):
                return goal.replace("_", " ").title()
        return None

    @classmethod
    def _extract_domain(cls, content: str) -> Optional[str]:
        """Extract problem domain from content."""
        matches = []
        for domain, patterns in cls.DOMAIN_PATTERNS.items():
            score = sum(1 for pattern in patterns if pattern in content)
            if score > 0:
                matches.append((domain, score))

        if matches:
            # Return domain with highest score
            return max(matches, key=lambda x: x[1])[0]
        return None

    @classmethod
    def _extract_problem_type(cls, content: str) -> Optional[str]:
        """Extract problem type from content."""
        for prob_type, patterns in cls.PROBLEM_TYPE_PATTERNS.items():
            if any(pattern in content for pattern in patterns):
                return prob_type
        return None

    @classmethod
    def _estimate_expertise(cls, first_message: str, all_messages: List[Any]) -> str:
        """Estimate user expertise level."""
        content = first_message.lower()

        # Count technical terms
        tech_term_count = sum(1 for term in cls.TECHNICAL_TERMS if term in content)

        # Check message length and detail
        message_length = len(first_message)

        # Check for code in user messages
        has_code = any(
            msg.role == "user" and "```" in msg.content for msg in all_messages
        )

        # Scoring
        score = 0
        if message_length > 300:
            score += 1
        if tech_term_count >= 3:
            score += 2
        elif tech_term_count >= 1:
            score += 1
        if has_code:
            score += 1

        # Classify
        if score >= 4:
            return "expert"
        elif score >= 2:
            return "intermediate"
        else:
            return "novice"

    @classmethod
    def _extract_success_criteria(cls, messages: List[Any]) -> Optional[str]:
        """Extract success criteria from messages."""
        success_indicators = ["should", "need to", "must", "has to", "expected to"]

        for msg in messages:
            if msg.role == "user":
                content = msg.content
                # Look for sentences with success indicators
                sentences = re.split(r"[.!?]", content)
                for sentence in sentences:
                    lower_sentence = sentence.lower()
                    if any(
                        indicator in lower_sentence for indicator in success_indicators
                    ):
                        # Check if it mentions completion/success
                        if any(
                            word in lower_sentence
                            for word in [
                                "work",
                                "pass",
                                "succeed",
                                "complete",
                                "finish",
                            ]
                        ):
                            return sentence.strip()
        return None

    @classmethod
    def _extract_files(cls, messages: List[Any]) -> List[str]:
        """Extract file paths mentioned in messages."""
        files = set()
        file_pattern = re.compile(
            r"[a-zA-Z_][a-zA-Z0-9_/\-]*\.(py|ts|tsx|js|jsx|sql|md|json|yaml|yml|txt)"
        )

        for msg in messages:
            matches = file_pattern.findall(msg.content)
            files.update(matches)

        return sorted(list(files))[:10]  # Limit to 10 files

    @classmethod
    def _extract_tools(cls, messages: List[Any]) -> List[str]:
        """Extract tools/commands mentioned."""
        tools = set()
        tool_patterns = [
            "git ",
            "npm ",
            "pip ",
            "docker ",
            "pytest",
            "curl ",
            "psql",
            "redis",
            "kubectl",
            "terraform",
            "ansible",
        ]

        for msg in messages:
            content = msg.content.lower()
            for tool in tool_patterns:
                if tool in content:
                    tools.add(tool.strip())

        return sorted(list(tools))

    @classmethod
    def _extract_constraints(cls, content: str) -> Dict[str, bool]:
        """Extract constraints from content."""
        constraints = {}
        for constraint, patterns in cls.CONSTRAINT_PATTERNS.items():
            if any(pattern in content for pattern in patterns):
                constraints[constraint] = True
        return constraints

    @classmethod
    def _extract_expected_outcome(cls, messages: List[Any]) -> Optional[str]:
        """Extract expected outcome from conversation."""
        outcome_indicators = ["should result in", "will", "expected", "goal is"]

        for msg in messages:
            if msg.role == "user":
                content = msg.content
                for indicator in outcome_indicators:
                    if indicator in content.lower():
                        # Extract the sentence with the outcome
                        sentences = re.split(r"[.!?]", content)
                        for sentence in sentences:
                            if indicator in sentence.lower():
                                return sentence.strip()
        return None

    @classmethod
    def _extract_risks(cls, messages: List[Any]) -> List[str]:
        """Extract identified risks from conversation."""
        risks = []
        risk_indicators = [
            "risk",
            "concern",
            "worried",
            "might break",
            "could fail",
            "careful",
        ]

        for msg in messages:
            content = msg.content.lower()
            for indicator in risk_indicators:
                if indicator in content:
                    # Extract context around the risk
                    sentences = re.split(r"[.!?]", msg.content)
                    for sentence in sentences:
                        if indicator in sentence.lower():
                            risks.append(sentence.strip())
                            break

        return risks[:5]  # Limit to 5 risks


# Example usage
if __name__ == "__main__":
    print("[OK] Enhanced Context Extractor Ready")
    print("\nCapabilities:")
    print("  - User goal inference")
    print("  - Problem domain/type classification")
    print("  - Constraint detection")
    print("  - Success criteria extraction")
    print("  - Expertise level estimation")
    print("  - File and tool tracking")
    print("  - Risk identification")
