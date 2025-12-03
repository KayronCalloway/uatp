"""
Advanced Reasoning Chain System
Implements complex logical reasoning workflows with full attribution tracking
"""

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List

from pydantic import BaseModel, Field, validator

from ..attribution.cross_conversation_tracker import CrossConversationTracker
from ..capsules.specialized_capsules import create_specialized_capsule
from ..economic.fcde_engine import FCDEEngine
from ..engine.capsule_engine import CapsuleEngine
from ..integrations.advanced_llm_registry import AdvancedLLMRegistry

logger = logging.getLogger(__name__)


class ReasoningType(Enum):
    """Types of reasoning patterns"""

    DEDUCTIVE = "deductive"
    INDUCTIVE = "inductive"
    ABDUCTIVE = "abductive"
    ANALOGICAL = "analogical"
    CAUSAL = "causal"
    COUNTERFACTUAL = "counterfactual"
    TEMPORAL = "temporal"
    SPATIAL = "spatial"
    PROBABILISTIC = "probabilistic"
    METACOGNITIVE = "metacognitive"


class ReasoningStep(BaseModel):
    """Individual step in a reasoning chain"""

    step_id: str
    reasoning_type: ReasoningType
    input_data: Dict[str, Any]
    reasoning_process: str
    output_data: Dict[str, Any]
    confidence: float = Field(ge=0.0, le=1.0)
    dependencies: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)

    @validator("confidence")
    def validate_confidence(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
        return v


@dataclass
class ReasoningChain:
    """Complete reasoning chain with multiple steps"""

    chain_id: str
    steps: List[ReasoningStep]
    overall_confidence: float
    reasoning_graph: Dict[str, List[str]]
    conclusion: Dict[str, Any]
    attribution_data: Dict[str, Any]
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chain_id": self.chain_id,
            "steps": [step.dict() for step in self.steps],
            "overall_confidence": self.overall_confidence,
            "reasoning_graph": self.reasoning_graph,
            "conclusion": self.conclusion,
            "attribution_data": self.attribution_data,
            "metadata": self.metadata,
        }


class ReasoningStrategy(ABC):
    """Abstract base class for reasoning strategies"""

    @abstractmethod
    async def execute_reasoning(
        self, input_data: Dict[str, Any], context: Dict[str, Any]
    ) -> ReasoningStep:
        """Execute the reasoning strategy"""
        pass

    @abstractmethod
    def get_reasoning_type(self) -> ReasoningType:
        """Get the reasoning type this strategy implements"""
        pass


class DeductiveReasoningStrategy(ReasoningStrategy):
    """Deductive reasoning: from general to specific"""

    def __init__(self, llm_registry: AdvancedLLMRegistry):
        self.llm_registry = llm_registry

    async def execute_reasoning(
        self, input_data: Dict[str, Any], context: Dict[str, Any]
    ) -> ReasoningStep:
        premises = input_data.get("premises", [])
        conclusion_template = input_data.get("conclusion_template", "")

        reasoning_prompt = f"""
        Apply deductive reasoning to derive a specific conclusion from the given premises.

        Premises:
        {json.dumps(premises, indent=2)}

        Conclusion Template: {conclusion_template}

        Please:
        1. Analyze each premise for validity
        2. Apply logical rules to derive the conclusion
        3. Assess the logical validity of the inference
        4. Provide confidence in the conclusion

        Format your response as structured JSON with:
        - reasoning_process: Step-by-step logical derivation
        - conclusion: The derived conclusion
        - validity_assessment: Analysis of logical validity
        - confidence: Confidence score (0.0-1.0)
        """

        # Get best model for logical reasoning
        model_info = await self.llm_registry.get_best_model_for_capability("reasoning")
        response = await self._call_reasoning_model(model_info, reasoning_prompt)

        return ReasoningStep(
            step_id=f"deductive_{int(datetime.now().timestamp())}",
            reasoning_type=ReasoningType.DEDUCTIVE,
            input_data=input_data,
            reasoning_process=response.get("reasoning_process", ""),
            output_data=response.get("conclusion", {}),
            confidence=response.get("confidence", 0.8),
            metadata={
                "premises_count": len(premises),
                "model_used": model_info.get("model_name", "unknown"),
                "validity_assessment": response.get("validity_assessment", ""),
            },
        )

    def get_reasoning_type(self) -> ReasoningType:
        return ReasoningType.DEDUCTIVE

    async def _call_reasoning_model(
        self, model_info: Dict[str, Any], prompt: str
    ) -> Dict[str, Any]:
        """Call the reasoning model"""
        # Mock implementation - in reality, this would call the actual model
        return {
            "reasoning_process": "Applied modus ponens to derive conclusion from premises",
            "conclusion": {"derived_fact": "Conclusion derived from premises"},
            "validity_assessment": "Logically valid inference",
            "confidence": 0.9,
        }


