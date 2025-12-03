"""
Web Interface Components for UATP Onboarding

Provides interactive web-based onboarding interface with visual progress,
real-time feedback, and intuitive user flows. Built using modern web
technologies for maximum accessibility and user experience.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path

from quart import Blueprint, render_template_string, jsonify, request, websocket
from quart_cors import cors

from .onboarding_orchestrator import OnboardingOrchestrator, UserType, OnboardingStage
from .health_monitor import SystemHealthMonitor
from .support_assistant import SupportAssistant, IssueType

logger = logging.getLogger(__name__)


def create_onboarding_blueprint() -> Blueprint:
    """Create onboarding web interface blueprint"""

    bp = Blueprint("onboarding", __name__, url_prefix="/onboarding")
    cors(
        bp,
        allow_origin=[
            "http://localhost:3000",
            "http://localhost:3001",
            "http://localhost:3004",
            "http://127.0.0.1:3000",
        ],
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-API-Key"],
        allow_credentials=True,
    )

    # Initialize components
    orchestrator = OnboardingOrchestrator()
    health_monitor = SystemHealthMonitor()
    support_assistant = SupportAssistant()

    @bp.route("/")
    async def onboarding_home():
        """Main onboarding interface"""
        return await render_template_string(ONBOARDING_HTML_TEMPLATE)

    @bp.route("/api/start", methods=["POST", "OPTIONS"])
    async def start_onboarding():
        """Start onboarding process"""
        if request.method == "OPTIONS":
            return "", 200

        try:
            data = await request.get_json()
            user_id = data.get("user_id", f"user_{int(datetime.now().timestamp())}")
            preferences = data.get("preferences", {})

            progress = await orchestrator.start_onboarding(user_id, preferences)

            return jsonify(
                {
                    "success": True,
                    "progress": orchestrator.serialize_progress(progress),
                    "next_step": {
                        "stage": progress.current_stage.value,
                        "title": _get_stage_title(progress.current_stage),
                        "description": _get_stage_description(
                            progress.current_stage, progress.user_type
                        ),
                    },
                }
            )
        except Exception as e:
            logger.error(f"Failed to start onboarding: {e}")
            return jsonify({"success": False, "error": str(e)}), 500

    @bp.route("/api/continue", methods=["POST", "OPTIONS"])
    async def continue_onboarding():
        """Continue onboarding to next step"""
        if request.method == "OPTIONS":
            return "", 200

        try:
            data = await request.get_json()
            user_id = data.get("user_id")
            step_data = data.get("step_data", {})

            if not user_id:
                return jsonify({"success": False, "error": "user_id required"}), 400

            progress = await orchestrator.continue_onboarding(user_id, step_data)

            return jsonify(
                {
                    "success": True,
                    "progress": orchestrator.serialize_progress(progress),
                    "next_step": {
                        "stage": progress.current_stage.value,
                        "title": _get_stage_title(progress.current_stage),
                        "description": _get_stage_description(
                            progress.current_stage, progress.user_type
                        ),
                    }
                    if progress.current_stage != OnboardingStage.COMPLETE
                    else None,
                }
            )
        except Exception as e:
            logger.error(f"Failed to continue onboarding: {e}")
            return jsonify({"success": False, "error": str(e)}), 500

    @bp.route("/api/status/<user_id>", methods=["GET", "OPTIONS"])
    async def get_onboarding_status(user_id):
        """Get current onboarding status"""
        if request.method == "OPTIONS":
            return "", 200

        try:
            progress = await orchestrator.get_onboarding_status(user_id)

            if not progress:
                return jsonify({"success": False, "error": "User not found"}), 404

            return jsonify(
                {"success": True, "progress": orchestrator.serialize_progress(progress)}
            )
        except Exception as e:
            logger.error(f"Failed to get onboarding status: {e}")
            return jsonify({"success": False, "error": str(e)}), 500

    @bp.route("/api/health", methods=["GET", "OPTIONS"])
    async def get_system_health():
        """Get system health for dashboard"""
        if request.method == "OPTIONS":
            return "", 200

        try:
            health = await health_monitor.get_system_health()
            return jsonify(
                {
                    "success": True,
                    "health": {
                        "overall_status": health.overall_status.value
                        if hasattr(health.overall_status, "value")
                        else str(health.overall_status),
                        "score": getattr(health, "score", 0),
                        "summary": getattr(health, "summary", "System healthy"),
                    },
                }
            )
        except Exception as e:
            logger.error(f"Failed to get system health: {e}")
            return jsonify({"success": False, "error": str(e)}), 500

    @bp.route("/api/support", methods=["POST", "OPTIONS"])
    async def get_support():
        """Get contextual support"""
        if request.method == "OPTIONS":
            return "", 200

        try:
            data = await request.get_json()
            user_id = data.get("user_id")
            issue_type = data.get("issue_type")
            message = data.get("message")

            # Get user progress for context
            progress = (
                await orchestrator.get_onboarding_status(user_id) if user_id else None
            )

            support_response = await support_assistant.get_contextual_help(
                user_progress=progress, issue_type=issue_type, user_message=message
            )

            return jsonify(
                {
                    "success": True,
                    "support": {
                        "message": getattr(
                            support_response, "message", "Support available"
                        ),
                        "issue_type": getattr(
                            support_response, "issue_type", issue_type or "general"
                        ),
                        "immediate_actions": getattr(
                            support_response, "immediate_actions", []
                        ),
                        "resources": getattr(support_response, "resources", []),
                    },
                }
            )
        except Exception as e:
            logger.error(f"Failed to get support: {e}")
            return jsonify({"success": False, "error": str(e)}), 500

    @bp.route("/api/platforms", methods=["GET", "OPTIONS"])
    async def get_available_platforms():
        """Get available AI platforms"""
        if request.method == "OPTIONS":
            return "", 200

        try:
            platforms = await orchestrator.integration_manager.get_available_platforms()
            discovered = (
                await orchestrator.integration_manager.auto_discover_integrations()
            )

            return jsonify(
                {
                    "success": True,
                    "platforms": {
                        platform_id: {
                            "name": getattr(platform_info, "name", platform_id),
                            "description": getattr(
                                platform_info,
                                "description",
                                f"{platform_id} AI platform",
                            ),
                            "available": discovered.get(platform_id, False),
                            "estimated_setup_time": getattr(
                                platform_info, "estimated_setup_time", 5
                            ),
                        }
                        for platform_id, platform_info in platforms.items()
                    },
                }
            )
        except Exception as e:
            logger.error(f"Failed to get platforms: {e}")
            return jsonify({"success": False, "error": str(e)}), 500

    @bp.websocket("/ws/progress")
    async def websocket_progress():
        """WebSocket for real-time progress updates"""
        try:
            while True:
                data = await websocket.receive_json()
                user_id = data.get("user_id")

                if user_id:
                    # Send progress update
                    progress = await orchestrator.get_onboarding_status(user_id)
                    if progress:
                        await websocket.send_json(
                            {
                                "type": "progress_update",
                                "data": orchestrator.serialize_progress(progress),
                            }
                        )

                # Send health update
                health = await health_monitor.get_system_health()
                await websocket.send_json(
                    {
                        "type": "health_update",
                        "data": {
                            "status": health.overall_status.value,
                            "score": health.score,
                            "summary": health.summary,
                        },
                    }
                )

                await asyncio.sleep(5)  # Update every 5 seconds

        except Exception as e:
            logger.error(f"WebSocket error: {e}")

    # Helper functions
    def _get_stage_title(stage: OnboardingStage) -> str:
        """Get user-friendly stage title"""
        titles = {
            OnboardingStage.WELCOME: "Welcome to UATP!",
            OnboardingStage.ENVIRONMENT_DETECTION: "Detecting Your Environment",
            OnboardingStage.QUICK_SETUP: "Setting Up Your System",
            OnboardingStage.AI_INTEGRATION: "Connecting AI Platforms",
            OnboardingStage.FIRST_CAPSULE: "Creating Your First Capsule",
            OnboardingStage.SUCCESS_MILESTONE: "Success! You're All Set",
            OnboardingStage.ADVANCED_FEATURES: "Explore Advanced Features",
            OnboardingStage.COMPLETE: "Onboarding Complete",
        }
        return titles.get(stage, "Processing...")

    def _get_stage_description(stage: OnboardingStage, user_type: UserType) -> str:
        """Get user-friendly stage description"""
        descriptions = {
            OnboardingStage.WELCOME: "Let's get you started with AI trust and attribution",
            OnboardingStage.ENVIRONMENT_DETECTION: "We're automatically detecting your setup to optimize configuration",
            OnboardingStage.QUICK_SETUP: "Configuring UATP with smart defaults for your environment",
            OnboardingStage.AI_INTEGRATION: "Connecting to your preferred AI platforms with one-click setup",
            OnboardingStage.FIRST_CAPSULE: "Creating your first UATP capsule with full attribution tracking",
            OnboardingStage.SUCCESS_MILESTONE: "Congratulations! Your UATP system is ready to use",
            OnboardingStage.ADVANCED_FEATURES: "Discover advanced features like governance and analytics",
            OnboardingStage.COMPLETE: "You're all set! Start creating capsules and exploring UATP",
        }
        return descriptions.get(stage, "Processing your request...")

    return bp


# HTML Template for onboarding interface
ONBOARDING_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UATP Onboarding - Get Started in Minutes</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #333;
        }
        
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            width: 90%;
            max-width: 800px;
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
            padding: 2rem;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
            font-weight: 700;
        }
        
        .header p {
            font-size: 1.2rem;
            opacity: 0.9;
        }
        
        .progress-container {
            padding: 1rem 2rem;
            background: #f8f9fa;
            border-bottom: 1px solid #e9ecef;
        }
        
        .progress-bar {
            background: #e9ecef;
            border-radius: 10px;
            height: 8px;
            overflow: hidden;
            margin-bottom: 1rem;
        }
        
        .progress-fill {
            background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%);
            height: 100%;
            width: 0%;
            transition: width 0.5s ease;
        }
        
        .progress-text {
            text-align: center;
            color: #6c757d;
            font-size: 0.9rem;
        }
        
        .content {
            padding: 2rem;
        }
        
        .step-card {
            display: none;
            animation: fadeIn 0.5s ease-in-out;
        }
        
        .step-card.active {
            display: block;
        }
        
        .step-title {
            font-size: 1.8rem;
            font-weight: 600;
            margin-bottom: 1rem;
            color: #2c3e50;
        }
        
        .step-description {
            font-size: 1.1rem;
            color: #6c757d;
            margin-bottom: 2rem;
            line-height: 1.6;
        }
        
        .user-type-selector {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }
        
        .user-type-card {
            border: 2px solid #e9ecef;
            border-radius: 12px;
            padding: 1.5rem;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .user-type-card:hover {
            border-color: #4facfe;
            transform: translateY(-2px);
            box-shadow: 0 8px 16px rgba(79, 172, 254, 0.2);
        }
        
        .user-type-card.selected {
            border-color: #4facfe;
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
        }
        
        .user-type-icon {
            font-size: 3rem;
            margin-bottom: 1rem;
        }
        
        .user-type-title {
            font-size: 1.2rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }
        
        .user-type-desc {
            font-size: 0.9rem;
            opacity: 0.8;
        }
        
        .platform-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }
        
        .platform-card {
            border: 2px solid #e9ecef;
            border-radius: 12px;
            padding: 1.5rem;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .platform-card:hover {
            border-color: #28a745;
            transform: translateY(-2px);
        }
        
        .platform-card.available {
            border-color: #28a745;
            background: #f8fff9;
        }
        
        .platform-card.selected {
            border-color: #28a745;
            background: #28a745;
            color: white;
        }
        
        .platform-status {
            display: inline-block;
            padding: 0.25rem 0.5rem;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: 500;
            margin-bottom: 1rem;
        }
        
        .platform-status.available {
            background: #d4edda;
            color: #155724;
        }
        
        .platform-status.setup-needed {
            background: #fff3cd;
            color: #856404;
        }
        
        .btn {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
            border: none;
            padding: 1rem 2rem;
            border-radius: 8px;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            width: 100%;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 16px rgba(79, 172, 254, 0.3);
        }
        
        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .btn-secondary {
            background: #6c757d;
        }
        
        .btn-success {
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
        }
        
        .success-animation {
            text-align: center;
            padding: 2rem;
        }
        
        .success-icon {
            font-size: 4rem;
            color: #28a745;
            margin-bottom: 1rem;
            animation: bounce 1s ease-in-out infinite alternate;
        }
        
        .loading-spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 2px solid #ffffff;
            border-radius: 50%;
            border-top-color: transparent;
            animation: spin 1s ease-in-out infinite;
            margin-right: 0.5rem;
        }
        
        .health-indicator {
            position: fixed;
            top: 1rem;
            right: 1rem;
            background: white;
            border-radius: 8px;
            padding: 0.5rem 1rem;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .health-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #28a745;
        }
        
        .health-dot.warning { background: #ffc107; }
        .health-dot.critical { background: #dc3545; }
        
        .support-fab {
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            font-size: 1.5rem;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            transition: all 0.3s ease;
        }
        
        .support-fab:hover {
            transform: scale(1.1);
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        @keyframes bounce {
            from { transform: translateY(0px); }
            to { transform: translateY(-10px); }
        }
        
        .hidden {
            display: none !important;
        }
        
        @media (max-width: 768px) {
            .container {
                width: 95%;
                margin: 1rem;
            }
            
            .header h1 {
                font-size: 2rem;
            }
            
            .content {
                padding: 1rem;
            }
            
            .user-type-selector {
                grid-template-columns: 1fr;
            }
            
            .platform-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Welcome to UATP</h1>
            <p>Universal AI Trust Protocol - Get started in minutes</p>
        </div>
        
        <div class="progress-container">
            <div class="progress-bar">
                <div class="progress-fill" id="progressFill"></div>
            </div>
            <div class="progress-text" id="progressText">Step 1 of 5</div>
        </div>
        
        <div class="content">
            <!-- Welcome Step -->
            <div class="step-card active" id="step-welcome">
                <div class="step-title">Choose Your Experience</div>
                <div class="step-description">
                    Tell us about yourself so we can personalize your onboarding experience.
                </div>
                
                <div class="user-type-selector">
                    <div class="user-type-card" data-type="casual_user">
                        <div class="user-type-icon">👋</div>
                        <div class="user-type-title">Just Getting Started</div>
                        <div class="user-type-desc">I want to try UATP with minimal setup</div>
                    </div>
                    
                    <div class="user-type-card" data-type="developer">
                        <div class="user-type-icon">👨‍💻</div>
                        <div class="user-type-title">Developer</div>
                        <div class="user-type-desc">I want to integrate UATP into my applications</div>
                    </div>
                    
                    <div class="user-type-card" data-type="business_user">
                        <div class="user-type-icon">💼</div>
                        <div class="user-type-title">Business User</div>
                        <div class="user-type-desc">I need AI attribution for business use</div>
                    </div>
                    
                    <div class="user-type-card" data-type="researcher">
                        <div class="user-type-icon">🔬</div>
                        <div class="user-type-title">Researcher</div>
                        <div class="user-type-desc">I need transparent AI for research</div>
                    </div>
                    
                    <div class="user-type-card" data-type="enterprise">
                        <div class="user-type-icon">🏢</div>
                        <div class="user-type-title">Enterprise</div>
                        <div class="user-type-desc">I need enterprise-grade AI governance</div>
                    </div>
                </div>
                
                <button class="btn" id="startBtn" disabled>Get Started</button>
            </div>
            
            <!-- Environment Detection Step -->
            <div class="step-card" id="step-environment">
                <div class="step-title">Detecting Your Environment</div>
                <div class="step-description">
                    We're automatically detecting your system configuration to optimize your setup.
                </div>
                
                <div style="text-align: center; padding: 2rem;">
                    <div class="loading-spinner"></div>
                    <div>Analyzing your environment...</div>
                </div>
            </div>
            
            <!-- Platform Selection Step -->
            <div class="step-card" id="step-platforms">
                <div class="step-title">Connect Your AI Platform</div>
                <div class="step-description">
                    Choose your preferred AI platform. We've detected which ones you can connect to immediately.
                </div>
                
                <div class="platform-grid" id="platformGrid">
                    <!-- Platforms will be loaded dynamically -->
                </div>
                
                <button class="btn" id="connectPlatformBtn" disabled>Connect Platform</button>
            </div>
            
            <!-- First Capsule Step -->
            <div class="step-card" id="step-capsule">
                <div class="step-title">Create Your First Capsule</div>
                <div class="step-description">
                    Let's create your first UATP capsule with full attribution tracking.
                </div>
                
                <div style="text-align: center; padding: 2rem;">
                    <div class="loading-spinner"></div>
                    <div>Creating your personalized capsule...</div>
                </div>
            </div>
            
            <!-- Success Step -->
            <div class="step-card" id="step-success">
                <div class="success-animation">
                    <div class="success-icon">🎉</div>
                    <div class="step-title">Success! You're All Set</div>
                    <div class="step-description">
                        Congratulations! Your UATP system is configured and ready to use.
                    </div>
                    
                    <div style="margin: 2rem 0;">
                        <strong>What you've accomplished:</strong>
                        <ul style="text-align: left; margin: 1rem 0;">
                            <li>✅ System configured with optimal settings</li>
                            <li>✅ AI platform connected and tested</li>
                            <li>✅ First capsule created with attribution</li>
                            <li>✅ Ready for production use</li>
                        </ul>
                    </div>
                    
                    <button class="btn btn-success" id="launchDashboardBtn">Launch Dashboard</button>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Health Indicator -->
    <div class="health-indicator">
        <div class="health-dot" id="healthDot"></div>
        <div id="healthText">System Healthy</div>
    </div>
    
    <!-- Support FAB -->
    <button class="support-fab" id="supportBtn" title="Get Help">❓</button>
    
    <script>
        class UATPOnboarding {
            constructor() {
                this.currentStep = 0;
                this.userId = `user_${Date.now()}`;
                this.selectedUserType = null;
                this.selectedPlatform = null;
                this.onboardingData = {};
                
                this.steps = [
                    'welcome',
                    'environment', 
                    'platforms',
                    'capsule',
                    'success'
                ];
                
                this.init();
            }
            
            init() {
                this.bindEvents();
                this.startHealthMonitoring();
                this.loadPlatforms();
            }
            
            bindEvents() {
                // User type selection
                document.querySelectorAll('.user-type-card').forEach(card => {
                    card.addEventListener('click', (e) => {
                        document.querySelectorAll('.user-type-card').forEach(c => c.classList.remove('selected'));
                        card.classList.add('selected');
                        this.selectedUserType = card.dataset.type;
                        document.getElementById('startBtn').disabled = false;
                    });
                });
                
                // Start button
                document.getElementById('startBtn').addEventListener('click', () => {
                    this.startOnboarding();
                });
                
                // Platform connection
                document.getElementById('connectPlatformBtn').addEventListener('click', () => {
                    this.connectPlatform();
                });
                
                // Launch dashboard
                document.getElementById('launchDashboardBtn').addEventListener('click', () => {
                    window.location.href = '/';
                });
                
                // Support button
                document.getElementById('supportBtn').addEventListener('click', () => {
                    this.showSupport();
                });
            }
            
            async startOnboarding() {
                try {
                    const response = await fetch('/onboarding/api/start', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            user_id: this.userId,
                            preferences: {
                                user_type: this.selectedUserType
                            }
                        })
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        this.onboardingData = data.progress;
                        this.nextStep();
                        
                        // Auto-continue to platforms after environment detection
                        setTimeout(() => {
                            this.continueOnboarding();
                        }, 3000);
                    } else {
                        this.showError('Failed to start onboarding: ' + data.error);
                    }
                } catch (error) {
                    this.showError('Network error: ' + error.message);
                }
            }
            
            async continueOnboarding(stepData = {}) {
                try {
                    const response = await fetch('/onboarding/api/continue', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            user_id: this.userId,
                            step_data: stepData
                        })
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        this.onboardingData = data.progress;
                        
                        if (data.next_step) {
                            this.nextStep();
                        }
                    } else {
                        this.showError('Failed to continue onboarding: ' + data.error);
                    }
                } catch (error) {
                    this.showError('Network error: ' + error.message);
                }
            }
            
            async loadPlatforms() {
                try {
                    const response = await fetch('/onboarding/api/platforms');
                    const data = await response.json();
                    
                    if (data.success) {
                        this.renderPlatforms(data.platforms);
                    }
                } catch (error) {
                    console.error('Failed to load platforms:', error);
                }
            }
            
            renderPlatforms(platforms) {
                const grid = document.getElementById('platformGrid');
                grid.innerHTML = '';
                
                Object.entries(platforms).forEach(([id, platform]) => {
                    const card = document.createElement('div');
                    card.className = `platform-card ${platform.available ? 'available' : ''}`;
                    card.dataset.platform = id;
                    
                    card.innerHTML = `
                        <div class="platform-status ${platform.available ? 'available' : 'setup-needed'}">
                            ${platform.available ? '✅ Ready' : '⚙️ Setup Needed'}
                        </div>
                        <h3>${platform.name}</h3>
                        <p>${platform.description}</p>
                        <div style="margin-top: 1rem;">
                            <small>Setup time: ~${platform.estimated_setup_time} min</small>
                        </div>
                    `;
                    
                    card.addEventListener('click', () => {
                        document.querySelectorAll('.platform-card').forEach(c => c.classList.remove('selected'));
                        card.classList.add('selected');
                        this.selectedPlatform = id;
                        document.getElementById('connectPlatformBtn').disabled = false;
                    });
                    
                    grid.appendChild(card);
                });
            }
            
            async connectPlatform() {
                if (!this.selectedPlatform) return;
                
                document.getElementById('connectPlatformBtn').innerHTML = 
                    '<div class="loading-spinner"></div>Connecting...';
                document.getElementById('connectPlatformBtn').disabled = true;
                
                await this.continueOnboarding({
                    preferred_platform: this.selectedPlatform
                });
                
                // Auto-continue to capsule creation
                setTimeout(() => {
                    this.nextStep();
                    this.createFirstCapsule();
                }, 2000);
            }
            
            async createFirstCapsule() {
                setTimeout(async () => {
                    await this.continueOnboarding();
                    this.nextStep();
                }, 3000);
            }
            
            nextStep() {
                if (this.currentStep < this.steps.length - 1) {
                    // Hide current step
                    document.getElementById(`step-${this.steps[this.currentStep]}`).classList.remove('active');
                    
                    // Show next step
                    this.currentStep++;
                    document.getElementById(`step-${this.steps[this.currentStep]}`).classList.add('active');
                    
                    // Update progress
                    this.updateProgress();
                }
            }
            
            updateProgress() {
                const progress = ((this.currentStep + 1) / this.steps.length) * 100;
                document.getElementById('progressFill').style.width = `${progress}%`;
                document.getElementById('progressText').textContent = 
                    `Step ${this.currentStep + 1} of ${this.steps.length}`;
            }
            
            async startHealthMonitoring() {
                setInterval(async () => {
                    try {
                        const response = await fetch('/onboarding/api/health');
                        const data = await response.json();
                        
                        if (data.success) {
                            this.updateHealthIndicator(data.health);
                        }
                    } catch (error) {
                        console.error('Health check failed:', error);
                    }
                }, 5000);
            }
            
            updateHealthIndicator(health) {
                const dot = document.getElementById('healthDot');
                const text = document.getElementById('healthText');
                
                dot.className = 'health-dot';
                
                if (health.overall_status === 'excellent' || health.overall_status === 'good') {
                    dot.classList.add('healthy');
                    text.textContent = 'System Healthy';
                } else if (health.overall_status === 'warning') {
                    dot.classList.add('warning');
                    text.textContent = 'System Warning';
                } else {
                    dot.classList.add('critical');
                    text.textContent = 'System Critical';
                }
            }
            
            async showSupport() {
                try {
                    const response = await fetch('/onboarding/api/support', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            user_id: this.userId,
                            issue_type: 'general_question',
                            message: 'I need help with onboarding'
                        })
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        alert(data.support.message + '\\n\\nNext steps:\\n' + 
                              data.support.immediate_actions.join('\\n'));
                    }
                } catch (error) {
                    alert('Support system temporarily unavailable. Please try again.');
                }
            }
            
            showError(message) {
                alert('Error: ' + message);
            }
        }
        
        // Initialize onboarding when page loads
        document.addEventListener('DOMContentLoaded', () => {
            new UATPOnboarding();
        });
    </script>
</body>
</html>
"""
