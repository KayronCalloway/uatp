#!/usr/bin/env python3
"""
Create a significant UATP conversation that should trigger capsule creation
"""

import requests
import time
import json


def create_significant_conversation():
    """Create a conversation about UATP implementation that should create a capsule."""

    print("🔥 Creating significant UATP conversation...")

    session_id = f"uatp-implementation-{int(time.time())}"

    # Create a multi-turn technical conversation about UATP
    conversation_data = {
        "session_id": session_id,
        "user_id": "kay",
        "messages": [
            {
                "role": "user",
                "content": "I need help implementing a live UATP capsule creation system for real-time attribution tracking. How do I capture Claude Code conversations and automatically create capsules when they're significant enough?",
            },
            {
                "role": "assistant",
                "content": "I'll help you implement a comprehensive UATP live capture system. Here's how to build it:\n\n```python\nfrom uatp.capture import LiveCaptureSystem\nfrom uatp.engine import CapsuleEngine\n\nclass UATPLiveCapture:\n    def __init__(self):\n        self.engine = CapsuleEngine()\n        self.active_sessions = {}\n    \n    async def capture_conversation(self, session_id, messages):\n        significance = self.calculate_significance(messages)\n        if significance >= 0.6:\n            await self.create_attribution_capsule(session_id, messages)\n```\n\nThe key is to analyze conversation significance in real-time and create capsules automatically.",
            },
            {
                "role": "user",
                "content": "Perfect! How do I calculate the significance score? I want to ensure that conversations about UATP implementation, AI attribution, and technical development get high scores.",
            },
            {
                "role": "assistant",
                "content": "Here's a robust significance scoring algorithm for UATP conversations:\n\n```python\ndef calculate_significance(self, messages):\n    score = 0.0\n    \n    # Technical content keywords (high weight)\n    tech_keywords = ['uatp', 'capsule', 'attribution', 'implement', 'api', 'engine', 'create']\n    \n    # Code patterns (medium weight) \n    code_patterns = ['```', 'function', 'class', 'async', 'await']\n    \n    # AI/ML keywords (high weight for attribution context)\n    ai_keywords = ['ai', 'llm', 'openai', 'claude', 'reasoning', 'model']\n    \n    for msg in messages:\n        content = msg['content'].lower()\n        \n        # Technical keywords: +0.3 each\n        score += sum(0.3 for kw in tech_keywords if kw in content)\n        \n        # Code patterns: +0.2 each\n        score += sum(0.2 for pattern in code_patterns if pattern in msg['content'])\n        \n        # AI keywords: +0.25 each\n        score += sum(0.25 for kw in ai_keywords if kw in content)\n        \n        # Length bonus for detailed responses\n        if len(content) > 200:\n            score += 0.1\n    \n    # Message count factor\n    score += min(len(messages) * 0.1, 1.0)\n    \n    return min(score / 5.0, 1.0)  # Normalize to 0-1\n```\n\nThis ensures UATP development conversations get high significance scores.",
            },
            {
                "role": "user",
                "content": "Excellent! Now I need to integrate this with my existing UATP backend API that's running on port 8000. The frontend dashboard should show these conversations in real-time and allow creating capsules with the click of a button.",
            },
            {
                "role": "assistant",
                "content": "Perfect! Here's how to integrate with your existing UATP backend and create the real-time frontend connection:\n\n```python\n# Backend Integration (src/api/live_capture_routes.py)\nfrom quart import Blueprint, request, jsonify\n\nlive_bp = Blueprint('live_capture', __name__)\n\n@live_bp.route('/live/capture/conversation', methods=['POST'])\nasync def capture_conversation():\n    data = await request.get_json()\n    session_id = data.get('session_id')\n    \n    # Store conversation with significance analysis\n    conversation = await capture_system.process_conversation(\n        session_id=session_id,\n        messages=data.get('messages', []),\n        user_id=data.get('user_id')\n    )\n    \n    return jsonify({\n        'success': True,\n        'conversation_id': session_id,\n        'significance_score': conversation.significance_score,\n        'should_create_capsule': conversation.should_create_capsule\n    })\n\n@live_bp.route('/live/conversations', methods=['GET'])\nasync def get_live_conversations():\n    conversations = await capture_system.get_active_conversations()\n    return jsonify({'success': True, 'conversations': conversations})\n```\n\nFor the frontend dashboard integration with your existing Live Capture component, you'll want to add WebSocket support for real-time updates and capsule creation buttons.",
            },
            {
                "role": "user",
                "content": "This is exactly what I need for Week 1 of my UATP realization strategy! The live conversation capture is the foundation for the entire AI accountability infrastructure. Once this works, we can expand to Cursor IDE, browser extensions, and eventually all AI interactions will create attribution capsules.",
            },
            {
                "role": "assistant",
                "content": "Absolutely! You're building the foundational infrastructure for universal AI accountability. This Week 1 implementation creates the technical foundation for your complete UATP vision:\n\n**Phase 1 Foundation (Week 1-2):**\n- ✅ Live Claude Code conversation capture \n- ✅ Real-time significance analysis\n- ✅ Automatic capsule creation for significant interactions\n- ✅ Frontend dashboard integration\n\n**Expansion Path:**\n```\nWeek 1-2: Claude Code → Cursor IDE → VS Code\nMonth 2-3: Browser extensions → Mobile apps → Voice assistants  \nMonth 4-6: API integrations → Enterprise deployments\nYear 1+: Universal AI decision accountability\n```\n\nThe architecture you're building now scales to handle:\n- Every autonomous vehicle decision → Insurance liability capsules\n- Every medical AI diagnosis → Audit trail capsules  \n- Every financial AI decision → Regulatory compliance capsules\n- Every content moderation decision → Transparency capsules\n\nYou're not just building attribution software - you're building the constitutional framework for AI-human civilization. Every conversation captured now is a step toward universal AI accountability.",
            },
        ],
        "model": "claude-3-sonnet",
    }

    try:
        # Send to OpenAI capture endpoint (more comprehensive)
        response = requests.post(
            "http://localhost:8000/api/v1/live/capture/openai", json=conversation_data
        )
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print(f"✅ Significant conversation created: {session_id}")
                print(f"📊 Messages: {len(conversation_data['messages'])}")

                # Check the significance score
                time.sleep(2)  # Wait for processing
                status_response = requests.get(
                    f"http://localhost:8000/api/v1/live/capture/conversation/{session_id}"
                )
                if status_response.status_code == 200:
                    status_result = status_response.json()
                    if status_result.get("success"):
                        conv = status_result.get("conversation", {})
                        significance = conv.get("significance_score", 0)
                        should_create = conv.get("should_create_capsule", False)

                        print(f"📈 Significance score: {significance:.2f}")
                        print(f"🔥 Should create capsule: {should_create}")

                        if should_create:
                            print(
                                "🎯 This conversation meets capsule creation criteria!"
                            )
                            print("💎 A UATP capsule should be created automatically")
                        else:
                            print(
                                "📝 Conversation recorded but doesn't meet capsule threshold"
                            )
                    else:
                        print("❌ Could not check conversation status")
                else:
                    print("❌ Status check failed")
            else:
                print(f"❌ Failed to create conversation: {result.get('error')}")
        else:
            print(f"❌ Request failed with status {response.status_code}")

    except Exception as e:
        print(f"❌ Error creating conversation: {e}")


if __name__ == "__main__":
    create_significant_conversation()
