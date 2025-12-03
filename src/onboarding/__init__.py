"""
UATP Capsule Engine Onboarding System

A comprehensive, frictionless client onboarding experience that makes
UATP accessible to everyone - from non-technical users to enterprise developers.

Core Philosophy: "Things should be intuitive - easy for the average person to do what they're trying to do."
"""

from .onboarding_orchestrator import OnboardingOrchestrator
from .setup_wizard import InteractiveSetupWizard
from .integration_manager import IntegrationManager
from .health_monitor import SystemHealthMonitor
from .support_assistant import SupportAssistant

__all__ = [
    "OnboardingOrchestrator",
    "InteractiveSetupWizard",
    "IntegrationManager",
    "SystemHealthMonitor",
    "SupportAssistant",
]
