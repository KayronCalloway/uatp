#!/usr/bin/env python3
"""
UATP Mobile App Prototype
React Native-style mobile app prototype for UATP attribution tracking
"""

import asyncio
import logging
from decimal import Decimal
from typing import Any, Dict

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MobileAppState:
    """Mobile app state management"""

    def __init__(self):
        self.current_screen = "splash"
        self.user = None
        self.navigation_stack = ["splash"]
        self.notifications = []
        self.real_time_data = {
            "earnings_today": Decimal("0.00"),
            "attributions_today": 0,
            "live_conversations": [],
        }

    def navigate_to(self, screen: str):
        """Navigate to a screen"""
        self.navigation_stack.append(screen)
        self.current_screen = screen

    def go_back(self):
        """Go back to previous screen"""
        if len(self.navigation_stack) > 1:
            self.navigation_stack.pop()
            self.current_screen = self.navigation_stack[-1]


class MobileUI:
    """Mobile UI components and rendering"""

    @staticmethod
    def render_header(title: str, has_back: bool = False) -> str:
        """Render mobile header"""
        back_button = "← " if has_back else ""
        return f"""
╭─────────────────────────────────────╮
│ {back_button}{title:<31} │
╰─────────────────────────────────────╯"""

    @staticmethod
    def render_card(title: str, content: str, highlight: bool = False) -> str:
        """Render mobile card component"""
        border_char = "█" if highlight else "─"
        return f"""
╭{border_char * 37}╮
│ {title:<35} │
├─────────────────────────────────────┤
│ {content:<35} │
╰{border_char * 37}╯"""

    @staticmethod
    def render_button(text: str, primary: bool = False) -> str:
        """Render mobile button"""
        if primary:
            return f"┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓\n┃ {text:^35} ┃\n┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛"
        else:
            return f"┌─────────────────────────────────────┐\n│ {text:^35} │\n└─────────────────────────────────────┘"

    @staticmethod
    def render_list_item(title: str, subtitle: str, value: str) -> str:
        """Render mobile list item"""
        return f"""
├─────────────────────────────────────┤
│ {title:<20} {value:>15} │
│ {subtitle:<35} │"""

    @staticmethod
    def render_progress_bar(percentage: float, label: str) -> str:
        """Render progress bar"""
        filled = int(percentage / 100 * 30)
        empty = 30 - filled
        bar = "█" * filled + "░" * empty
        return f"│ {label:<20} │{bar}│ {percentage:5.1f}% │"


