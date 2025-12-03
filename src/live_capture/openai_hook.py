#!/usr/bin/env python3
"""
OpenAI Live Capture Integration
===============================

This module provides integration with OpenAI API for live conversation
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


class OpenAILiveCapture:
    """Live capture integration for OpenAI API."""

    def __init__(self, user_id: str = "openai_user", api_key: Optional[str] = None):
        self.platform = "openai"
        self.user_id = user_id
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.session_id = f"openai_session_{int(time.time())}"

        logger.info(f"🤖 OpenAI Live Capture initialized")
        logger.info(f"   User ID: {user_id}")
        logger.info(f"   Session ID: {self.session_id}")
        logger.info(f"   API Key: {'✅ Set' if self.api_key else '❌ Missing'}")

    async def capture_openai_interaction(
        self,
        user_input: str,
        assistant_response: str,
        model: str = "gpt-4",
        interaction_type: str = "chat_completion",
        conversation_context: Optional[List[Dict]] = None,
        usage_info: Optional[Dict] = None,
        **kwargs,
    ) -> Optional[str]:
        """
        Capture an OpenAI interaction and create capsule if significant.

        Args:
            user_input: User's message to OpenAI
            assistant_response: OpenAI's response
            model: OpenAI model used (gpt-4, gpt-3.5-turbo, etc.)
            interaction_type: Type of interaction (chat_completion, completion, etc.)
            conversation_context: Full conversation history
            usage_info: Token usage information
            **kwargs: Additional metadata

        Returns:
            Capsule ID if created, None if not significant
        """

        try:
            # Enhance metadata with OpenAI-specific context
            metadata = {
                "interaction_type": interaction_type,
                "model": model,
                "conversation_context": conversation_context,
                "usage_info": usage_info,
                "openai_version": "1.0",
                "api_provider": "openai",
                **kwargs,
            }

            # Capture the interaction
            capsule_id = await capture_live_interaction(
                session_id=self.session_id,
                user_message=user_input,
                ai_response=assistant_response,
                user_id=self.user_id,
                platform=self.platform,
                model=model,
                metadata=metadata,
            )

            if capsule_id:
                logger.info(f"🤖 OpenAI interaction encapsulated: {capsule_id}")
                logger.info(f"   Model: {model}")
                logger.info(f"   Type: {interaction_type}")
                if usage_info:
                    logger.info(
                        f"   Tokens: {usage_info.get('total_tokens', 'unknown')}"
                    )

            return capsule_id

        except Exception as e:
            logger.error(f"❌ OpenAI interaction capture failed: {e}")
            return None

    async def capture_chat_completion(
        self,
        messages: List[Dict[str, str]],
        response: str,
        model: str = "gpt-4",
        usage_info: Optional[Dict] = None,
        **kwargs,
    ) -> Optional[str]:
        """Capture chat completion interaction."""

        # Extract user input from messages
        user_messages = [msg for msg in messages if msg.get("role") == "user"]
        user_input = user_messages[-1].get("content", "") if user_messages else ""

        return await self.capture_openai_interaction(
            user_input=user_input,
            assistant_response=response,
            model=model,
            interaction_type="chat_completion",
            conversation_context=messages,
            usage_info=usage_info,
            **kwargs,
        )

    async def capture_completion(
        self,
        prompt: str,
        completion: str,
        model: str = "gpt-3.5-turbo-instruct",
        usage_info: Optional[Dict] = None,
        **kwargs,
    ) -> Optional[str]:
        """Capture completion interaction."""

        return await self.capture_openai_interaction(
            user_input=prompt,
            assistant_response=completion,
            model=model,
            interaction_type="completion",
            usage_info=usage_info,
            **kwargs,
        )

    async def capture_code_generation(
        self,
        user_input: str,
        code_response: str,
        language: str = None,
        model: str = "gpt-4",
        **kwargs,
    ) -> Optional[str]:
        """Capture code generation interaction."""

        return await self.capture_openai_interaction(
            user_input=user_input,
            assistant_response=code_response,
            model=model,
            interaction_type="code_generation",
            language=language,
            **kwargs,
        )

    async def capture_embedding_interaction(
        self,
        input_text: str,
        embedding_result: List[float],
        model: str = "text-embedding-ada-002",
        **kwargs,
    ) -> Optional[str]:
        """Capture embedding interaction."""

        # For embeddings, we'll create a summary response
        response = f"Generated embedding vector with {len(embedding_result)} dimensions using {model}"

        return await self.capture_openai_interaction(
            user_input=input_text,
            assistant_response=response,
            model=model,
            interaction_type="embedding",
            embedding_dimensions=len(embedding_result),
            **kwargs,
        )

    async def capture_function_calling(
        self,
        user_input: str,
        function_calls: List[Dict],
        function_responses: List[Dict],
        final_response: str,
        model: str = "gpt-4",
        **kwargs,
    ) -> Optional[str]:
        """Capture function calling interaction."""

        return await self.capture_openai_interaction(
            user_input=user_input,
            assistant_response=final_response,
            model=model,
            interaction_type="function_calling",
            function_calls=function_calls,
            function_responses=function_responses,
            **kwargs,
        )


# Global instance for easy access
_openai_capture = None


def get_openai_capture(
    user_id: str = "openai_user", api_key: Optional[str] = None
) -> OpenAILiveCapture:
    """Get the global OpenAI capture instance."""
    global _openai_capture
    if _openai_capture is None:
        _openai_capture = OpenAILiveCapture(user_id, api_key)
    return _openai_capture


async def capture_openai_interaction(
    user_input: str,
    assistant_response: str,
    model: str = "gpt-4",
    interaction_type: str = "chat_completion",
    conversation_context: Optional[List[Dict]] = None,
    usage_info: Optional[Dict] = None,
    user_id: str = "openai_user",
    **kwargs,
) -> Optional[str]:
    """
    Convenience function to capture OpenAI interactions.

    Args:
        user_input: User's message to OpenAI
        assistant_response: OpenAI's response
        model: OpenAI model used
        interaction_type: Type of interaction
        conversation_context: Full conversation history
        usage_info: Token usage information
        user_id: User identifier
        **kwargs: Additional metadata

    Returns:
        Capsule ID if created, None if not significant
    """

    capture = get_openai_capture(user_id)
    return await capture.capture_openai_interaction(
        user_input=user_input,
        assistant_response=assistant_response,
        model=model,
        interaction_type=interaction_type,
        conversation_context=conversation_context,
        usage_info=usage_info,
        **kwargs,
    )


# OpenAI API wrapper with automatic capturing
class CaptureEnabledOpenAI:
    """OpenAI API wrapper with automatic capsule generation."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        user_id: str = "openai_user",
        auto_capture: bool = True,
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.user_id = user_id
        self.auto_capture = auto_capture
        self.capture = get_openai_capture(user_id, api_key)

        # Try to import OpenAI client
        try:
            import openai

            self.client = openai.OpenAI(api_key=self.api_key)
            logger.info("✅ OpenAI client initialized with auto-capture")
        except ImportError:
            logger.warning(
                "⚠️ OpenAI library not installed, capture wrapper unavailable"
            )
            self.client = None

    async def chat_completion(
        self, messages: List[Dict[str, str]], model: str = "gpt-4", **kwargs
    ) -> Dict[str, Any]:
        """Chat completion with automatic capturing."""

        if not self.client:
            raise RuntimeError("OpenAI client not available")

        try:
            # Make the API call
            response = self.client.chat.completions.create(
                model=model, messages=messages, **kwargs
            )

            # Extract response data
            response_content = response.choices[0].message.content
            usage_info = response.usage.dict() if response.usage else None

            # Capture interaction if enabled
            if self.auto_capture:
                await self.capture.capture_chat_completion(
                    messages=messages,
                    response=response_content,
                    model=model,
                    usage_info=usage_info,
                )

            return {
                "response": response_content,
                "usage": usage_info,
                "model": model,
                "raw_response": response,
            }

        except Exception as e:
            logger.error(f"❌ OpenAI chat completion failed: {e}")
            raise


