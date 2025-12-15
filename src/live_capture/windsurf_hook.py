#!/usr/bin/env python3
"""
Windsurf Live Capture Integration
=================================

This module provides integration with Windsurf IDE for live conversation
capture and automatic capsule generation.
"""

import asyncio
import logging
import os
import sys
import time
from typing import Optional

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from src.live_capture.real_time_capsule_generator import capture_live_interaction

logger = logging.getLogger(__name__)


class WindsurfLiveCapture:
    """Live capture integration for Windsurf IDE."""

    def __init__(self, user_id: str = "windsurf_user"):
        self.platform = "windsurf"
        self.user_id = user_id
        self.session_id = f"windsurf_session_{int(time.time())}"

        logger.info("🌊 Windsurf Live Capture initialized")
        logger.info(f"   User ID: {user_id}")
        logger.info(f"   Session ID: {self.session_id}")

    async def capture_windsurf_interaction(
        self,
        user_input: str,
        assistant_response: str,
        interaction_type: str = "code_assistance",
        file_context: Optional[str] = None,
        project_context: Optional[str] = None,
        language: Optional[str] = None,
        **kwargs,
    ) -> Optional[str]:
        """
        Capture a Windsurf interaction and create capsule if significant.

        Args:
            user_input: User's message to Windsurf
            assistant_response: Windsurf's response
            interaction_type: Type of interaction (code_completion, debugging, etc.)
            file_context: File being worked on
            project_context: Project context
            language: Programming language
            **kwargs: Additional metadata

        Returns:
            Capsule ID if created, None if not significant
        """

        try:
            # Enhance metadata with Windsurf-specific context
            metadata = {
                "interaction_type": interaction_type,
                "file_context": file_context,
                "project_context": project_context,
                "language": language,
                "windsurf_version": "1.0",
                "ide_platform": "windsurf",
                **kwargs,
            }

            # Capture the interaction
            capsule_id = await capture_live_interaction(
                session_id=self.session_id,
                user_message=user_input,
                ai_response=assistant_response,
                user_id=self.user_id,
                platform=self.platform,
                model="windsurf-ai",
                metadata=metadata,
            )

            if capsule_id:
                logger.info(f"🌊 Windsurf interaction encapsulated: {capsule_id}")
                logger.info(f"   Type: {interaction_type}")
                logger.info(f"   File: {file_context}")
                logger.info(f"   Language: {language}")

            return capsule_id

        except Exception as e:
            logger.error(f"❌ Windsurf interaction capture failed: {e}")
            return None

    async def capture_code_completion(
        self,
        user_input: str,
        completion: str,
        file_path: str,
        language: str = None,
        **kwargs,
    ) -> Optional[str]:
        """Capture code completion interaction."""

        return await self.capture_windsurf_interaction(
            user_input=user_input,
            assistant_response=completion,
            interaction_type="code_completion",
            file_context=file_path,
            language=language,
            **kwargs,
        )

    async def capture_debugging_session(
        self,
        user_input: str,
        debug_response: str,
        error_context: str = None,
        file_path: str = None,
        **kwargs,
    ) -> Optional[str]:
        """Capture debugging session interaction."""

        return await self.capture_windsurf_interaction(
            user_input=user_input,
            assistant_response=debug_response,
            interaction_type="debugging",
            file_context=file_path,
            error_context=error_context,
            **kwargs,
        )

    async def capture_refactoring_session(
        self,
        user_input: str,
        refactoring_response: str,
        file_path: str,
        refactoring_type: str = None,
        **kwargs,
    ) -> Optional[str]:
        """Capture refactoring session interaction."""

        return await self.capture_windsurf_interaction(
            user_input=user_input,
            assistant_response=refactoring_response,
            interaction_type="refactoring",
            file_context=file_path,
            refactoring_type=refactoring_type,
            **kwargs,
        )

    async def capture_explanation_request(
        self,
        user_input: str,
        explanation: str,
        code_context: str = None,
        file_path: str = None,
        **kwargs,
    ) -> Optional[str]:
        """Capture code explanation interaction."""

        return await self.capture_windsurf_interaction(
            user_input=user_input,
            assistant_response=explanation,
            interaction_type="code_explanation",
            file_context=file_path,
            code_context=code_context,
            **kwargs,
        )


# Global instance for easy access
_windsurf_capture = None


