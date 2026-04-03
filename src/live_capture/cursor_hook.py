#!/usr/bin/env python3
"""
Cursor Live Capture Integration
==============================

This module provides integration with Cursor AI IDE for live conversation
capture and automatic capsule generation.

Refactored to use BaseHook for reduced duplication.
"""

import asyncio
import logging
import os
from typing import Dict, Optional

from src.live_capture.base_hook import BaseHook

logger = logging.getLogger(__name__)


class CursorLiveCapture(BaseHook):
    """Live capture integration for Cursor AI IDE."""

    def __init__(
        self, user_id: str = "cursor_user", workspace_path: Optional[str] = None
    ):
        self.workspace_path = workspace_path or os.getcwd()
        super().__init__(platform="cursor", user_id=user_id)

    def get_platform_emoji(self) -> str:
        return ""

    def get_platform_specific_metadata(self, **kwargs) -> Dict:
        """Get Cursor-specific metadata."""
        return {
            "cursor_version": "1.0",
            "ide_provider": "cursor",
            "workspace_path": self.workspace_path,
            "file_context": kwargs.get("file_context"),
            "project_context": kwargs.get("project_context"),
        }

    def _log_platform_specific_init(self) -> None:
        """Log Cursor-specific initialization."""
        logger.info(f"   Workspace: {self.workspace_path}")

    def _log_platform_specific_success(self, capsule_id: str, **kwargs) -> None:
        """Log Cursor-specific success info."""
        file_context = kwargs.get("file_context")
        if file_context:
            logger.info(f"   File: {file_context.get('filename', 'unknown')}")

    # Convenience methods for Cursor-specific interactions

    async def capture_cursor_interaction(
        self,
        user_input: str,
        assistant_response: str,
        interaction_type: str = "code_assistance",
        file_context: Optional[Dict] = None,
        project_context: Optional[Dict] = None,
        cursor_model: str = "claude-3.5-sonnet",
        **kwargs,
    ) -> Optional[str]:
        """
        Capture a Cursor interaction and create capsule if significant.

        Thin wrapper around BaseHook.capture_interaction with Cursor-specific parameters.
        """
        return await self.capture_interaction(
            user_input=user_input,
            assistant_response=assistant_response,
            model=cursor_model,
            interaction_type=interaction_type,
            file_context=file_context,
            project_context=project_context,
            **kwargs,
        )

    async def capture_code_assistance(
        self,
        user_input: str,
        assistant_response: str,
        filename: str = None,
        language: str = None,
        line_number: int = None,
        cursor_model: str = "claude-3.5-sonnet",
        **kwargs,
    ) -> Optional[str]:
        """Capture code assistance interaction."""
        file_context = {
            "filename": filename,
            "language": language,
            "line_number": line_number,
            "workspace_path": self.workspace_path,
        }

        return await self.capture_cursor_interaction(
            user_input=user_input,
            assistant_response=assistant_response,
            interaction_type="code_assistance",
            file_context=file_context,
            cursor_model=cursor_model,
            **kwargs,
        )

    async def capture_debugging_session(
        self,
        user_input: str,
        assistant_response: str,
        error_context: Optional[Dict] = None,
        stack_trace: Optional[str] = None,
        cursor_model: str = "claude-3.5-sonnet",
        **kwargs,
    ) -> Optional[str]:
        """Capture debugging session interaction."""
        return await self.capture_cursor_interaction(
            user_input=user_input,
            assistant_response=assistant_response,
            interaction_type="debugging",
            error_context=error_context,
            stack_trace=stack_trace,
            cursor_model=cursor_model,
            **kwargs,
        )

    async def capture_code_review(
        self,
        user_input: str,
        assistant_response: str,
        code_snippet: str = None,
        review_type: str = "general",
        cursor_model: str = "claude-3.5-sonnet",
        **kwargs,
    ) -> Optional[str]:
        """Capture code review interaction."""
        return await self.capture_cursor_interaction(
            user_input=user_input,
            assistant_response=assistant_response,
            interaction_type="code_review",
            code_snippet=code_snippet,
            review_type=review_type,
            cursor_model=cursor_model,
            **kwargs,
        )

    async def capture_refactoring_suggestion(
        self,
        user_input: str,
        assistant_response: str,
        original_code: str = None,
        suggested_code: str = None,
        cursor_model: str = "claude-3.5-sonnet",
        **kwargs,
    ) -> Optional[str]:
        """Capture refactoring suggestion interaction."""
        return await self.capture_cursor_interaction(
            user_input=user_input,
            assistant_response=assistant_response,
            interaction_type="refactoring",
            original_code=original_code,
            suggested_code=suggested_code,
            cursor_model=cursor_model,
            **kwargs,
        )

    async def capture_documentation_generation(
        self,
        user_input: str,
        assistant_response: str,
        code_context: str = None,
        doc_type: str = "docstring",
        cursor_model: str = "claude-3.5-sonnet",
        **kwargs,
    ) -> Optional[str]:
        """Capture documentation generation interaction."""
        return await self.capture_cursor_interaction(
            user_input=user_input,
            assistant_response=assistant_response,
            interaction_type="documentation",
            code_context=code_context,
            doc_type=doc_type,
            cursor_model=cursor_model,
            **kwargs,
        )