class InductiveReasoningStrategy(ReasoningStrategy):
    """Inductive reasoning: from specific to general"""

    def __init__(self, llm_registry: AdvancedLLMRegistry):
        self.llm_registry = llm_registry

    async def execute_reasoning(
        self, input_data: Dict[str, Any], context: Dict[str, Any]
    ) -> ReasoningStep:
        observations = input_data.get("observations", [])
        pattern_type = input_data.get("pattern_type", "general")

        reasoning_prompt = f"""
        Apply inductive reasoning to identify patterns and make generalizations from specific observations.

        Observations:
        {json.dumps(observations, indent=2)}

        Pattern Type: {pattern_type}

        Please:
        1. Identify recurring patterns in the observations
        2. Assess the strength of evidence for each pattern
        3. Formulate generalizations based on the patterns
        4. Evaluate the reliability of the inductive inference

        Format your response as structured JSON.
        """

        model_info = await self.llm_registry.get_best_model_for_capability(
            "pattern_recognition"
        )
        response = await self._call_reasoning_model(model_info, reasoning_prompt)

        return ReasoningStep(
            step_id=f"inductive_{int(datetime.now().timestamp())}",
            reasoning_type=ReasoningType.INDUCTIVE,
            input_data=input_data,
            reasoning_process=response.get("reasoning_process", ""),
            output_data=response.get("generalization", {}),
            confidence=response.get("confidence", 0.7),
            metadata={
                "observations_count": len(observations),
                "patterns_identified": response.get("patterns_identified", []),
                "evidence_strength": response.get("evidence_strength", "medium"),
            },
        )

    def get_reasoning_type(self) -> ReasoningType:
        return ReasoningType.INDUCTIVE

    async def _call_reasoning_model(
        self, model_info: Dict[str, Any], prompt: str
    ) -> Dict[str, Any]:
        """Call the reasoning model"""
        return {
            "reasoning_process": "Identified recurring patterns and formulated generalizations",
            "generalization": {"general_rule": "Pattern-based generalization"},
            "patterns_identified": ["pattern1", "pattern2"],
            "evidence_strength": "strong",
            "confidence": 0.8,
        }


class AbductiveReasoningStrategy(ReasoningStrategy):
    """Abductive reasoning: inference to the best explanation"""

    def __init__(self, llm_registry: AdvancedLLMRegistry):
        self.llm_registry = llm_registry

    async def execute_reasoning(
        self, input_data: Dict[str, Any], context: Dict[str, Any]
    ) -> ReasoningStep:
        observations = input_data.get("observations", [])
        possible_explanations = input_data.get("possible_explanations", [])

        reasoning_prompt = f"""
        Apply abductive reasoning to find the best explanation for the given observations.

        Observations:
        {json.dumps(observations, indent=2)}

        Possible Explanations:
        {json.dumps(possible_explanations, indent=2)}

        Please:
        1. Evaluate each possible explanation against the observations
        2. Consider explanatory power, simplicity, and plausibility
        3. Rank explanations by their likelihood
        4. Select the best explanation with justification

        Format your response as structured JSON.
        """

        model_info = await self.llm_registry.get_best_model_for_capability(
            "explanation_generation"
        )
        response = await self._call_reasoning_model(model_info, reasoning_prompt)

        return ReasoningStep(
            step_id=f"abductive_{int(datetime.now().timestamp())}",
            reasoning_type=ReasoningType.ABDUCTIVE,
            input_data=input_data,
            reasoning_process=response.get("reasoning_process", ""),
            output_data=response.get("best_explanation", {}),
            confidence=response.get("confidence", 0.75),
            metadata={
                "explanations_evaluated": len(possible_explanations),
                "ranking": response.get("ranking", []),
                "selection_criteria": response.get("selection_criteria", []),
            },
        )

    def get_reasoning_type(self) -> ReasoningType:
        return ReasoningType.ABDUCTIVE

    async def _call_reasoning_model(
        self, model_info: Dict[str, Any], prompt: str
    ) -> Dict[str, Any]:
        """Call the reasoning model"""
        return {
            "reasoning_process": "Evaluated explanations and selected the most plausible",
            "best_explanation": {
                "explanation": "Most likely explanation based on evidence"
            },
            "ranking": ["explanation1", "explanation2", "explanation3"],
            "selection_criteria": ["explanatory_power", "simplicity", "plausibility"],
            "confidence": 0.85,
        }


