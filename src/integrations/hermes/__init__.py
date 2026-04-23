"""
UATP Capture Plugin for Hermes
==============================

Captures Hermes sessions as signed UATP capsules on session end.
Reads messages from state.db, runs implicit feedback detection via
SignalDetector, signs with Ed25519 (UATPCryptoV7), writes to uatp_dev.db.
"""

import logging
import threading

logger = logging.getLogger(__name__)


def register(ctx):
    """Called by Hermes plugin system on startup."""
    ctx.register_hook("on_session_end", _on_session_end)
    logger.info("uatp-capture: registered on_session_end hook")


def _on_session_end(**kwargs):
    """Fire-and-forget capsule creation in a background thread."""
    session_id = kwargs.get("session_id")
    model = kwargs.get("model")
    platform = kwargs.get("platform", "cli")

    if not session_id:
        return

    # Don't block the exit path — capture in background
    t = threading.Thread(
        target=_capture_session_safe,
        args=(session_id, model, platform),
        daemon=True,
        name="uatp-capture",
    )
    t.start()
    # Give it a moment so it doesn't get killed on process exit
    t.join(timeout=30)
    if t.is_alive():
        logger.warning(
            "uatp-capture: capture thread still running after 30s, continuing without blocking"
        )


def _capture_session_safe(session_id: str, model: str, platform: str):
    """Wrapper that eats exceptions so a bad capture never breaks Hermes."""
    try:
        import sys
        from pathlib import Path

        plugin_dir = str(Path(__file__).parent)
        if plugin_dir not in sys.path:
            sys.path.insert(0, plugin_dir)
        from hermes_capture import capture_session

        result = capture_session(session_id, model=model, platform=platform)
        if result:
            logger.info(
                "uatp-capture: created capsule %s for session %s",
                result.get("capsule_id", "?"),
                session_id,
            )
        else:
            logger.debug("uatp-capture: session %s below capture threshold", session_id)
    except Exception:
        logger.exception("uatp-capture: failed to capture session %s", session_id)
