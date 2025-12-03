"""
Reasoning Analysis API Endpoints for UATP Capsule Engine

This module provides API endpoints for reasoning trace validation,
analysis, and comparison capabilities.
"""

import asyncio
import hashlib
import logging
from typing import Any, Dict, List, Optional, Union

from .cache import cache_ai_response, get_cached_ai_response
from .schemas import ErrorResponse
from src.capsule_schema import Capsule
from pydantic import BaseModel, Field
from quart import Blueprint, Response, jsonify
from quart_schema import validate_request, validate_response
from src.reasoning.analyzer import ReasoningAnalyzer
from src.reasoning.trace import ReasoningStep, ReasoningTrace, StepType
from src.reasoning.validator import ReasoningValidator

# --- Schema Definitions ---


class ValidateReasoningRequest(BaseModel):
    """Schema for the /reasoning/validate request."""

    capsule_id: Optional[str] = None
    reasoning_trace: Optional[Dict[str, Any]] = None


class ValidationIssue(BaseModel):
    """Schema for a single validation issue."""

    message: str
    severity: str


class ValidationResultModel(BaseModel):
    """Schema for the validation result."""

    is_valid: bool
    score: float
    issues: List[ValidationIssue]
    suggestions: List[str]


class ValidateReasoningResponse(BaseModel):
    """Schema for the /reasoning/validate response."""

    capsule_id: Optional[str] = None
    validation_result: ValidationResultModel


class AnalyzeReasoningRequest(BaseModel):
    """Schema for the /reasoning/analyze request."""

    capsule_id: Optional[str] = None
    reasoning_trace: Optional[Dict[str, Any]] = None


class FlowAnalysisModel(BaseModel):
    """Schema for the reasoning flow analysis."""

    confidence_trend: str
    early_step_placement: str
    late_step_placement: str
    flow_quality: str


class AnalysisResultModel(BaseModel):
    """Schema for the analysis result."""

    step_count: int
    type_distribution: Dict[str, float]
    average_confidence: float
    has_conclusion: bool
    patterns: List[str]
    flow: FlowAnalysisModel


class AnalyzeReasoningResponse(BaseModel):
    """Schema for the /reasoning/analyze response."""

    capsule_id: Optional[str] = None
    analysis_result: AnalysisResultModel


class CompareReasoningRequest(BaseModel):
    """Schema for the /reasoning/compare request."""

    capsule_id_1: Optional[str] = None
    reasoning_trace_1: Optional[Dict[str, Any]] = None
    capsule_id_2: Optional[str] = None
    reasoning_trace_2: Optional[Dict[str, Any]] = None


class UniquePatternsModel(BaseModel):
    """Schema for unique patterns in comparison."""

    trace1: List[str]
    trace2: List[str]


class ComparisonResultModel(BaseModel):
    """Schema for the comparison result."""

    step_count_diff: int
    confidence_diff: float
    type_distribution_diffs: Dict[str, float]
    common_patterns: List[str]
    unique_patterns: UniquePatternsModel


class CompareReasoningResponse(BaseModel):
    """Schema for the /reasoning/compare response."""

    comparison_result: ComparisonResultModel


class BatchAnalysisRequest(BaseModel):
    """Schema for the /reasoning/analyze-batch request."""

    capsule_ids: Optional[List[str]] = None
    reasoning_traces: Optional[List[Dict[str, Any]]] = None


class StatisticsModel(BaseModel):
    """Schema for statistical measures."""

    min: float
    max: float
    mean: float
    median: Optional[float] = None


class CommonPatternModel(BaseModel):
    """Schema for a common pattern."""

    pattern: str
    frequency: float


class BatchAnalysisResultModel(BaseModel):
    """Schema for the batch analysis result."""

    trace_count: int
    step_count_statistics: StatisticsModel
    confidence_statistics: StatisticsModel
    aggregate_type_distribution: Dict[str, float]
    common_patterns: List[CommonPatternModel]


class BatchAnalysisResponse(BaseModel):
    """Schema for the /reasoning/analyze-batch response."""

    batch_size: int
    analysis: BatchAnalysisResultModel


