from datetime import timedelta

from src.engine.exceptions import UATPEngineError
from quart import Blueprint, Response, current_app
from quart_rate_limiter import rate_limit
from quart_schema import validate_request

from .dependencies import get_engine, require_api_key
from .schemas import AIGenerateRequest, AIGenerateResponse, ErrorResponse

ai_bp = Blueprint("ai", __name__, url_prefix="/ai")


@ai_bp.route("/generate", methods=["POST"])
@require_api_key(["write", "ai"])
@rate_limit(30, timedelta(minutes=1))
@validate_request(AIGenerateRequest)
async def generate_ai_text(data: AIGenerateRequest) -> Response:
    """
    Generates text using the integrated OpenAI model and logs the
    interaction in a UATP capsule for attribution.
    """
    engine = get_engine()
    if not engine.openai_client:
        return ErrorResponse(error="AI features are not configured on the server."), 503

    try:
        capsule = await engine.create_capsule_from_prompt_async(
            prompt=data.prompt,
            capsule_type="ai_generation",
            model=data.model,
            temperature=data.temperature,
        )
        response_model = AIGenerateResponse(
            status="success", generated_text=capsule.output
        )
        return Response(
            response_model.model_dump_json(), mimetype="application/json", status=200
        )
    except UATPEngineError as e:
        current_app.logger.error(f"Error during AI text generation: {e}", exc_info=True)
        return ErrorResponse(error="Failed to generate AI text", details=str(e)), 400
    except Exception as e:
        error_message = f"Error during AI text generation: {e}"
        current_app.logger.error(error_message, exc_info=True)
        response_data = ErrorResponse(error=error_message, status_code=500)
        return Response(
            response_data.model_dump_json(), status=500, mimetype="application/json"
        )
