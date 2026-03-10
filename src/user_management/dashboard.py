"""
User Dashboard Implementation
Real-time attribution tracking and earnings dashboard
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from ..integrations.ai_platform_framework import AIAttributionOrchestrator
from ..integrations.openai_attribution import AttributionResult
from .user_service import UserProfile, UserService

logger = logging.getLogger(__name__)


@dataclass
class AttributionActivity:
    """Individual attribution activity record"""

    activity_id: str
    user_id: str
    timestamp: datetime
    platform: str
    model: str
    conversation_id: str
    prompt_preview: str
    attribution_amount: Decimal
    confidence_score: float
    attribution_breakdown: Dict[str, Any]


@dataclass
class DashboardMetrics:
    """Dashboard metrics and analytics"""

    total_earnings: Decimal
    daily_earnings: Decimal
    weekly_earnings: Decimal
    monthly_earnings: Decimal
    total_attributions: int
    average_confidence: float
    top_platforms: List[Dict[str, Any]]
    earning_trends: List[Dict[str, Any]]
    attribution_sources: Dict[str, float]


@dataclass
class NotificationPreferences:
    """User notification preferences"""

    email_notifications: bool = True
    push_notifications: bool = True
    attribution_alerts: bool = True
    payout_alerts: bool = True
    weekly_summaries: bool = True
    threshold_alerts: bool = True
    minimum_amount: Decimal = field(default_factory=lambda: Decimal("0.10"))


class UserDashboard:
    """Complete user dashboard implementation"""

    def __init__(
        self, user_service: UserService, ai_orchestrator: AIAttributionOrchestrator
    ):
        self.user_service = user_service
        self.ai_orchestrator = ai_orchestrator
        self.attribution_activities: Dict[str, List[AttributionActivity]] = {}
        self.user_notifications: Dict[str, List[Dict[str, Any]]] = {}
        self.notification_preferences: Dict[str, NotificationPreferences] = {}

    async def record_attribution_activity(
        self,
        user_id: str,
        platform: str,
        model: str,
        conversation_id: str,
        prompt: str,
        attribution_result: AttributionResult,
    ) -> str:
        """Record attribution activity for the dashboard"""

        activity_id = f"activity_{int(datetime.now().timestamp())}_{user_id[-6:]}"

        activity = AttributionActivity(
            activity_id=activity_id,
            user_id=user_id,
            timestamp=datetime.now(timezone.utc),
            platform=platform,
            model=model,
            conversation_id=conversation_id,
            prompt_preview=prompt[:100] + "..." if len(prompt) > 100 else prompt,
            attribution_amount=attribution_result.total_value,
            confidence_score=max(attribution_result.confidence_scores.values())
            if attribution_result.confidence_scores
            else 0.0,
            attribution_breakdown=attribution_result.attribution_breakdown,
        )

        # Store activity
        if user_id not in self.attribution_activities:
            self.attribution_activities[user_id] = []

        self.attribution_activities[user_id].append(activity)

        # Update user profile with earnings
        user_profile = await self.user_service.get_user_profile(user_id)
        if user_profile:
            user_profile.total_earnings += attribution_result.total_value
            user_profile.total_attributions += 1

            # Update average confidence
            total_confidence = user_profile.average_confidence * (
                user_profile.total_attributions - 1
            )
            user_profile.average_confidence = (
                total_confidence + activity.confidence_score
            ) / user_profile.total_attributions

        # Check for notification triggers
        await self._check_notification_triggers(user_id, activity)

        logger.info(f"Attribution activity recorded: {activity_id}")
        return activity_id

    async def get_dashboard_data(self, user_id: str) -> Dict[str, Any]:
        """Get complete dashboard data for a user"""

        user_profile = await self.user_service.get_user_profile(user_id)
        if not user_profile:
            return {"error": "User not found"}

        # Get recent activities
        activities = self.attribution_activities.get(user_id, [])
        recent_activities = sorted(activities, key=lambda x: x.timestamp, reverse=True)[
            :10
        ]

        # Calculate metrics
        metrics = await self._calculate_dashboard_metrics(user_id, activities)

        # Get notifications
        notifications = self.user_notifications.get(user_id, [])
        unread_notifications = [n for n in notifications if not n.get("read", False)]

        # Get onboarding status
        onboarding_status = await self.user_service.get_user_onboarding_status(user_id)

        return {
            "user_profile": {
                "user_id": user_profile.user_id,
                "username": user_profile.username,
                "full_name": user_profile.full_name,
                "total_earnings": float(user_profile.total_earnings),
                "total_attributions": user_profile.total_attributions,
                "average_confidence": user_profile.average_confidence,
                "verification_status": user_profile.verification_status.value,
                "payout_method": user_profile.payout_method.value
                if user_profile.payout_method
                else None,
                "member_since": user_profile.created_at.isoformat(),
            },
            "metrics": metrics,
            "recent_activities": [
                {
                    "activity_id": activity.activity_id,
                    "timestamp": activity.timestamp.isoformat(),
                    "platform": activity.platform,
                    "model": activity.model,
                    "prompt_preview": activity.prompt_preview,
                    "attribution_amount": float(activity.attribution_amount),
                    "confidence_score": activity.confidence_score,
                }
                for activity in recent_activities
            ],
            "notifications": {
                "unread_count": len(unread_notifications),
                "recent_notifications": notifications[-5:],  # Last 5 notifications
            },
            "onboarding_status": onboarding_status,
            "quick_actions": self._get_quick_actions(user_profile),
        }

    async def _calculate_dashboard_metrics(
        self, user_id: str, activities: List[AttributionActivity]
    ) -> DashboardMetrics:
        """Calculate dashboard metrics"""

        now = datetime.now(timezone.utc)

        # Time-based earnings
        daily_earnings = sum(
            activity.attribution_amount
            for activity in activities
            if activity.timestamp >= now - timedelta(days=1)
        )

        weekly_earnings = sum(
            activity.attribution_amount
            for activity in activities
            if activity.timestamp >= now - timedelta(weeks=1)
        )

        monthly_earnings = sum(
            activity.attribution_amount
            for activity in activities
            if activity.timestamp >= now - timedelta(days=30)
        )

        total_earnings = sum(activity.attribution_amount for activity in activities)

        # Platform breakdown
        platform_earnings = {}
        for activity in activities:
            if activity.platform not in platform_earnings:
                platform_earnings[activity.platform] = {
                    "count": 0,
                    "earnings": Decimal("0"),
                }
            platform_earnings[activity.platform]["count"] += 1
            platform_earnings[activity.platform]["earnings"] += (
                activity.attribution_amount
            )

        top_platforms = [
            {
                "platform": platform,
                "earnings": float(data["earnings"]),
                "count": data["count"],
                "percentage": float(data["earnings"] / total_earnings * 100)
                if total_earnings > 0
                else 0,
            }
            for platform, data in sorted(
                platform_earnings.items(), key=lambda x: x[1]["earnings"], reverse=True
            )
        ]

        # Earning trends (last 7 days)
        earning_trends = []
        for i in range(7):
            date = now - timedelta(days=i)
            day_earnings = sum(
                activity.attribution_amount
                for activity in activities
                if activity.timestamp.date() == date.date()
            )
            earning_trends.append(
                {"date": date.date().isoformat(), "earnings": float(day_earnings)}
            )

        earning_trends.reverse()  # Chronological order

        # Attribution sources (simplified)
        attribution_sources = {
            "Direct Attribution": 70.0,
            "Commons Fund": 15.0,
            "UBA Distribution": 15.0,
        }

        return DashboardMetrics(
            total_earnings=total_earnings,
            daily_earnings=daily_earnings,
            weekly_earnings=weekly_earnings,
            monthly_earnings=monthly_earnings,
            total_attributions=len(activities),
            average_confidence=sum(a.confidence_score for a in activities)
            / len(activities)
            if activities
            else 0.0,
            top_platforms=top_platforms,
            earning_trends=earning_trends,
            attribution_sources=attribution_sources,
        )

    def _get_quick_actions(self, user_profile: UserProfile) -> List[Dict[str, Any]]:
        """Get quick actions for the user"""

        actions = []

        # Onboarding actions
        if user_profile.verification_status.value != "verified":
            actions.append(
                {
                    "type": "verification",
                    "title": "Complete Identity Verification",
                    "description": "Verify your identity to enable full features",
                    "priority": "high",
                }
            )

        if not user_profile.payout_method:
            actions.append(
                {
                    "type": "payout",
                    "title": "Set Up Payout Method",
                    "description": "Configure how you want to receive earnings",
                    "priority": "medium",
                }
            )

        # Earning-related actions
        if user_profile.total_earnings >= user_profile.payout_threshold:
            actions.append(
                {
                    "type": "payout_available",
                    "title": "Payout Available",
                    "description": f"${user_profile.total_earnings} ready for payout",
                    "priority": "high",
                }
            )

        # Engagement actions
        actions.append(
            {
                "type": "connect_platform",
                "title": "Connect AI Platform",
                "description": "Connect more AI platforms to increase earnings",
                "priority": "low",
            }
        )

        return actions

    async def _check_notification_triggers(
        self, user_id: str, activity: AttributionActivity
    ):
        """Check if activity triggers notifications"""

        preferences = self.notification_preferences.get(
            user_id, NotificationPreferences()
        )

        notifications = []

        # Attribution threshold notification
        if (
            preferences.attribution_alerts
            and activity.attribution_amount >= preferences.minimum_amount
        ):
            notifications.append(
                {
                    "type": "attribution_earned",
                    "title": "Attribution Earned",
                    "message": f"You earned ${activity.attribution_amount:.4f} from {activity.platform}",
                    "timestamp": activity.timestamp.isoformat(),
                    "read": False,
                }
            )

        # High confidence notification
        if activity.confidence_score >= 0.9:
            notifications.append(
                {
                    "type": "high_confidence",
                    "title": "High Confidence Attribution",
                    "message": f"Attribution with {activity.confidence_score:.1%} confidence",
                    "timestamp": activity.timestamp.isoformat(),
                    "read": False,
                }
            )

        # Store notifications
        if user_id not in self.user_notifications:
            self.user_notifications[user_id] = []

        self.user_notifications[user_id].extend(notifications)

        # Keep only last 50 notifications
        self.user_notifications[user_id] = self.user_notifications[user_id][-50:]

    async def get_attribution_history(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
        platform_filter: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get detailed attribution history"""

        activities = self.attribution_activities.get(user_id, [])

        # Apply filters
        filtered_activities = activities

        if platform_filter:
            filtered_activities = [
                a for a in filtered_activities if a.platform == platform_filter
            ]

        if date_from:
            filtered_activities = [
                a for a in filtered_activities if a.timestamp >= date_from
            ]

        if date_to:
            filtered_activities = [
                a for a in filtered_activities if a.timestamp <= date_to
            ]

        # Sort by timestamp (newest first)
        filtered_activities.sort(key=lambda x: x.timestamp, reverse=True)

        # Apply pagination
        paginated_activities = filtered_activities[offset : offset + limit]

        return {
            "activities": [
                {
                    "activity_id": activity.activity_id,
                    "timestamp": activity.timestamp.isoformat(),
                    "platform": activity.platform,
                    "model": activity.model,
                    "conversation_id": activity.conversation_id,
                    "prompt_preview": activity.prompt_preview,
                    "attribution_amount": float(activity.attribution_amount),
                    "confidence_score": activity.confidence_score,
                    "attribution_breakdown": activity.attribution_breakdown,
                }
                for activity in paginated_activities
            ],
            "pagination": {
                "total": len(filtered_activities),
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < len(filtered_activities),
            },
            "summary": {
                "total_amount": float(
                    sum(a.attribution_amount for a in filtered_activities)
                ),
                "average_confidence": sum(
                    a.confidence_score for a in filtered_activities
                )
                / len(filtered_activities)
                if filtered_activities
                else 0.0,
                "platform_breakdown": self._get_platform_breakdown(filtered_activities),
            },
        }

    def _get_platform_breakdown(
        self, activities: List[AttributionActivity]
    ) -> Dict[str, Any]:
        """Get platform breakdown for activities"""

        breakdown = {}
        for activity in activities:
            if activity.platform not in breakdown:
                breakdown[activity.platform] = {"count": 0, "total_amount": 0.0}
            breakdown[activity.platform]["count"] += 1
            breakdown[activity.platform]["total_amount"] += float(
                activity.attribution_amount
            )

        return breakdown

    async def set_notification_preferences(
        self, user_id: str, preferences: NotificationPreferences
    ) -> Dict[str, Any]:
        """Set user notification preferences"""

        self.notification_preferences[user_id] = preferences

        return {"success": True, "message": "Notification preferences updated"}

    async def mark_notifications_read(
        self, user_id: str, notification_ids: List[str] = None
    ) -> Dict[str, Any]:
        """Mark notifications as read"""

        if user_id not in self.user_notifications:
            return {"success": False, "error": "No notifications found"}

        notifications = self.user_notifications[user_id]

        if notification_ids:
            # Mark specific notifications as read
            for notification in notifications:
                if notification.get("id") in notification_ids:
                    notification["read"] = True
        else:
            # Mark all notifications as read
            for notification in notifications:
                notification["read"] = True

        return {"success": True, "message": "Notifications marked as read"}

    async def get_earnings_analytics(
        self, user_id: str, period: str = "month"
    ) -> Dict[str, Any]:
        """Get detailed earnings analytics"""

        activities = self.attribution_activities.get(user_id, [])

        # Calculate period
        now = datetime.now(timezone.utc)
        if period == "week":
            start_date = now - timedelta(weeks=1)
        elif period == "month":
            start_date = now - timedelta(days=30)
        elif period == "quarter":
            start_date = now - timedelta(days=90)
        else:
            start_date = now - timedelta(days=365)

        period_activities = [a for a in activities if a.timestamp >= start_date]

        # Calculate analytics
        analytics = {
            "period": period,
            "total_earnings": float(
                sum(a.attribution_amount for a in period_activities)
            ),
            "total_attributions": len(period_activities),
            "average_per_attribution": float(
                sum(a.attribution_amount for a in period_activities)
                / len(period_activities)
            )
            if period_activities
            else 0.0,
            "confidence_distribution": self._get_confidence_distribution(
                period_activities
            ),
            "platform_performance": self._get_platform_performance(period_activities),
            "daily_breakdown": self._get_daily_breakdown(
                period_activities, start_date, now
            ),
            "growth_metrics": self._calculate_growth_metrics(activities, start_date),
        }

        return analytics

    def _get_confidence_distribution(
        self, activities: List[AttributionActivity]
    ) -> Dict[str, int]:
        """Get confidence score distribution"""

        distribution = {"high": 0, "medium": 0, "low": 0}

        for activity in activities:
            if activity.confidence_score >= 0.8:
                distribution["high"] += 1
            elif activity.confidence_score >= 0.5:
                distribution["medium"] += 1
            else:
                distribution["low"] += 1

        return distribution

    def _get_platform_performance(
        self, activities: List[AttributionActivity]
    ) -> List[Dict[str, Any]]:
        """Get platform performance metrics"""

        platform_data = {}
        for activity in activities:
            if activity.platform not in platform_data:
                platform_data[activity.platform] = {
                    "count": 0,
                    "total_earnings": Decimal("0"),
                    "confidence_scores": [],
                }

            platform_data[activity.platform]["count"] += 1
            platform_data[activity.platform]["total_earnings"] += (
                activity.attribution_amount
            )
            platform_data[activity.platform]["confidence_scores"].append(
                activity.confidence_score
            )

        performance = []
        for platform, data in platform_data.items():
            avg_confidence = sum(data["confidence_scores"]) / len(
                data["confidence_scores"]
            )
            performance.append(
                {
                    "platform": platform,
                    "attributions": data["count"],
                    "total_earnings": float(data["total_earnings"]),
                    "avg_earnings": float(data["total_earnings"] / data["count"]),
                    "avg_confidence": avg_confidence,
                }
            )

        return sorted(performance, key=lambda x: x["total_earnings"], reverse=True)

    def _get_daily_breakdown(
        self,
        activities: List[AttributionActivity],
        start_date: datetime,
        end_date: datetime,
    ) -> List[Dict[str, Any]]:
        """Get daily earnings breakdown"""

        daily_data = {}
        current_date = start_date

        # Initialize all days with zero
        while current_date <= end_date:
            daily_data[current_date.date()] = {"earnings": Decimal("0"), "count": 0}
            current_date += timedelta(days=1)

        # Populate with actual data
        for activity in activities:
            date_key = activity.timestamp.date()
            if date_key in daily_data:
                daily_data[date_key]["earnings"] += activity.attribution_amount
                daily_data[date_key]["count"] += 1

        return [
            {
                "date": date.isoformat(),
                "earnings": float(data["earnings"]),
                "attributions": data["count"],
            }
            for date, data in sorted(daily_data.items())
        ]

    def _calculate_growth_metrics(
        self, activities: List[AttributionActivity], period_start: datetime
    ) -> Dict[str, Any]:
        """Calculate growth metrics"""

        now = datetime.now(timezone.utc)

        # Current period
        current_period_activities = [
            a for a in activities if a.timestamp >= period_start
        ]
        current_earnings = sum(a.attribution_amount for a in current_period_activities)

        # Previous period
        period_length = now - period_start
        previous_period_start = period_start - period_length
        previous_period_activities = [
            a for a in activities if previous_period_start <= a.timestamp < period_start
        ]
        previous_earnings = sum(
            a.attribution_amount for a in previous_period_activities
        )

        # Calculate growth
        earnings_growth = 0.0
        if previous_earnings > 0:
            earnings_growth = float(
                (current_earnings - previous_earnings) / previous_earnings * 100
            )

        attribution_growth = 0.0
        if len(previous_period_activities) > 0:
            attribution_growth = (
                (len(current_period_activities) - len(previous_period_activities))
                / len(previous_period_activities)
                * 100
            )

        return {
            "earnings_growth_percent": earnings_growth,
            "attribution_growth_percent": attribution_growth,
            "current_period_earnings": float(current_earnings),
            "previous_period_earnings": float(previous_earnings),
            "current_period_attributions": len(current_period_activities),
            "previous_period_attributions": len(previous_period_activities),
        }


