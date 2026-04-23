"""
UATP MCP Proof Attachment
=========================

Formats proof references for MCP tool results.

MCP content is typed: TextContent, ImageContent, EmbeddedResource.
There is no generic metadata field on result blocks.

Strategy:
1. Append a TextContent block with a compact, human-readable proof URI
2. Return an EmbeddedResource pointing to uatp://capsules/{id} when the client
   supports MCP resources (machine-readable, queryable)
3. Keep the original result blocks untouched

This gives both human readability and machine actionability without
breaking clients that don't understand UATP.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class ProofAttachment:
    """
    Attaches proof references to MCP tool results.
    """

    @staticmethod
    def attach_proof(
        original_result: Any,
        capsule_id: str,
        base_url: str = "https://uatp.io/c",
    ) -> dict[str, Any]:
        """
        Attach proof metadata to a tool result.

        Returns a dict with:
        - original: the original result
        - proof_url: human-readable link
        - capsule_id: machine-reference
        - resource_uri: MCP resource URI (if client supports it)
        """
        return {
            "original": original_result,
            "proof_url": f"{base_url}/{capsule_id}",
            "capsule_id": capsule_id,
            "resource_uri": f"uatp://capsules/{capsule_id}",
        }

    @staticmethod
    def text_proof_block(capsule_id: str, base_url: str = "https://uatp.io/c") -> str:
        """
        Return a compact text block to append to MCP TextContent results.
        """
        return f"\n\n[UATP Certified] Proof: {base_url}/{capsule_id}"

    @staticmethod
    def refusal_text_block(refusal_id: str, reason: str) -> str:
        """
        Return a text block for a refused tool call.
        """
        return (
            f"\n\n[UATP Policy Blocked]\n"
            f"Reason: {reason}\n"
            f"Refusal proof: https://uatp.io/c/{refusal_id}"
        )