class GenerateReasoningRequest(BaseModel):
    """Schema for the /reasoning/generate request."""

    prompt: str
    agent_id: str
    capsule_type: str
    parent_capsule: Optional[str] = None
    model: Optional[str] = Field(
        None, description="The specific AI model to use for generation."
    )


# Configure logging
logger = logging.getLogger(__name__)


async def _get_capsule_by_id(engine, capsule_id):
    """Helper function to retrieve a capsule by its ID from the engine."""
    async for capsule in engine.load_chain():
        if capsule.capsule_id == capsule_id:
            return capsule
    return None


def create_reasoning_blueprint(
    engine_getter, require_api_key, decompress_capsule_func=None
):
    """Create and return the reasoning API blueprint with injected dependencies."""
    reasoning_bp = Blueprint("reasoning", __name__, url_prefix="/reasoning")

    def _parse_reasoning_trace(trace_data: Dict[str, Any]) -> ReasoningTrace:
        """Parse a dictionary into a ReasoningTrace object."""
        if not isinstance(trace_data, dict) or "steps" not in trace_data:
            raise ValueError(
                "Invalid reasoning_trace format. Expected a dict with 'steps' key."
            )

        steps = []
        for step_data in trace_data.get("steps", []):
            if "step_type" in step_data and isinstance(step_data["step_type"], str):
                try:
                    step_data["step_type"] = StepType[step_data["step_type"].upper()]
                except KeyError:
                    raise ValueError(f"Invalid step_type: {step_data['step_type']}")
            steps.append(ReasoningStep(**step_data))
        return ReasoningTrace(steps=steps)

    @reasoning_bp.route("/validate", methods=["POST"])
    @require_api_key(["read"])
    @validate_request(ValidateReasoningRequest)
    @validate_response(ValidateReasoningResponse, 200)
    @validate_response(ErrorResponse, (400, 404, 500))
    async def validate_reasoning(
        data: ValidateReasoningRequest,
    ) -> Union[ValidateReasoningResponse, Response]:
        """Validate a reasoning trace for logical consistency, structure, and quality."""
        engine = engine_getter()
        try:
            trace = None
            if data.capsule_id:
                capsule = await _get_capsule_by_id(engine, data.capsule_id)
                if not capsule:
                    return (
                        jsonify(
                            ErrorResponse(
                                error=f"Capsule with ID {data.capsule_id} not found"
                            ).model_dump()
                        ),
                        404,
                    )
                trace = capsule.get_reasoning_trace_as_structured()
            elif data.reasoning_trace:
                trace = _parse_reasoning_trace(data.reasoning_trace)
            else:
                return (
                    jsonify(
                        ErrorResponse(
                            error="Either capsule_id or reasoning_trace must be provided."
                        ).model_dump()
                    ),
                    400,
                )

            if not trace:
                return (
                    jsonify(
                        ErrorResponse(
                            error="Could not find a valid trace."
                        ).model_dump()
                    ),
                    400,
                )

            validator = ReasoningValidator(trace)
            result = validator.validate()

            response_model = ValidateReasoningResponse(
                capsule_id=data.capsule_id,
                validation_result=result,
            )
            return jsonify(response_model.model_dump()), 200
        except (ValueError, TypeError) as e:
            return jsonify(ErrorResponse(error=str(e)).model_dump()), 400
        except Exception as e:
            logger.error(f"Error validating reasoning: {e}", exc_info=True)
            return (
                jsonify(
                    ErrorResponse(
                        error="An unexpected error occurred during validation.",
                        details=str(e),
                    ).model_dump()
                ),
                500,
            )

    @reasoning_bp.route("/analyze", methods=["POST"])
    @require_api_key(["read"])
    @validate_request(AnalyzeReasoningRequest)
    @validate_response(AnalyzeReasoningResponse, 200)
    @validate_response(ErrorResponse, (400, 404, 500))
    async def analyze_reasoning(
        data: AnalyzeReasoningRequest,
    ) -> Union[AnalyzeReasoningResponse, Response]:
        """Analyze a reasoning trace to extract patterns, metrics, and insights."""
        engine = engine_getter()
        try:
            trace = None
            if data.capsule_id:
                capsule = await _get_capsule_by_id(engine, data.capsule_id)
                if not capsule:
                    return (
                        jsonify(
                            ErrorResponse(
                                error=f"Capsule with ID {data.capsule_id} not found"
                            ).model_dump()
                        ),
                        404,
                    )
                trace = capsule.get_reasoning_trace_as_structured()
            elif data.reasoning_trace:
                trace = _parse_reasoning_trace(data.reasoning_trace)
            else:
                return (
                    jsonify(
                        ErrorResponse(
                            error="Either capsule_id or reasoning_trace must be provided"
                        ).model_dump()
                    ),
                    400,
                )

            if not trace:
                return (
                    jsonify(
                        ErrorResponse(
                            error="No valid trace found for analysis."
                        ).model_dump()
                    ),
                    400,
                )

            analyzer = ReasoningAnalyzer(trace)
            analysis = analyzer.analyze()
            response_model = AnalyzeReasoningResponse(
                capsule_id=data.capsule_id, analysis_result=analysis
            )
            return jsonify(response_model.model_dump()), 200
        except (ValueError, TypeError) as e:
            return jsonify(ErrorResponse(error=str(e)).model_dump()), 400
        except Exception as e:
            logger.error(f"Error analyzing reasoning: {e}", exc_info=True)
            return (
                jsonify(
                    ErrorResponse(
                        error="An unexpected error occurred during analysis.",
                        details=str(e),
                    ).model_dump()
                ),
                500,
            )

    @reasoning_bp.route("/compare", methods=["POST"])
    @require_api_key(["read"])
    @validate_request(CompareReasoningRequest)
    @validate_response(CompareReasoningResponse, 200)
    @validate_response(ErrorResponse, (400, 404, 500))
    async def compare_reasoning(
        data: CompareReasoningRequest,
    ) -> Union[CompareReasoningResponse, Response]:
        """Compare two reasoning traces to identify differences and similarities."""
        engine = engine_getter()

        async def _get_trace(capsule_id, reasoning_trace_data):
            if capsule_id:
                capsule = await _get_capsule_by_id(engine, capsule_id)
                if not capsule:
                    raise FileNotFoundError(f"Capsule with ID {capsule_id} not found")
                return capsule.get_reasoning_trace_as_structured()
            elif reasoning_trace_data:
                return _parse_reasoning_trace(reasoning_trace_data)
            raise ValueError("Either capsule_id or reasoning_trace must be provided")

        try:
            if not (
                (data.capsule_id_1 or data.reasoning_trace_1)
                and (data.capsule_id_2 or data.reasoning_trace_2)
            ):
                return (
                    jsonify(
                        ErrorResponse(
                            error="Both traces must be provided for comparison."
                        ).model_dump()
                    ),
                    400,
                )

            trace1 = await _get_trace(data.capsule_id_1, data.reasoning_trace_1)
            trace2 = await _get_trace(data.capsule_id_2, data.reasoning_trace_2)

            comparison_result = ReasoningAnalyzer.compare_traces(trace1, trace2)
            response_model = CompareReasoningResponse(
                comparison_result=comparison_result
            )
            return jsonify(response_model.model_dump()), 200
        except FileNotFoundError as e:
            return jsonify(ErrorResponse(error=str(e)).model_dump()), 404
        except (ValueError, TypeError) as e:
            return jsonify(ErrorResponse(error=str(e)).model_dump()), 400
        except Exception as e:
            logger.error(f"Error comparing reasoning: {e}", exc_info=True)
            return (
                jsonify(
                    ErrorResponse(
                        error="An unexpected error occurred during comparison.",
                        details=str(e),
                    ).model_dump()
                ),
                500,
            )

    @reasoning_bp.route("/analyze-batch", methods=["POST"])
    @require_api_key(["read"])
    @validate_request(BatchAnalysisRequest)
    @validate_response(BatchAnalysisResponse, 200)
    @validate_response(ErrorResponse, (400, 500))
    async def analyze_batch(
        data: BatchAnalysisRequest,
    ) -> Union[BatchAnalysisResponse, Response]:
        """Analyze a batch of reasoning traces for aggregate statistics and patterns."""
        engine = engine_getter()
        try:
            if not data.capsule_ids and not data.reasoning_traces:
                return (
                    jsonify(
                        ErrorResponse(
                            error="Either capsule_ids or reasoning_traces must be provided"
                        ).model_dump()
                    ),
                    400,
                )

            traces = []
            if data.capsule_ids:
                capsules = await asyncio.gather(
                    *[_get_capsule_by_id(engine, cid) for cid in data.capsule_ids]
                )
                for capsule in capsules:
                    if capsule:
                        traces.append(capsule.get_reasoning_trace_as_structured())

            if data.reasoning_traces:
                for reasoning_data in data.reasoning_traces:
                    traces.append(_parse_reasoning_trace(reasoning_data))

            if not traces:
                return (
                    jsonify(
                        ErrorResponse(
                            error="No valid traces found for analysis."
                        ).model_dump()
                    ),
                    400,
                )

            analysis_result = ReasoningAnalyzer.analyze_multiple_traces(traces)
            if "error" in analysis_result:
                return (
                    jsonify(ErrorResponse(error=analysis_result["error"]).model_dump()),
                    400,
                )

            response_model = BatchAnalysisResponse(
                batch_size=len(traces),
                analysis=BatchAnalysisResultModel(**analysis_result),
            )
            return jsonify(response_model.model_dump()), 200
        except (ValueError, TypeError) as e:
            return jsonify(ErrorResponse(error=str(e)).model_dump()), 400
        except Exception as e:
            logger.error(f"Error analyzing batch reasoning: {e}", exc_info=True)
            return (
                jsonify(
                    ErrorResponse(
                        error="An unexpected error occurred during batch analysis.",
                        details=str(e),
                    ).model_dump()
                ),
                500,
            )

    @reasoning_bp.route("/generate", methods=["POST"])
    @require_api_key(["write"])
    @validate_request(GenerateReasoningRequest)
    # Removed @validate_response decorators because this route returns a manually constructed Response
    # which cannot be validated by the decorator
    async def generate_reasoning_capsule(
        data: GenerateReasoningRequest,
    ) -> Union[Capsule, Response]:
        """Generate a new capsule with an AI-generated reasoning trace based on a prompt."""
        engine = engine_getter()
        try:
            if not engine.openai_client:
                logger.warning(
                    "OpenAI client not available. Cannot generate reasoning."
                )
                return (
                    jsonify(
                        ErrorResponse(
                            error="AI reasoning generation is not configured on the server."
                        ).model_dump()
                    ),
                    503,
                )

            model_to_use = data.model or engine.get_default_ai_model()
            key_string = f"{data.prompt}:{data.agent_id}:{data.capsule_type}:{data.parent_capsule}:{model_to_use}"
            prompt_hash = hashlib.sha256(key_string.encode()).hexdigest()

            cached_response = await get_cached_ai_response(prompt_hash)
            if cached_response:
                logger.info(f"AI response cache hit for hash: {prompt_hash}")
                cached_capsule = Capsule.model_validate(cached_response)
                return jsonify(cached_capsule.model_dump()), 201

            logger.info(
                f"AI response cache miss for hash: {prompt_hash}. Generating new capsule."
            )
            capsule = await engine.create_capsule_from_prompt_async(
                prompt=data.prompt,
                capsule_type=data.capsule_type,
                agent_id=data.agent_id,
                parent_capsule=data.parent_capsule,
                model=data.model,
            )

            if capsule:
                await cache_ai_response(prompt_hash, capsule.model_dump())
                logger.info(f"Cached new AI response for hash: {prompt_hash}")

            return jsonify(capsule.model_dump()), 201
        except Exception as e:
            logger.error(f"Error generating reasoning capsule: {e}", exc_info=True)
            return (
                jsonify(
                    ErrorResponse(
                        error="An unexpected error occurred while generating the capsule.",
                        details=str(e),
                    ).model_dump()
                ),
                500,
            )

    return reasoning_bp