# Factory function
def create_user_dashboard(
    user_service: UserService, ai_orchestrator: AIAttributionOrchestrator
) -> UserDashboard:
    """Create a user dashboard instance"""
    return UserDashboard(user_service, ai_orchestrator)


# Example usage
if __name__ == "__main__":

    async def demo_dashboard():
        """Demonstrate the user dashboard"""

        from ..integrations.ai_platform_framework import create_ai_orchestrator
        from .user_service import create_user_service

        user_service = create_user_service()
        ai_orchestrator = create_ai_orchestrator()
        dashboard = create_user_dashboard(user_service, ai_orchestrator)

        # Create a test user
        user_result = await user_service.register_user(
            email="test@example.com",
            username="testuser",
            password="TestPass123!",
            full_name="Test User",
        )

        if user_result["success"]:
            user_id = user_result["user_id"]

            # Simulate some attribution activities
            from decimal import Decimal

            from ..integrations.openai_attribution import AttributionResult

            mock_attribution = AttributionResult(
                total_value=Decimal("0.25"),
                direct_attributions={"source1": Decimal("0.15")},
                commons_allocation=Decimal("0.05"),
                uba_allocation=Decimal("0.05"),
                confidence_scores={"source1": 0.85},
                attribution_breakdown={
                    "platform": "openai",
                    "model": "gpt-4",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )

            # Record activities
            await dashboard.record_attribution_activity(
                user_id=user_id,
                platform="openai",
                model="gpt-4",
                conversation_id="test_conv_1",
                prompt="What is machine learning?",
                attribution_result=mock_attribution,
            )

            # Get dashboard data
            dashboard_data = await dashboard.get_dashboard_data(user_id)
            print("Dashboard Data:", dashboard_data)

            # Get earnings analytics
            analytics = await dashboard.get_earnings_analytics(user_id, "month")
            print("Earnings Analytics:", analytics)

    asyncio.run(demo_dashboard())