class CausalReasoningStrategy(ReasoningStrategy):
    """Causal reasoning: identifying cause-effect relationships"""

    def __init__(self, llm_registry: AdvancedLLMRegistry):
        self.llm_registry = llm_registry

    async def execute_reasoning(
        self, input_data: Dict[str, Any], context: Dict[str, Any]
    ) -> ReasoningStep:
        events = input_data.get("events", [])
        temporal_sequence = input_data.get("temporal_sequence", [])

        reasoning_prompt = f"""
        Apply causal reasoning to identify cause-effect relationships in the given events.

        Events:
        {json.dumps(events, indent=2)}

        Temporal Sequence:
        {json.dumps(temporal_sequence, indent=2)}

        Please:
        1. Identify potential causal relationships
        2. Assess temporal precedence
        3. Evaluate causal strength and mechanisms
        4. Consider alternative explanations and confounding factors

        Format your response as structured JSON.
        """

        model_info = await self.llm_registry.get_best_model_for_capability(
            "causal_reasoning"
        )
        response = await self._call_reasoning_model(model_info, reasoning_prompt)

        return ReasoningStep(
            step_id=f"causal_{int(datetime.now().timestamp())}",
            reasoning_type=ReasoningType.CAUSAL,
            input_data=input_data,
            reasoning_process=response.get("reasoning_process", ""),
            output_data=response.get("causal_relationships", {}),
            confidence=response.get("confidence", 0.7),
            metadata={
                "events_analyzed": len(events),
                "causal_chains": response.get("causal_chains", []),
                "confounding_factors": response.get("confounding_factors", []),
            },
        )

    def get_reasoning_type(self) -> ReasoningType:
        return ReasoningType.CAUSAL

    async def _call_reasoning_model(
        self, model_info: Dict[str, Any], prompt: str
    ) -> Dict[str, Any]:
        """Call the reasoning model"""
        return {
            "reasoning_process": "Analyzed temporal relationships and identified causal mechanisms",
            "causal_relationships": {"primary_cause": "Event A", "effect": "Event B"},
            "causal_chains": ["A -> B -> C"],
            "confounding_factors": ["factor1", "factor2"],
            "confidence": 0.8,
        }


