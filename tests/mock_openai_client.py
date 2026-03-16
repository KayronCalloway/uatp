"""
Mock implementation of the OpenAIClient for testing purposes.
This allows us to test the /reasoning/generate endpoint without a valid OpenAI API key.
"""

import asyncio


class MockOpenAIClient:
    """A mock version of the OpenAIClient that returns predefined responses."""

    def __init__(self, response_text="This is a mock AI response.", *args, **kwargs):
        """Initialize the mock client."""
        self.call_count = 0
        self.response_text = response_text

    def generate_text(self, prompt, model="gpt-4", max_tokens=150):
        """Mock synchronous text generation."""
        self.call_count += 1
        return self._generate_response(prompt, model)

    async def generate_text_async(self, prompt, model="gpt-4", **kwargs):
        """Mock asynchronous text generation."""
        self.call_count += 1
        # Add a small delay to simulate network latency
        await asyncio.sleep(0.1)
        return self._generate_response(prompt, model)

    async def get_completion_async(self, prompt, model="gpt-4", **kwargs):
        """Mock asynchronous text generation to match the new interface."""
        self.call_count += 1
        # Add a small delay to simulate network latency
        await asyncio.sleep(0.1)
        return self._generate_response(prompt, model)

    def _generate_response(self, prompt, model):
        """Generate a mock response based on the prompt."""
        return self.response_text

    def _log_interaction(self, *args, **kwargs):
        """Mock the interaction logging."""
        pass  # Do nothing, this is just a mock