async def main():
    """Test the OpenAI integration."""

    print("🤖 Testing OpenAI Live Capture Integration")
    print("=" * 50)

    # Test chat completion
    print("\n💬 Testing chat completion capture...")
    messages = [
        {
            "role": "user",
            "content": "Write a Python function to calculate the Fibonacci sequence using dynamic programming",
        }
    ]

    response = """Here's a Python function to calculate the Fibonacci sequence using dynamic programming:

```python
def fibonacci_dp(n):
    '''
    Calculate the nth Fibonacci number using dynamic programming (bottom-up approach).
    
    Args:
        n (int): The position in the Fibonacci sequence (0-indexed)
        
    Returns:
        int: The nth Fibonacci number
    '''
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    
    # Create a DP table to store results
    dp = [0] * (n + 1)
    dp[0] = 0
    dp[1] = 1
    
    # Fill the DP table bottom-up
    for i in range(2, n + 1):
        dp[i] = dp[i - 1] + dp[i - 2]
    
    return dp[n]

# Example usage
def fibonacci_sequence(count):
    '''Generate the first 'count' Fibonacci numbers.'''
    return [fibonacci_dp(i) for i in range(count)]

# Test the function
print("First 10 Fibonacci numbers:")
print(fibonacci_sequence(10))  # Output: [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]

# Calculate a specific Fibonacci number
print(f"The 15th Fibonacci number is: {fibonacci_dp(15)}")  # Output: 610
```

This implementation has several advantages:

1. **Time Complexity**: O(n) - much better than the recursive approach
2. **Space Complexity**: O(n) for the DP table
3. **No redundant calculations**: Each Fibonacci number is calculated only once
4. **Handles edge cases**: Properly handles n <= 0 and n == 1

**Space-optimized version** (O(1) space complexity):

```python
def fibonacci_optimized(n):
    '''Space-optimized version using only two variables.'''
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    
    prev2 = 0  # F(i-2)
    prev1 = 1  # F(i-1)
    
    for i in range(2, n + 1):
        current = prev1 + prev2
        prev2 = prev1
        prev1 = current
    
    return prev1
```

This optimized version uses only O(1) space while maintaining O(n) time complexity."""

    usage_info = {"prompt_tokens": 25, "completion_tokens": 350, "total_tokens": 375}

    capsule_id = await capture_openai_interaction(
        user_input=messages[0]["content"],
        assistant_response=response,
        model="gpt-4",
        interaction_type="chat_completion",
        conversation_context=messages,
        usage_info=usage_info,
        user_id="openai_developer",
    )

    if capsule_id:
        print(f"✅ OpenAI interaction captured: {capsule_id}")
    else:
        print("❌ No capsule created - interaction not significant enough")

    # Test code generation
    print("\n🔧 Testing code generation capture...")
    code_capsule = await capture_openai_interaction(
        user_input="Create a REST API endpoint for user authentication using FastAPI",
        assistant_response="""Here's a FastAPI REST API endpoint for user authentication:

```python
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os

app = FastAPI()

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Models
class UserCreate(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

# Mock user database
fake_users_db = {
    "testuser": {
        "username": "testuser",
        "hashed_password": pwd_context.hash("testpass123")
    }
}

# Helper functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def authenticate_user(username: str, password: str):
    user = fake_users_db.get(username)
    if not user or not verify_password(password, user["hashed_password"]):
        return False
    return user

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = fake_users_db.get(username)
    if user is None:
        raise credentials_exception
    return user

# Endpoints
@app.post("/register", response_model=dict)
async def register(user: UserCreate):
    if user.username in fake_users_db:
        raise HTTPException(
            status_code=400,
            detail="Username already registered"
        )
    
    hashed_password = pwd_context.hash(user.password)
    fake_users_db[user.username] = {
        "username": user.username,
        "hashed_password": hashed_password
    }
    
    return {"message": "User registered successfully"}

@app.post("/login", response_model=Token)
async def login(user: UserLogin):
    authenticated_user = authenticate_user(user.username, user.password)
    if not authenticated_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": authenticated_user["username"]}, 
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/protected")
async def protected_route(current_user: dict = Depends(get_current_user)):
    return {"message": f"Hello {current_user['username']}, this is a protected route!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

This implementation provides:

1. **User Registration**: `/register` endpoint for creating new users
2. **User Login**: `/login` endpoint that returns JWT tokens
3. **Protected Routes**: Example of how to protect routes with JWT authentication
4. **Password Hashing**: Secure password storage using bcrypt
5. **JWT Tokens**: Secure token-based authentication
6. **Error Handling**: Proper HTTP error responses

To use this API:

1. Install dependencies: `pip install fastapi uvicorn passlib[bcrypt] python-jose[cryptography]`
2. Run the server: `python main.py`
3. Register a user: `POST /register`
4. Login to get a token: `POST /login`
5. Use the token in the Authorization header: `Bearer <token>`""",
        model="gpt-4",
        interaction_type="code_generation",
        language="python",
        user_id="openai_developer",
    )

    if code_capsule:
        print(f"✅ Code generation captured: {code_capsule}")
    else:
        print("❌ No capsule created - interaction not significant enough")

    print("\n✅ OpenAI integration test completed!")


if __name__ == "__main__":
    asyncio.run(main())
