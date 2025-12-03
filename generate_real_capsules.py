#!/usr/bin/env python3
"""
Generate Real Capsules using OpenAI API
This script creates real UATP capsules from actual AI interactions
"""

import os
import json
import asyncio
from datetime import datetime
from src.integrations.openai_client import OpenAIClient
from src.engine.capsule_engine import CapsuleEngine
from src.core.database import db


async def generate_real_capsule_conversation():
    """Generate a real conversation and capsule it."""

    # Initialize OpenAI client
    openai_client = OpenAIClient()

    # Initialize capsule engine
    engine = CapsuleEngine()

    print("🤖 Generating real AI conversation...")

    # Real conversation prompts
    conversations = [
        {
            "user": "Explain how UATP (Universal Attribution and Trust Protocol) enables fair AI attribution",
            "context": "educational_content",
        },
        {
            "user": "What are the key benefits of using capsule-based AI reasoning?",
            "context": "technical_explanation",
        },
        {
            "user": "How does the UATP economics engine ensure fair compensation for content creators?",
            "context": "economic_analysis",
        },
    ]

    for i, conv in enumerate(conversations):
        try:
            print(f"🔄 Processing conversation {i+1}/{len(conversations)}")

            # Generate real AI response
            messages = [{"role": "user", "content": conv["user"]}]

            # Call OpenAI API
            response = await openai_client.generate_completion(
                messages=messages,
                model="gpt-3.5-turbo",  # Using gpt-3.5-turbo as it's more cost-effective
                max_tokens=200,
            )

            ai_response = response.get("content", "")

            print(f"✅ Got AI response: {ai_response[:100]}...")

            # Create reasoning trace capsule
            reasoning_steps = [
                {
                    "operation": "problem_analysis",
                    "reasoning": f"User asked: {conv['user']}",
                    "confidence": 1.0,
                    "timestamp": datetime.utcnow().isoformat(),
                },
                {
                    "operation": "knowledge_synthesis",
                    "reasoning": f"Generated comprehensive response covering key aspects",
                    "confidence": 0.9,
                    "timestamp": datetime.utcnow().isoformat(),
                },
                {
                    "operation": "response_generation",
                    "reasoning": ai_response,
                    "confidence": 0.95,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            ]

            # Create capsule using the engine
            capsule = await engine.create_reasoning_trace_capsule(
                reasoning_steps=reasoning_steps,
                agent_id="openai-gpt-3.5-turbo",
                context_metadata={
                    "conversation_type": conv["context"],
                    "user_query": conv["user"],
                    "ai_response": ai_response,
                    "real_interaction": True,
                },
            )

            print(f"📦 Created real capsule: {capsule.capsule_id}")

        except Exception as e:
            print(f"❌ Error processing conversation {i+1}: {e}")
            continue

    print("🎉 Real capsule generation complete!")


if __name__ == "__main__":
    print("🚀 Starting Real UATP Capsule Generation")
    print("=" * 50)

    # Check if OpenAI API key is configured
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not found in environment variables")
        print("Please set your OpenAI API key in .env file")
        exit(1)

    asyncio.run(generate_real_capsule_conversation())