class MobileApp:
    """Main mobile app class"""

    def __init__(self):
        self.state = MobileAppState()
        self.ui = MobileUI()

        # Mock data
        self.mock_user = {
            "id": "user123",
            "name": "Alex Johnson",
            "email": "alex@example.com",
            "avatar": "👤",
            "total_earnings": Decimal("127.45"),
            "total_attributions": 342,
            "member_since": "2024-01-15",
            "verification_status": "verified",
            "payout_method": "PayPal",
        }

        self.mock_recent_activity = [
            {
                "id": "1",
                "platform": "OpenAI",
                "amount": "$0.23",
                "confidence": "87%",
                "time": "2 min ago",
                "conversation": "Climate change discussion",
            },
            {
                "id": "2",
                "platform": "Claude",
                "amount": "$0.15",
                "confidence": "92%",
                "time": "15 min ago",
                "conversation": "Python programming help",
            },
            {
                "id": "3",
                "platform": "OpenAI",
                "amount": "$0.08",
                "confidence": "76%",
                "time": "1 hour ago",
                "conversation": "Recipe recommendations",
            },
        ]

        self.mock_live_conversations = [
            {
                "id": "conv1",
                "platform": "OpenAI",
                "status": "active",
                "estimated_value": "$0.12",
                "time": "30 sec ago",
            },
            {
                "id": "conv2",
                "platform": "Claude",
                "status": "processing",
                "estimated_value": "$0.18",
                "time": "1 min ago",
            },
        ]

    def render_splash_screen(self) -> str:
        """Render splash screen"""
        return f"""
{self.ui.render_header("UATP Attribution Tracker")}

        ⚡ UATP ⚡
    Attribution Tracker

   💰 Real-time AI Attribution
   🔗 Cross-platform Tracking
   📊 Earnings Dashboard
   🏦 Automatic Payouts

{self.ui.render_button("Get Started", primary=True)}

{self.ui.render_button("Login")}

        Version 1.0.0"""

    def render_login_screen(self) -> str:
        """Render login screen"""
        return f"""
{self.ui.render_header("Login", has_back=True)}

{self.ui.render_card("Welcome Back", "Sign in to track your AI attributions")}

┌─────────────────────────────────────┐
│ Email                               │
│ ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓ │
│ ┃ alex@example.com              ┃ │
│ ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛ │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ Password                            │
│ ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓ │
│ ┃ ••••••••••••••••••••••••••••••┃ │
│ ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛ │
└─────────────────────────────────────┘

{self.ui.render_button("Sign In", primary=True)}

{self.ui.render_button("Forgot Password?")}

┌─────────────────────────────────────┐
│           Need an account?          │
│              Sign Up                │
└─────────────────────────────────────┘"""

    def render_dashboard_screen(self) -> str:
        """Render main dashboard"""
        user = self.mock_user
        return f"""
{self.ui.render_header(f"Hi, {user['name'].split()[0]} {user['avatar']}")}

{self.ui.render_card("Today's Earnings", f"${self.state.real_time_data['earnings_today']:.2f}", highlight=True)}

┌─────────────────────────────────────┐
│ Quick Stats                         │
├─────────────────────────────────────┤
│ Total Earnings    ${user['total_earnings']:>15} │
│ Attributions      {user['total_attributions']:>15} │
│ Success Rate      {95.2:>14.1f}% │
│ Avg Confidence    {87.3:>14.1f}% │
└─────────────────────────────────────┘

{self.ui.render_card("Live Tracking", f"{len(self.mock_live_conversations)} conversations active")}

┌─────────────────────────────────────┐
│ Recent Attribution Activity         │
├─────────────────────────────────────┤
│ OpenAI            2m ago      $0.23 │
│ Climate discussion        87% conf  │
├─────────────────────────────────────┤
│ Claude           15m ago      $0.15 │
│ Python programming        92% conf  │
├─────────────────────────────────────┤
│ OpenAI            1h ago      $0.08 │
│ Recipe recommendations    76% conf  │
└─────────────────────────────────────┘

{self.ui.render_button("View All Activity")}

┌─────────────────────────────────────┐
│ 📊 Analytics  💳 Payments  ⚙️ Settings │
└─────────────────────────────────────┘"""

    def render_live_tracking_screen(self) -> str:
        """Render live conversation tracking"""
        return f"""
{self.ui.render_header("Live Tracking", has_back=True)}

{self.ui.render_card("Active Conversations", f"{len(self.mock_live_conversations)} in progress")}

┌─────────────────────────────────────┐
│ Real-time Attribution Tracking     │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ 🟢 OpenAI GPT-4                    │
├─────────────────────────────────────┤
│ Status: Processing response         │
│ Estimated Value: $0.12              │
│ Confidence: Calculating...          │
│ Time: 30 seconds ago                │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ 🟡 Claude Sonnet                   │
├─────────────────────────────────────┤
│ Status: Analyzing attribution       │
│ Estimated Value: $0.18              │
│ Confidence: 89%                     │
│ Time: 1 minute ago                  │
└─────────────────────────────────────┘

{self.ui.render_button("Refresh")}

┌─────────────────────────────────────┐
│ Auto-refresh: ON     Last: 2s ago   │
└─────────────────────────────────────┘"""

    def render_analytics_screen(self) -> str:
        """Render analytics dashboard"""
        return f"""
{self.ui.render_header("Analytics", has_back=True)}

{self.ui.render_card("7-Day Performance", "Trending upward 📈")}

┌─────────────────────────────────────┐
│ Earnings Breakdown                  │
├─────────────────────────────────────┤
{self.ui.render_progress_bar(67.5, "Direct Attribution")}
{self.ui.render_progress_bar(15.0, "UBA Share")}
{self.ui.render_progress_bar(12.5, "Commons Fund")}
{self.ui.render_progress_bar(5.0, "Platform Fees")}
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ Platform Performance               │
├─────────────────────────────────────┤
│ OpenAI            185 conv    $67.23│
│ Claude             89 conv    $35.45│
│ Others             68 conv    $24.77│
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ Confidence Trends                  │
├─────────────────────────────────────┤
│ High (>80%)       67%     📈 +12%   │
│ Medium (50-80%)   28%     📊 stable │
│ Low (<50%)         5%     📉 -3%    │
└─────────────────────────────────────┘

{self.ui.render_button("Detailed Report")}"""

    def render_payments_screen(self) -> str:
        """Render payments dashboard"""
        user = self.mock_user
        return f"""
{self.ui.render_header("Payments", has_back=True)}

{self.ui.render_card("Available Balance", f"${user['total_earnings']:.2f}", highlight=True)}

┌─────────────────────────────────────┐
│ Payout Information                  │
├─────────────────────────────────────┤
│ Method: {user['payout_method']:<26} │
│ Threshold: $10.00                   │
│ Next Payout: Available Now          │
│ Processing Time: 1-3 business days  │
└─────────────────────────────────────┘

{self.ui.render_button("Request Payout", primary=True)}

┌─────────────────────────────────────┐
│ Recent Transactions                 │
├─────────────────────────────────────┤
│ Mar 15  Payout Sent      -$85.30   │
│ Mar 10  Attribution      +$12.45   │
│ Mar 08  Attribution      +$8.75    │
│ Mar 05  Attribution      +$15.20   │
│ Mar 01  UBA Distribution +$4.50    │
└─────────────────────────────────────┘

{self.ui.render_button("Transaction History")}

┌─────────────────────────────────────┐
│ Payment Settings                    │
├─────────────────────────────────────┤
│ • Change Payout Method              │
│ • Update Threshold                  │
│ • Tax Documents                     │
│ • Payment Notifications             │
└─────────────────────────────────────┘"""

    def render_settings_screen(self) -> str:
        """Render settings screen"""
        user = self.mock_user
        return f"""
{self.ui.render_header("Settings", has_back=True)}

┌─────────────────────────────────────┐
│ {user['avatar']} {user['name']:<30} │
├─────────────────────────────────────┤
│ {user['email']:<35} │
│ Member since {user['member_since']}           │
│ Status: ✅ {user['verification_status'].title():<25} │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ Account Settings                    │
├─────────────────────────────────────┤
│ • Profile Information               │
│ • Privacy Preferences               │
│ • Notification Settings             │
│ • Connected Platforms               │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ Attribution Settings                │
├─────────────────────────────────────┤
│ • Attribution Tracking: ON          │
│ • UBA Participation: ON             │
│ • Cross-platform Sync: ON           │
│ • Real-time Notifications: ON       │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ Privacy & Security                  │
├─────────────────────────────────────┤
│ • Data Usage Consent                │
│ • Export My Data                    │
│ • Delete Account                    │
│ • Security Settings                 │
└─────────────────────────────────────┘

{self.ui.render_button("Save Changes", primary=True)}

┌─────────────────────────────────────┐
│ Help & Support                      │
├─────────────────────────────────────┤
│ • FAQ & Documentation               │
│ • Contact Support                   │
│ • Report an Issue                   │
│ • App Version: 1.0.0                │
└─────────────────────────────────────┘"""

    def render_notification_popup(self, notification: Dict[str, Any]) -> str:
        """Render notification popup"""
        return f"""
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ 🔔 New Attribution                ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃ Platform: {notification.get('platform', 'Unknown'):<26} ┃
┃ Amount: {notification.get('amount', '$0.00'):<28} ┃
┃ Confidence: {notification.get('confidence', '0%'):<24} ┃
┃                                   ┃
┃ {notification.get('message', 'Attribution recorded'):<35} ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

          [Tap to dismiss]"""

    def show_screen(self):
        """Display current screen"""
        print("\033[2J\033[H")  # Clear screen and move cursor to top

        if self.state.current_screen == "splash":
            print(self.render_splash_screen())
        elif self.state.current_screen == "login":
            print(self.render_login_screen())
        elif self.state.current_screen == "dashboard":
            print(self.render_dashboard_screen())
        elif self.state.current_screen == "live_tracking":
            print(self.render_live_tracking_screen())
        elif self.state.current_screen == "analytics":
            print(self.render_analytics_screen())
        elif self.state.current_screen == "payments":
            print(self.render_payments_screen())
        elif self.state.current_screen == "settings":
            print(self.render_settings_screen())

        # Show pending notifications
        if self.state.notifications:
            print("\n" + self.render_notification_popup(self.state.notifications[0]))

    def handle_input(self, user_input: str):
        """Handle user input based on current screen"""
        current = self.state.current_screen

        if current == "splash":
            if "1" in user_input or "start" in user_input.lower():
                self.state.navigate_to("login")
            elif "2" in user_input or "login" in user_input.lower():
                self.state.navigate_to("login")

        elif current == "login":
            if "back" in user_input.lower() or "b" in user_input:
                self.state.go_back()
            elif "login" in user_input.lower() or "sign" in user_input.lower():
                # Simulate successful login
                self.state.user = self.mock_user
                self.state.navigate_to("dashboard")
                # Add welcome notification
                self.add_notification(
                    {
                        "platform": "UATP",
                        "amount": "+$2.45",
                        "confidence": "Welcome!",
                        "message": "You earned while away!",
                    }
                )

        elif current == "dashboard":
            if "1" in user_input or "activity" in user_input.lower():
                self.state.navigate_to("live_tracking")
            elif "2" in user_input or "analytics" in user_input.lower():
                self.state.navigate_to("analytics")
            elif "3" in user_input or "payments" in user_input.lower():
                self.state.navigate_to("payments")
            elif "4" in user_input or "settings" in user_input.lower():
                self.state.navigate_to("settings")
            elif "live" in user_input.lower() or "tracking" in user_input.lower():
                self.state.navigate_to("live_tracking")

        elif current in ["live_tracking", "analytics", "payments", "settings"]:
            if "back" in user_input.lower() or "b" in user_input:
                self.state.go_back()
            elif current == "live_tracking" and "refresh" in user_input.lower():
                # Simulate new attribution
                self.add_notification(
                    {
                        "platform": "OpenAI",
                        "amount": "+$0.34",
                        "confidence": "91%",
                        "message": "New attribution from code review",
                    }
                )

        # Handle notifications
        if self.state.notifications and (
            "tap" in user_input.lower() or "dismiss" in user_input.lower()
        ):
            self.state.notifications.pop(0)

    def add_notification(self, notification: Dict[str, Any]):
        """Add a new notification"""
        self.state.notifications.append(notification)
        # Update real-time data
        if "amount" in notification and notification["amount"].startswith("+$"):
            amount_str = notification["amount"][2:]  # Remove '+$'
            try:
                amount = Decimal(amount_str)
                self.state.real_time_data["earnings_today"] += amount
                self.state.real_time_data["attributions_today"] += 1
            except:
                pass

    def simulate_real_time_data(self):
        """Simulate real-time attribution updates"""
        import random

        # Randomly add new attributions
        if random.random() < 0.3:  # 30% chance
            platforms = ["OpenAI", "Claude", "Cohere"]
            amounts = [0.05, 0.12, 0.23, 0.34, 0.45]
            confidences = [76, 82, 87, 91, 94]

            self.add_notification(
                {
                    "platform": random.choice(platforms),
                    "amount": f"+${random.choice(amounts):.2f}",
                    "confidence": f"{random.choice(confidences)}%",
                    "message": "New attribution recorded",
                }
            )

    async def run(self):
        """Main app loop"""
        print("🚀 UATP Mobile App Prototype")
        print("=" * 40)
        print("Commands:")
        print("- Type numbers (1, 2, 3, 4) to navigate")
        print("- Type 'back' or 'b' to go back")
        print("- Type 'refresh' in live tracking")
        print("- Type 'tap' or 'dismiss' to close notifications")
        print("- Type 'quit' to exit")
        print("=" * 40)

        while True:
            self.show_screen()

            # Simulate real-time updates occasionally
            self.simulate_real_time_data()

            print("\n" + "─" * 39)
            user_input = input("Action: ").strip()

            if user_input.lower() in ["quit", "exit", "q"]:
                print("\n👋 Thanks for using UATP Mobile!")
                break

            self.handle_input(user_input)

            # Small delay for better UX
            await asyncio.sleep(0.1)


# Demo launcher
if __name__ == "__main__":

    async def main():
        app = MobileApp()
        await app.run()

    print(
        """
    ⚡ UATP Mobile App Prototype ⚡

    This prototype demonstrates:
    • Mobile-optimized UI/UX design
    • Real-time attribution tracking
    • Cross-platform conversation monitoring
    • Earnings dashboard and analytics
    • Payment management interface
    • Privacy and consent controls

    Navigate using numbers or keywords!
    """
    )

    asyncio.run(main())