def get_windsurf_capture(user_id: str = "windsurf_user") -> WindsurfLiveCapture:
    """Get the global Windsurf capture instance."""
    global _windsurf_capture
    if _windsurf_capture is None:
        _windsurf_capture = WindsurfLiveCapture(user_id)
    return _windsurf_capture


async def capture_windsurf_interaction(
    user_input: str,
    assistant_response: str,
    interaction_type: str = "code_assistance",
    file_context: Optional[str] = None,
    project_context: Optional[str] = None,
    language: Optional[str] = None,
    user_id: str = "windsurf_user",
    **kwargs,
) -> Optional[str]:
    """
    Convenience function to capture Windsurf interactions.

    Args:
        user_input: User's message to Windsurf
        assistant_response: Windsurf's response
        interaction_type: Type of interaction
        file_context: File being worked on
        project_context: Project context
        language: Programming language
        user_id: User identifier
        **kwargs: Additional metadata

    Returns:
        Capsule ID if created, None if not significant
    """

    capture = get_windsurf_capture(user_id)
    return await capture.capture_windsurf_interaction(
        user_input=user_input,
        assistant_response=assistant_response,
        interaction_type=interaction_type,
        file_context=file_context,
        project_context=project_context,
        language=language,
        **kwargs,
    )


async def main():
    """Test the Windsurf integration."""

    print("🌊 Testing Windsurf Live Capture Integration")
    print("=" * 50)

    # Test code completion
    print("\n📝 Testing code completion capture...")
    capsule_id = await capture_windsurf_interaction(
        user_input="Create a React component for user authentication",
        assistant_response="""Here's a React authentication component:

```jsx
import React, { useState } from 'react';
import { useAuth } from './hooks/useAuth';

const AuthComponent = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { login, register, error } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      await login(email, password);
    } catch (err) {
      console.error('Authentication failed:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="auth-form">
      <div className="form-group">
        <label htmlFor="email">Email:</label>
        <input
          id="email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          disabled={isLoading}
        />
      </div>

      <div className="form-group">
        <label htmlFor="password">Password:</label>
        <input
          id="password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          disabled={isLoading}
        />
      </div>

      {error && <div className="error-message">{error}</div>}

      <button type="submit" disabled={isLoading}>
        {isLoading ? 'Authenticating...' : 'Login'}
      </button>
    </form>
  );
};

export default AuthComponent;
```

This component includes:
- State management for email/password
- Form validation
- Loading states
- Error handling
- Accessibility features""",
        interaction_type="code_completion",
        file_context="src/components/AuthComponent.jsx",
        project_context="react-auth-app",
        language="javascript",
        user_id="windsurf_developer",
    )

    if capsule_id:
        print(f"✅ Windsurf interaction captured: {capsule_id}")
    else:
        print("❌ No capsule created - interaction not significant enough")

    # Test debugging session
    print("\n🐛 Testing debugging session capture...")
    debug_capsule = await capture_windsurf_interaction(
        user_input="I'm getting a TypeError: Cannot read property 'map' of undefined in my React component",
        assistant_response="""This error occurs when you're trying to use .map() on a value that is undefined. Here's how to fix it:

```jsx
// Problem: data might be undefined initially
const MyComponent = ({ data }) => {
  return (
    <div>
      {data.map(item => <div key={item.id}>{item.name}</div>)}
    </div>
  );
};

// Solution: Add a guard clause
const MyComponent = ({ data = [] }) => {
  return (
    <div>
      {data && data.map(item => <div key={item.id}>{item.name}</div>)}
    </div>
  );
};

// Or use optional chaining (modern approach)
const MyComponent = ({ data }) => {
  return (
    <div>
      {data?.map(item => <div key={item.id}>{item.name}</div>)}
    </div>
  );
};
```

Common causes:
1. Async data hasn't loaded yet
2. API call failed
3. Props not passed correctly
4. State initialization issue

Make sure to handle the loading and error states properly.""",
        interaction_type="debugging",
        file_context="src/components/DataList.jsx",
        language="javascript",
        error_context="TypeError: Cannot read property 'map' of undefined",
        user_id="windsurf_developer",
    )

    if debug_capsule:
        print(f"✅ Debugging session captured: {debug_capsule}")
    else:
        print("❌ No capsule created - interaction not significant enough")

    print("\n✅ Windsurf integration test completed!")


if __name__ == "__main__":
    asyncio.run(main())
