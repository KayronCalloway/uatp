import time

from aioprometheus import (
    REGISTRY,
    Counter,
    Gauge,
    Histogram,
    render,
)
from quart import Quart, Response, request

# Define application-level metrics. They are automatically registered with the global REGISTRY.
CONST_LABELS = {"app": "uatp-capsule-engine"}

REQUESTS_IN_PROGRESS = Gauge(
    "uatp_requests_in_progress",
    "Number of requests in progress.",
    const_labels=CONST_LABELS,
)

REQUESTS_TOTAL = Counter(
    "uatp_requests_total",
    "Total number of requests.",
    const_labels=CONST_LABELS,
)

REQUESTS_FAILED_TOTAL = Counter(
    "uatp_requests_failed_total",
    "Total number of failed requests (status >= 500).",
    const_labels=CONST_LABELS,
)

REQUEST_LATENCY = Histogram(
    "uatp_request_latency_seconds",
    "Request latency in seconds.",
    const_labels=CONST_LABELS,
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 10.0],
)


async def render_metrics() -> Response:
    """
    Renders the Prometheus metrics into the appropriate format.
    This endpoint is scraped by the Prometheus server.
    """
    content, http_headers = render(REGISTRY, request.headers.getlist("accept"))
    return Response(content, headers=http_headers)


def setup_metrics_hooks(app: Quart):
    """
    Sets up before_request and after_request hooks to capture metrics for every request.
    This is a clean way to instrument all endpoints without decorators.

    Args:
        app: The Quart application instance.
    """

    @app.before_request
    async def before_request_metrics():
        """Capture metrics before the request is processed."""
        request.start_time = time.time()
        labels = {"method": request.method, "endpoint": request.path}
        REQUESTS_IN_PROGRESS.inc(labels)
        REQUESTS_TOTAL.inc(labels)

    @app.after_request
    async def after_request_metrics(response: Response) -> Response:
        """Capture metrics after the request is processed."""
        latency = time.time() - request.start_time

        # Define labels for this request
        request_labels = {"method": request.method, "endpoint": request.path}
        {**request_labels, "status_code": str(response.status_code)}

        # Observe latency
        REQUEST_LATENCY.observe(request_labels, latency)

        # Decrement in-progress gauge
        REQUESTS_IN_PROGRESS.dec(request_labels)

        # Increment failure counter for 5xx responses
        if response.status_code >= 500:
            REQUESTS_FAILED_TOTAL.inc(request_labels)

        return response
