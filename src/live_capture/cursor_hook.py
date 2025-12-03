#!/usr/bin/env python3
"""
Cursor Live Capture Integration
==============================

This module provides integration with Cursor AI IDE for live conversation
capture and automatic capsule generation.
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from live_capture.real_time_capsule_generator import capture_live_interaction

logger = logging.getLogger(__name__)


class CursorLiveCapture:
    """Live capture integration for Cursor AI IDE."""

    def __init__(
        self, user_id: str = "cursor_user", workspace_path: Optional[str] = None
    ):
        self.platform = "cursor"
        self.user_id = user_id
        self.workspace_path = workspace_path or os.getcwd()
        self.session_id = f"cursor_session_{int(time.time())}"

        logger.info(f"🎯 Cursor Live Capture initialized")
        logger.info(f"   User ID: {user_id}")
        logger.info(f"   Session ID: {self.session_id}")
        logger.info(f"   Workspace: {self.workspace_path}")

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

        Args:
            user_input: User's message to Cursor
            assistant_response: Cursor's response
            interaction_type: Type of interaction (code_assistance, debugging, etc.)
            file_context: Information about the current file being edited
            project_context: Information about the project structure
            cursor_model: Model used by Cursor
            **kwargs: Additional metadata

        Returns:
            Capsule ID if created, None if not significant
        """

        try:
            # Enhance metadata with Cursor-specific context
            metadata = {
                "interaction_type": interaction_type,
                "model": cursor_model,
                "file_context": file_context,
                "project_context": project_context,
                "workspace_path": self.workspace_path,
                "cursor_version": "1.0",
                "ide_provider": "cursor",
                **kwargs,
            }

            # Capture the interaction
            capsule_id = await capture_live_interaction(
                session_id=self.session_id,
                user_message=user_input,
                ai_response=assistant_response,
                user_id=self.user_id,
                platform=self.platform,
                model=cursor_model,
                metadata=metadata,
            )

            if capsule_id:
                logger.info(f"🎯 Cursor interaction encapsulated: {capsule_id}")
                logger.info(f"   Model: {cursor_model}")
                logger.info(f"   Type: {interaction_type}")
                if file_context:
                    logger.info(f"   File: {file_context.get('filename', 'unknown')}")

            return capsule_id

        except Exception as e:
            logger.error(f"❌ Cursor interaction capture failed: {e}")
            return None

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

        logger.info("✅ Cursor integration helper initialized")

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

    print("🎯 Testing Cursor Live Capture Integration")
    print("=" * 50)

    # Test code assistance
    print("\n💻 Testing code assistance capture...")
    code_assistance_capsule = await capture_cursor_interaction(
        user_input="Help me write a Python function to validate email addresses using regex",
        assistant_response="""I'll help you create a Python function to validate email addresses using regex. Here's a comprehensive solution:

```python
import re
from typing import bool

def validate_email(email: str) -> bool:
    \"\"\"
    Validate an email address using regex pattern.
    
    Args:
        email (str): Email address to validate
        
    Returns:
        bool: True if email is valid, False otherwise
    \"\"\"
    # RFC 5322 compliant email regex pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'
    
    return bool(re.match(pattern, email))

# Example usage
if __name__ == "__main__":
    test_emails = [
        "user@example.com",
        "test.email+tag@domain.co.uk",
        "invalid.email",
        "user@",
        "@domain.com"
    ]
    
    for email in test_emails:
        is_valid = validate_email(email)
        print(f"{email}: {'Valid' if is_valid else 'Invalid'}")
```

This function uses a regex pattern that validates most common email formats while being reasonably strict.""",
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
        print(f"✅ Code assistance captured: {code_assistance_capsule}")
    else:
        print("❌ No capsule created - interaction not significant enough")

    # Test debugging session
    print("\n🐛 Testing debugging session capture...")
    debug_capsule = await capture_cursor_interaction(
        user_input="I'm getting a KeyError: 'name' in my Python code. Can you help me debug this?",
        assistant_response="""A KeyError: 'name' typically occurs when you're trying to access a dictionary key that doesn't exist. Here are common causes and solutions:

1. **Missing key in dictionary**:
   ```python
   # Problem
   user_data = {'id': 123, 'email': 'user@example.com'}
   name = user_data['name']  # KeyError: 'name'
   
   # Solution - use get() method
   name = user_data.get('name', 'Unknown')
   ```

2. **Check if key exists**:
   ```python
   if 'name' in user_data:
       name = user_data['name']
   else:
       name = 'Unknown'
   ```

3. **Use try-except block**:
   ```python
   try:
       name = user_data['name']
   except KeyError:
       name = 'Unknown'
   ```

To help you debug further, could you share the specific code where the error occurs?""",
        interaction_type="debugging",
        error_context={
            "error_type": "KeyError",
            "error_message": "KeyError: 'name'",
            "line_number": 42,
        },
        cursor_model="claude-3.5-sonnet",
        user_id="cursor_developer",
    )

    if debug_capsule:
        print(f"✅ Debugging session captured: {debug_capsule}")
    else:
        print("❌ No capsule created - interaction not significant enough")

    # Test code review
    print("\n🔍 Testing code review capture...")
    review_capsule = await capture_cursor_interaction(
        user_input="Can you review this function for potential improvements?",
        assistant_response="""I'll review your function for potential improvements:

**Strengths:**
- Clear function purpose
- Good variable naming
- Handles edge cases

**Suggestions for improvement:**

1. **Add type hints** for better code documentation
2. **Add docstring** to explain the function's purpose
3. **Consider error handling** for invalid inputs
4. **Use more descriptive variable names** if needed
5. **Add unit tests** to ensure reliability

**Performance considerations:**
- The current implementation looks efficient
- Consider using generator expressions for large datasets
- Memory usage is acceptable for typical use cases

Would you like me to show you a refactored version with these improvements?""",
        interaction_type="code_review",
        code_snippet="def process_data(items): return [x * 2 for x in items if x > 0]",
        review_type="general",
        cursor_model="claude-3.5-sonnet",
        user_id="cursor_developer",
    )

    if review_capsule:
        print(f"✅ Code review captured: {review_capsule}")
    else:
        print("❌ No capsule created - interaction not significant enough")

    print("\n✅ Cursor integration test completed!")


if __name__ == "__main__":
    asyncio.run(main())