class AdvancedReasoningChainProcessor:
    """
    Advanced reasoning chain processor that orchestrates complex reasoning workflows
    """

    def __init__(
        self,
        capsule_engine: CapsuleEngine,
        attribution_tracker: CrossConversationTracker,
        fcde_engine: FCDEEngine,
        llm_registry: AdvancedLLMRegistry,
    ):
        self.capsule_engine = capsule_engine
        self.attribution_tracker = attribution_tracker
        self.fcde_engine = fcde_engine
        self.llm_registry = llm_registry

        # Initialize reasoning strategies
        self.strategies = {
            ReasoningType.DEDUCTIVE: DeductiveReasoningStrategy(llm_registry),
            ReasoningType.INDUCTIVE: InductiveReasoningStrategy(llm_registry),
            ReasoningType.ABDUCTIVE: AbductiveReasoningStrategy(llm_registry),
            ReasoningType.CAUSAL: CausalReasoningStrategy(llm_registry),
        }

        self.processing_stats = {
            "total_chains": 0,
            "successful_chains": 0,
            "failed_chains": 0,
            "total_steps": 0,
            "average_confidence": 0.0,
            "by_reasoning_type": {rt.value: 0 for rt in ReasoningType},
        }

    async def process_reasoning_chain(
        self, chain_definition: Dict[str, Any]
    ) -> ReasoningChain:
        """Process a complete reasoning chain"""

        chain_id = f"chain_{int(datetime.now().timestamp())}"
        start_time = datetime.now()

        try:
            self.processing_stats["total_chains"] += 1

            # Parse chain definition
            steps_definition = chain_definition.get("steps", [])
            context = chain_definition.get("context", {})

            # Execute reasoning steps
            reasoning_steps = []
            step_outputs = {}

            for step_def in steps_definition:
                step = await self._execute_reasoning_step(
                    step_def, step_outputs, context
                )
                reasoning_steps.append(step)
                step_outputs[step.step_id] = step.output_data

                # Update statistics
                self.processing_stats["total_steps"] += 1
                self.processing_stats["by_reasoning_type"][
                    step.reasoning_type.value
                ] += 1

            # Build reasoning graph
            reasoning_graph = self._build_reasoning_graph(reasoning_steps)

            # Calculate overall confidence
            overall_confidence = self._calculate_overall_confidence(reasoning_steps)

            # Generate conclusion
            conclusion = await self._generate_conclusion(reasoning_steps, context)

            # Track attribution
            attribution_data = await self._track_reasoning_attribution(
                reasoning_steps, context
            )

            # Create reasoning chain
            reasoning_chain = ReasoningChain(
                chain_id=chain_id,
                steps=reasoning_steps,
                overall_confidence=overall_confidence,
                reasoning_graph=reasoning_graph,
                conclusion=conclusion,
                attribution_data=attribution_data,
                metadata={
                    "processing_time": (datetime.now() - start_time).total_seconds(),
                    "steps_count": len(reasoning_steps),
                    "reasoning_types": list(
                        {step.reasoning_type.value for step in reasoning_steps}
                    ),
                    "timestamp": datetime.now().isoformat(),
                },
            )

            # Create and store capsule
            await self._create_reasoning_capsule(reasoning_chain)

            # Update statistics
            self.processing_stats["successful_chains"] += 1
            self.processing_stats["average_confidence"] = (
                self.processing_stats["average_confidence"]
                * (self.processing_stats["successful_chains"] - 1)
                + overall_confidence
            ) / self.processing_stats["successful_chains"]

            return reasoning_chain

        except Exception as e:
            self.processing_stats["failed_chains"] += 1
            logger.error(f"Reasoning chain processing failed: {str(e)}")
            raise

    async def _execute_reasoning_step(
        self,
        step_def: Dict[str, Any],
        step_outputs: Dict[str, Any],
        context: Dict[str, Any],
    ) -> ReasoningStep:
        """Execute a single reasoning step"""

        reasoning_type = ReasoningType(step_def["reasoning_type"])
        step_input = step_def.get("input", {})

        # Resolve dependencies
        for dep_id in step_def.get("dependencies", []):
            if dep_id in step_outputs:
                step_input[f"dependency_{dep_id}"] = step_outputs[dep_id]

        # Get and execute strategy
        strategy = self.strategies.get(reasoning_type)
        if not strategy:
            raise ValueError(
                f"No strategy available for reasoning type: {reasoning_type}"
            )

        step = await strategy.execute_reasoning(step_input, context)

        # Add dependencies to step
        step.dependencies = step_def.get("dependencies", [])

        return step

    def _build_reasoning_graph(
        self, reasoning_steps: List[ReasoningStep]
    ) -> Dict[str, List[str]]:
        """Build a graph representation of reasoning dependencies"""

        graph = {}

        for step in reasoning_steps:
            graph[step.step_id] = step.dependencies

        return graph

    def _calculate_overall_confidence(
        self, reasoning_steps: List[ReasoningStep]
    ) -> float:
        """Calculate overall confidence for the reasoning chain"""

        if not reasoning_steps:
            return 0.0

        # Use weighted average based on step dependencies
        total_weight = 0
        weighted_confidence = 0

        for step in reasoning_steps:
            # Steps with more dependencies have higher weight
            weight = 1.0 + (len(step.dependencies) * 0.2)
            total_weight += weight
            weighted_confidence += step.confidence * weight

        return weighted_confidence / total_weight if total_weight > 0 else 0.0

    async def _generate_conclusion(
        self, reasoning_steps: List[ReasoningStep], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate a conclusion from the reasoning chain"""

        # Collect all outputs
        all_outputs = []
        for step in reasoning_steps:
            all_outputs.append(
                {
                    "step_id": step.step_id,
                    "reasoning_type": step.reasoning_type.value,
                    "output": step.output_data,
                    "confidence": step.confidence,
                }
            )

        # Generate synthesis prompt
        synthesis_prompt = f"""
        Synthesize a conclusion from the following reasoning chain steps:

        {json.dumps(all_outputs, indent=2)}

        Context: {json.dumps(context, indent=2)}

        Please:
        1. Integrate insights from all reasoning steps
        2. Resolve any contradictions or inconsistencies
        3. Provide a coherent final conclusion
        4. Assess the overall strength of the reasoning chain

        Format your response as structured JSON.
        """

        # Get best model for synthesis
        model_info = await self.llm_registry.get_best_model_for_capability("synthesis")

        # Mock synthesis - in reality, this would call the actual model
        conclusion = {
            "final_conclusion": "Synthesized conclusion from reasoning chain",
            "supporting_evidence": [step.step_id for step in reasoning_steps],
            "confidence_assessment": "High confidence based on multiple reasoning approaches",
            "potential_limitations": ["limitation1", "limitation2"],
            "synthesis_method": "multi-step_integration",
        }

        return conclusion

    async def _track_reasoning_attribution(
        self, reasoning_steps: List[ReasoningStep], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Track attribution for reasoning chain processing"""

        attribution_data = {
            "session_id": context.get("session_id", "unknown"),
            "user_id": context.get("user_id", "unknown"),
            "conversation_id": context.get("conversation_id", "unknown"),
            "reasoning_contributions": [],
            "model_usage": {},
            "processing_costs": {},
            "step_weights": {},
        }

        total_processing_time = 0

        for step in reasoning_steps:
            contribution = {
                "step_id": step.step_id,
                "reasoning_type": step.reasoning_type.value,
                "confidence": step.confidence,
                "dependencies": step.dependencies,
                "model_used": step.metadata.get("model_used", "unknown"),
                "processing_time": 0.1,  # Mock processing time
            }

            attribution_data["reasoning_contributions"].append(contribution)
            total_processing_time += contribution["processing_time"]

            # Track model usage
            model = step.metadata.get("model_used", "unknown")
            if model not in attribution_data["model_usage"]:
                attribution_data["model_usage"][model] = {
                    "total_calls": 0,
                    "reasoning_types": set(),
                }

            attribution_data["model_usage"][model]["total_calls"] += 1
            attribution_data["model_usage"][model]["reasoning_types"].add(
                step.reasoning_type.value
            )

        # Convert sets to lists for JSON serialization
        for model_data in attribution_data["model_usage"].values():
            model_data["reasoning_types"] = list(model_data["reasoning_types"])

        # Calculate step weights
        for step in reasoning_steps:
            weight = (
                0.1 / total_processing_time
                if total_processing_time > 0
                else 1.0 / len(reasoning_steps)
            )
            attribution_data["step_weights"][step.step_id] = weight

        return attribution_data

    async def _create_reasoning_capsule(self, reasoning_chain: ReasoningChain):
        """Create and store a capsule for the reasoning chain"""

        capsule_data = {
            "type": "reasoning_chain",
            "chain_id": reasoning_chain.chain_id,
            "steps": [step.dict() for step in reasoning_chain.steps],
            "overall_confidence": reasoning_chain.overall_confidence,
            "reasoning_graph": reasoning_chain.reasoning_graph,
            "conclusion": reasoning_chain.conclusion,
            "attribution_data": reasoning_chain.attribution_data,
            "metadata": reasoning_chain.metadata,
            "timestamp": datetime.now().isoformat(),
        }

        # Create specialized capsule
        capsule = create_specialized_capsule(
            capsule_type="reasoning_chain",
            data=capsule_data,
            metadata={"source": "advanced_reasoning_chains"},
        )

        # Store in capsule engine
        await self.capsule_engine.store_capsule(capsule)

        return capsule

    async def create_reasoning_workflow(
        self, workflow_definition: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a complex reasoning workflow with multiple chains"""

        workflow_id = f"workflow_{int(datetime.now().timestamp())}"
        chains = []

        for chain_def in workflow_definition.get("chains", []):
            chain = await self.process_reasoning_chain(chain_def)
            chains.append(chain)

        # Create workflow summary
        workflow_summary = {
            "workflow_id": workflow_id,
            "total_chains": len(chains),
            "overall_confidence": sum(chain.overall_confidence for chain in chains)
            / len(chains),
            "chain_summaries": [
                {
                    "chain_id": chain.chain_id,
                    "steps_count": len(chain.steps),
                    "confidence": chain.overall_confidence,
                    "reasoning_types": list(
                        {step.reasoning_type.value for step in chain.steps}
                    ),
                }
                for chain in chains
            ],
            "timestamp": datetime.now().isoformat(),
        }

        return workflow_summary

    async def get_reasoning_statistics(self) -> Dict[str, Any]:
        """Get reasoning processing statistics"""

        stats = self.processing_stats.copy()

        if stats["total_chains"] > 0:
            stats["success_rate"] = stats["successful_chains"] / stats["total_chains"]
            stats["average_steps_per_chain"] = (
                stats["total_steps"] / stats["total_chains"]
            )
        else:
            stats["success_rate"] = 0.0
            stats["average_steps_per_chain"] = 0.0

        return stats

    async def get_supported_reasoning_types(self) -> List[str]:
        """Get list of supported reasoning types"""
        return [rt.value for rt in ReasoningType]
