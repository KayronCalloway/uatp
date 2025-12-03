#!/usr/bin/env python3
"""
UATP User App Demo
Consumer-facing application demonstrating real-time AI attribution tracking
"""

import asyncio
import logging
from datetime import datetime
from decimal import Decimal

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mock user data for demo
DEMO_USERS = {
    "alice123": {
        "name": "Alice Johnson",
        "email": "alice@example.com",
        "joined": "2024-01-15",
        "total_earnings": Decimal("45.67"),
        "attribution_count": 127,
        "preferred_payout": "paypal",
    },
    "bob456": {
        "name": "Bob Smith",
        "email": "bob@example.com",
        "joined": "2024-02-20",
        "total_earnings": Decimal("23.45"),
        "attribution_count": 89,
        "preferred_payout": "crypto",
    },
}


class UserApp:
    """Main user application class"""

    def __init__(self):
        self.current_user = None
        self.ai_orchestrator = None
        self.attribution_history = []

    async def initialize(self):
        """Initialize the app with AI platform integrations"""

        try:
            # Import our AI platform framework
            import os
            import sys

            sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

            from src.integrations.ai_platform_framework import (
                setup_multi_platform_attribution,
            )

            # Set up multi-platform attribution
            self.ai_orchestrator = setup_multi_platform_attribution(
                openai_key=os.getenv("OPENAI_API_KEY"),
                anthropic_key=os.getenv("ANTHROPIC_API_KEY"),
            )

            logger.info("UATP User App initialized successfully")

        except Exception as e:
            logger.warning(f"AI platform integration failed: {e}")
            logger.info("Running in demo mode without real AI integration")

    def login(self, user_id: str) -> bool:
        """User login"""
        if user_id in DEMO_USERS:
            self.current_user = user_id
            print(f"✅ Welcome back, {DEMO_USERS[user_id]['name']}!")
            return True
        print("❌ User not found")
        return False

    def display_dashboard(self):
        """Display user dashboard"""
        if not self.current_user:
            print("❌ Please login first")
            return

        user_data = DEMO_USERS[self.current_user]

        print("\n" + "=" * 60)
        print("🎯 UATP ATTRIBUTION DASHBOARD")
        print("=" * 60)
        print(f"👤 User: {user_data['name']}")
        print(f"📧 Email: {user_data['email']}")
        print(f"📅 Member since: {user_data['joined']}")
        print(f"💰 Total earnings: ${user_data['total_earnings']}")
        print(f"🔗 Attributions: {user_data['attribution_count']}")
        print(f"💳 Payout method: {user_data['preferred_payout']}")
        print("=" * 60)

        # Show recent attribution activity
        self.display_recent_activity()

    def display_recent_activity(self):
        """Display recent attribution activity"""

        print("\n📊 RECENT ATTRIBUTION ACTIVITY")
        print("-" * 40)

        # Mock recent activity
        recent_activity = [
            {
                "date": "2024-01-10",
                "platform": "OpenAI",
                "conversation": "Climate change discussion",
                "attribution": "$0.45",
                "confidence": 0.82,
            },
            {
                "date": "2024-01-09",
                "platform": "Claude",
                "conversation": "Python programming help",
                "attribution": "$0.23",
                "confidence": 0.76,
            },
            {
                "date": "2024-01-08",
                "platform": "OpenAI",
                "conversation": "Recipe recommendations",
                "attribution": "$0.12",
                "confidence": 0.65,
            },
        ]

        for activity in recent_activity:
            print(
                f"📅 {activity['date']} | {activity['platform']:10} | {activity['attribution']:8} | {activity['conversation']}"
            )
            print(f"   Confidence: {activity['confidence']:.1%}")
            print()

    async def start_ai_conversation(self):
        """Start an AI conversation with real-time attribution"""

        if not self.current_user:
            print("❌ Please login first")
            return

        print("\n🤖 AI CONVERSATION WITH ATTRIBUTION")
        print("=" * 50)
        print("Type your questions below. Attribution will be tracked in real-time!")
        print("Type 'quit' to exit the conversation.")
        print("-" * 50)

        conversation_id = f"conv_{datetime.now().timestamp()}"

        while True:
            user_input = input("\n🧑 You: ")

            if user_input.lower() == "quit":
                break

            # Show attribution calculation
            await self.process_ai_interaction(user_input, conversation_id)

    async def process_ai_interaction(self, user_input: str, conversation_id: str):
        """Process AI interaction with attribution tracking"""

        if self.ai_orchestrator:
            # Real AI integration
            try:
                from src.integrations.openai_attribution import AttributionContext

                # Create attribution context
                context = AttributionContext(
                    user_id=self.current_user,
                    conversation_id=conversation_id,
                    prompt_sources=["user_conversation", "personal_knowledge"],
                    training_data_sources=["web_crawl", "books", "papers"],
                    attribution_metadata={
                        "app_version": "1.0",
                        "interaction_type": "chat",
                    },
                )

                # Get completion with attribution
                (
                    completion,
                    attribution_result,
                ) = await self.ai_orchestrator.get_completion_with_attribution(
                    prompt=user_input, attribution_context=context
                )

                # Display response and attribution
                print(f"\n🤖 AI: {completion}")
                print(f"\n💰 Attribution: ${attribution_result.total_value:.4f}")
                print(
                    f"   Direct: ${sum(attribution_result.direct_attributions.values()):.4f}"
                )
                print(f"   Commons: ${attribution_result.commons_allocation:.4f}")
                print(f"   UBA: ${attribution_result.uba_allocation:.4f}")
                print(
                    f"   Confidence: {max(attribution_result.confidence_scores.values()):.1%}"
                )

            except Exception as e:
                logger.error(f"Real AI interaction failed: {e}")
                await self.mock_ai_interaction(user_input)
        else:
            # Mock AI interaction
            await self.mock_ai_interaction(user_input)

    async def mock_ai_interaction(self, user_input: str):
        """Mock AI interaction for demo purposes"""

        # Mock AI responses
        responses = [
            "That's an interesting question! Let me think about that...",
            "Based on the information available, I would say...",
            "Here's what I understand about this topic...",
            "That's a complex issue with multiple perspectives...",
            "Let me break this down for you...",
        ]

        import random

        mock_response = random.choice(responses)
        mock_attribution = random.uniform(0.01, 0.50)
        mock_confidence = random.uniform(0.60, 0.95)

        print(f"\n🤖 AI: {mock_response}")
        print(f"\n💰 Attribution: ${mock_attribution:.4f}")
        print(f"   Direct: ${mock_attribution * 0.7:.4f}")
        print(f"   Commons: ${mock_attribution * 0.15:.4f}")
        print(f"   UBA: ${mock_attribution * 0.15:.4f}")
        print(f"   Confidence: {mock_confidence:.1%}")

        # Update user earnings
        DEMO_USERS[self.current_user]["total_earnings"] += Decimal(
            str(mock_attribution)
        )
        DEMO_USERS[self.current_user]["attribution_count"] += 1

    def display_earnings_breakdown(self):
        """Display detailed earnings breakdown"""

        if not self.current_user:
            print("❌ Please login first")
            return

        print("\n💰 EARNINGS BREAKDOWN")
        print("=" * 40)

        # Mock breakdown data
        breakdown = {
            "Direct Attributions": "67.5%",
            "Commons Fund (UBA)": "15.0%",
            "Temporal Decay": "12.5%",
            "Platform Fees": "5.0%",
        }

        total_earnings = DEMO_USERS[self.current_user]["total_earnings"]

        for category, percentage in breakdown.items():
            amount = total_earnings * (float(percentage.strip("%")) / 100)
            print(f"{category:20} {percentage:>8} ${amount:.2f}")

        print("-" * 40)
        print(f"{'Total Earnings':20} {'100.0%':>8} ${total_earnings:.2f}")

        print(
            f"\n💳 Next payout: ${total_earnings:.2f} via {DEMO_USERS[self.current_user]['preferred_payout']}"
        )

    def display_attribution_insights(self):
        """Display attribution insights and analytics"""

        print("\n📊 ATTRIBUTION INSIGHTS")
        print("=" * 40)

        # Mock insights
        insights = [
            "🎯 Your technical explanations have 15% higher attribution rates",
            "📈 Attribution confidence increased 12% this month",
            "🔥 Best performing topic: Climate science discussions",
            "⏰ Peak attribution times: 2-4 PM weekdays",
            "🌍 Contributing to UBA: $6.85 to global commons fund",
        ]

        for insight in insights:
            print(f"  {insight}")

        print("\n🏆 Attribution Rank: Top 15% of contributors")
        print("⭐ Quality Score: 4.2/5.0")

    def display_settings(self):
        """Display user settings and preferences"""

        print("\n⚙️ USER SETTINGS")
        print("=" * 30)

        user_data = DEMO_USERS[self.current_user]

        print("🔔 Notifications: Enabled")
        print(f"💳 Payout method: {user_data['preferred_payout']}")
        print("🎯 Attribution threshold: $1.00")
        print("🔒 Privacy level: Standard")
        print("🌍 UBA participation: Enabled")
        print("📱 Platform connections: OpenAI, Claude")

    def display_menu(self):
        """Display main menu"""

        print("\n🎯 UATP USER APP - MAIN MENU")
        print("=" * 35)
        print("1. 📊 Dashboard")
        print("2. 🤖 Start AI Conversation")
        print("3. 💰 Earnings Breakdown")
        print("4. 📈 Attribution Insights")
        print("5. ⚙️ Settings")
        print("6. 🚪 Logout")
        print("=" * 35)

    async def run(self):
        """Main application loop"""

        await self.initialize()

        print("\n🚀 WELCOME TO UATP USER APP")
        print("Real-time AI Attribution Tracking")
        print("=" * 40)

        # Demo login
        print("\n🔐 LOGIN")
        print("Available demo users: alice123, bob456")
        user_id = input("Enter user ID: ")

        if not self.login(user_id):
            return

        # Main menu loop
        while True:
            self.display_menu()

            choice = input("\nSelect an option (1-6): ")

            if choice == "1":
                self.display_dashboard()
            elif choice == "2":
                await self.start_ai_conversation()
            elif choice == "3":
                self.display_earnings_breakdown()
            elif choice == "4":
                self.display_attribution_insights()
            elif choice == "5":
                self.display_settings()
            elif choice == "6":
                print(f"\n👋 Goodbye, {DEMO_USERS[self.current_user]['name']}!")
                break
            else:
                print("❌ Invalid option. Please try again.")

            input("\nPress Enter to continue...")


# Main execution
if __name__ == "__main__":

    async def main():
        app = UserApp()
        await app.run()

    asyncio.run(main())