# Global instance for easy access
_cursor_capture = None


def get_cursor_capture(
    user_id: str = "cursor_user", workspace_path: Optional[str] = None
) -> CursorLiveCapture:
    """Get the global Cursor capture instance."""
    global _cursor_capture
    if _cursor_capture is None:
        _cursor_capture = CursorLiveCapture(user_id, workspace_path)
    return _cursor_capture


async def capture_cursor_interaction(
    user_input: str,
    assistant_response: str,
    interaction_type: str = "code_assistance",
    file_context: Optional[Dict] = None,
    project_context: Optional[Dict] = None,
    cursor_model: str = "claude-3.5-sonnet",
    user_id: str = "cursor_user",
    workspace_path: Optional[str] = None,
    **kwargs,
) -> Optional[str]:
    """
    Convenience function to capture Cursor interactions.

    Args:
        user_input: User's message to Cursor
        assistant_response: Cursor's response
        interaction_type: Type of interaction
        file_context: Information about the current file
        project_context: Information about the project
        cursor_model: Model used by Cursor
        user_id: User identifier
        workspace_path: Path to the workspace
        **kwargs: Additional metadata

    Returns:
        Capsule ID if created, None if not significant
    """
    capture = get_cursor_capture(user_id, workspace_path)
    return await capture.capture_cursor_interaction(
        user_input=user_input,
        assistant_response=assistant_response,
        interaction_type=interaction_type,
        file_context=file_context,
        project_context=project_context,
        cursor_model=cursor_model,
        **kwargs,
    )


# Cursor IDE integration helper
class CursorIntegrationHelper:
    """Helper class for integrating with Cursor IDE."""

    def __init__(
        self,
        user_id: str = "cursor_user",
        workspace_path: Optional[str] = None,
        auto_capture: bool = True,
    ):
        self.user_id = user_id
        self.workspace_path = workspace_path or os.getcwd()
        self.auto_capture = auto_capture
        self.capture = get_cursor_capture(user_id, workspace_path)

        logger.info("[OK] Cursor integration helper initialized")

    async def on_chat_message(
        self,
        user_message: str,
        assistant_response: str,
        file_context: Optional[Dict] = None,
        **kwargs,
    ):
        """Handle chat message in Cursor."""
        if self.auto_capture:
            return await self.capture.capture_code_assistance(
                user_input=user_message,
                assistant_response=assistant_response,
                filename=file_context.get("filename") if file_context else None,
                language=file_context.get("language") if file_context else None,
                **kwargs,
            )
        return None

    async def on_code_edit(
        self,
        user_request: str,
        code_changes: str,
        file_context: Optional[Dict] = None,
        **kwargs,
    ):
        """Handle code edit in Cursor."""
        if self.auto_capture:
            return await self.capture.capture_code_assistance(
                user_input=user_request,
                assistant_response=code_changes,
                filename=file_context.get("filename") if file_context else None,
                language=file_context.get("language") if file_context else None,
                **kwargs,
            )
        return None

    async def on_debug_session(
        self,
        user_input: str,
        debug_response: str,
        error_context: Optional[Dict] = None,
        **kwargs,
    ):
        """Handle debug session in Cursor."""
        if self.auto_capture:
            return await self.capture.capture_debugging_session(
                user_input=user_input,
                assistant_response=debug_response,
                error_context=error_context,
                **kwargs,
            )
        return None


async def main():
    """Test the Cursor integration."""
    print(" Testing Cursor Live Capture Integration (with BaseHook)")
    print("=" * 50)

    # Test code assistance
    print("\n Testing code assistance capture...")
    code_assistance_capsule = await capture_cursor_interaction(
        user_input="Help me write a Python function to validate email addresses",
        assistant_response="Here's a Python function to validate email addresses using regex...",
        interaction_type="code_assistance",
        file_context={
            "filename": "email_validator.py",
            "language": "python",
            "line_number": 1,
        },
        cursor_model="claude-3.5-sonnet",
        user_id="cursor_developer",
    )

    if code_assistance_capsule:
        print(f"[OK] Code assistance captured: {code_assistance_capsule}")
    else:
        print("[ERROR] No capsule created")

    print("\n[OK] Cursor integration test completed (with BaseHook refactoring)!")


if __name__ == "__main__":
    asyncio.run(main())
