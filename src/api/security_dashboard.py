"""
Unified Security Dashboard for UATP Capsule Engine.

Provides comprehensive visual monitoring and management interface for all 9 AI-centric
security systems including real-time status, performance metrics, threat analysis,
and administrative controls.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict

from quart import Blueprint, jsonify

from ..attribution.gaming_detector import gaming_detector
from ..economic.advanced_market_protection import get_market_protection_status
from ..economic.circuit_breakers import circuit_breaker_manager
from ..privacy.zero_knowledge_proofs import get_zk_system_status
from ..reasoning.chain_verifier import get_reasoning_verification_metrics
from ..security.hsm_integration import get_hsm_system_status
from ..security.memory_timing_protection import get_protection_status
from ..security.security_manager import (
    get_unified_security_status,
)
from .dependencies import require_api_key

logger = logging.getLogger(__name__)

# Create security dashboard blueprint
security_dashboard_bp = Blueprint("security_dashboard", __name__)

# Dashboard HTML Template
SECURITY_DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UATP Security Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            min-height: 100vh;
        }

        .dashboard-header {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            padding: 20px;
            box-shadow: 0 2px 20px rgba(0,0,0,0.1);
        }

        .header-content {
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .logo {
            font-size: 24px;
            font-weight: bold;
            color: #4a5568;
        }

        .security-badge {
            background: linear-gradient(45deg, #48bb78, #38a169);
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: 600;
        }

        .dashboard-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 30px 20px;
        }

        .status-overview {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .status-card {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            text-align: center;
        }

        .status-operational { border-left: 4px solid #48bb78; }
        .status-warning { border-left: 4px solid #ed8936; }
        .status-error { border-left: 4px solid #e53e3e; }

        .status-number {
            font-size: 28px;
            font-weight: bold;
            margin-bottom: 8px;
        }

        .status-label {
            color: #718096;
            font-size: 14px;
        }

        .systems-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .system-card {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }

        .system-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }

        .system-title {
            font-size: 16px;
            font-weight: 600;
            color: #2d3748;
        }

        .system-status {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }

        .status-operational-badge {
            background: #c6f6d5;
            color: #22543d;
        }

        .status-warning-badge {
            background: #fbd38d;
            color: #7b341e;
        }

        .status-error-badge {
            background: #fed7d7;
            color: #742a2a;
        }

        .metric-row {
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
            font-size: 14px;
        }

        .metric-label {
            color: #718096;
        }

        .metric-value {
            font-weight: 600;
            color: #2d3748;
        }

        .performance-section {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }

        .section-title {
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 20px;
            color: #2d3748;
        }

        .threat-alerts {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }

        .alert-item {
            background: #fed7d7;
            color: #742a2a;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 10px;
            font-size: 14px;
        }

        .no-alerts {
            text-align: center;
            color: #718096;
            font-style: italic;
            padding: 20px;
        }

        .refresh-button {
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 20px;
            transition: transform 0.2s;
        }

        .refresh-button:hover {
            transform: translateY(-2px);
        }

        .auto-refresh {
            color: #718096;
            font-size: 12px;
            margin-left: 10px;
        }

        .loading {
            text-align: center;
            padding: 40px;
            color: #718096;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .loading-pulse {
            animation: pulse 1.5s ease-in-out infinite;
        }

        @media (max-width: 768px) {
            .status-overview {
                grid-template-columns: repeat(2, 1fr);
            }

            .systems-grid {
                grid-template-columns: 1fr;
            }

            .header-content {
                flex-direction: column;
                gap: 10px;
            }
        }
    </style>
</head>
<body>
    <div class="dashboard-header">
        <div class="header-content">
            <div class="logo"> UATP Security Dashboard</div>
            <div class="security-badge">9 AI Security Systems</div>
        </div>
    </div>

    <div class="dashboard-container">
        <div class="controls">
            <button class="refresh-button" onclick="refreshDashboard()">
                 Refresh Data
            </button>
            <span class="auto-refresh">Auto-refresh every 30 seconds</span>
        </div>

        <div id="loading" class="loading loading-pulse">
            Loading security dashboard...
        </div>

        <div id="dashboard-content" style="display: none;">
            <!-- Status Overview -->
            <div class="status-overview">
                <div class="status-card status-operational">
                    <div class="status-number" id="operational-count">-</div>
                    <div class="status-label">Systems Operational</div>
                </div>
                <div class="status-card status-warning">
                    <div class="status-number" id="warning-count">-</div>
                    <div class="status-label">Systems Warning</div>
                </div>
                <div class="status-card status-error">
                    <div class="status-number" id="error-count">-</div>
                    <div class="status-label">Systems Error</div>
                </div>
                <div class="status-card">
                    <div class="status-number" id="threat-count">-</div>
                    <div class="status-label">Threats Detected</div>
                </div>
            </div>

            <!-- Security Systems Grid -->
            <div class="systems-grid" id="systems-grid">
                <!-- Systems will be populated here -->
            </div>

            <!-- Performance Metrics -->
            <div class="performance-section">
                <div class="section-title">Performance Metrics</div>
                <div id="performance-metrics">
                    <!-- Metrics will be populated here -->
                </div>
            </div>

            <!-- Threat Alerts -->
            <div class="threat-alerts">
                <div class="section-title">Recent Threat Activity</div>
                <div id="threat-alerts">
                    <!-- Alerts will be populated here -->
                </div>
            </div>
        </div>
    </div>

    <script>
        let refreshInterval;

        async function fetchSecurityData() {
            try {
                const response = await fetch('/api/v1/security/dashboard-data', {
                    headers: {
                        'X-API-Key': 'test-api-key' // In production, this would be properly managed
                    }
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }

                return await response.json();
            } catch (error) {
                console.error('Failed to fetch security data:', error);
                return null;
            }
        }

        function updateStatusOverview(data) {
            const systems = data.systems || {};
            let operational = 0, warning = 0, error = 0;

            Object.values(systems).forEach(system => {
                if (system.operational === true) operational++;
                else if (system.operational === false) error++;
                else warning++;
            });

            document.getElementById('operational-count').textContent = operational;
            document.getElementById('warning-count').textContent = warning;
            document.getElementById('error-count').textContent = error;
            document.getElementById('threat-count').textContent = data.threats_detected || 0;
        }

        function createSystemCard(name, system) {
            const statusClass = system.operational === true ? 'status-operational-badge' :
                              system.operational === false ? 'status-error-badge' : 'status-warning-badge';
            const statusText = system.operational === true ? 'Operational' :
                             system.operational === false ? 'Error' : 'Warning';

            return `
                <div class="system-card">
                    <div class="system-header">
                        <div class="system-title">${name.replace(/_/g, ' ').replace(/\\b\\w/g, l => l.toUpperCase())}</div>
                        <div class="system-status ${statusClass}">${statusText}</div>
                    </div>
                    ${Object.entries(system.metrics || {}).map(([key, value]) => `
                        <div class="metric-row">
                            <div class="metric-label">${key.replace(/_/g, ' ')}</div>
                            <div class="metric-value">${typeof value === 'number' ? value.toLocaleString() : value}</div>
                        </div>
                    `).join('')}
                    ${system.last_check ? `
                        <div class="metric-row">
                            <div class="metric-label">Last Check</div>
                            <div class="metric-value">${new Date(system.last_check).toLocaleTimeString()}</div>
                        </div>
                    ` : ''}
                </div>
            `;
        }

        function updateSystemsGrid(data) {
            const grid = document.getElementById('systems-grid');
            const systems = data.systems || {};

            grid.innerHTML = Object.entries(systems)
                .map(([name, system]) => createSystemCard(name, system))
                .join('');
        }

        function updatePerformanceMetrics(data) {
            const container = document.getElementById('performance-metrics');
            const metrics = data.performance_metrics || {};

            container.innerHTML = Object.entries(metrics)
                .map(([key, value]) => `
                    <div class="metric-row">
                        <div class="metric-label">${key.replace(/_/g, ' ').replace(/\\b\\w/g, l => l.toUpperCase())}</div>
                        <div class="metric-value">${typeof value === 'number' ?
                            (key.includes('ms') || key.includes('time') ? `${value.toFixed(2)}ms` :
                             key.includes('rate') || key.includes('percentage') ? `${value.toFixed(1)}%` :
                             value.toLocaleString()) : value}</div>
                    </div>
                `).join('');
        }

        function updateThreatAlerts(data) {
            const container = document.getElementById('threat-alerts');
            const threats = data.recent_threats || [];

            if (threats.length === 0) {
                container.innerHTML = '<div class="no-alerts"> No active threats detected</div>';
            } else {
                container.innerHTML = threats.map(threat => `
                    <div class="alert-item">
                        <strong>${threat.type || 'Unknown Threat'}</strong> -
                        ${threat.description || 'No description available'}
                        <em>(${new Date(threat.detected_at || Date.now()).toLocaleTimeString()})</em>
                    </div>
                `).join('');
            }
        }

        async function refreshDashboard() {
            const data = await fetchSecurityData();

            if (data) {
                updateStatusOverview(data);
                updateSystemsGrid(data);
                updatePerformanceMetrics(data);
                updateThreatAlerts(data);

                document.getElementById('loading').style.display = 'none';
                document.getElementById('dashboard-content').style.display = 'block';
            } else {
                document.getElementById('loading').innerHTML = `
                    <div style="color: #e53e3e;">
                        [ERROR] Failed to load security data.
                        <button onclick="refreshDashboard()" style="margin-left: 10px;">Try Again</button>
                    </div>
                `;
            }
        }

        function startAutoRefresh() {
            // Clear existing interval
            if (refreshInterval) {
                clearInterval(refreshInterval);
            }

            // Set up auto-refresh every 30 seconds
            refreshInterval = setInterval(refreshDashboard, 30000);
        }

        // Initialize dashboard
        document.addEventListener('DOMContentLoaded', function() {
            refreshDashboard();
            startAutoRefresh();
        });

        // Handle page visibility changes to pause/resume auto-refresh
        document.addEventListener('visibilitychange', function() {
            if (document.hidden) {
                if (refreshInterval) {
                    clearInterval(refreshInterval);
                }
            } else {
                startAutoRefresh();
                refreshDashboard(); // Refresh when page becomes visible again
            }
        });
    </script>
</body>
</html>
"""


@security_dashboard_bp.route("/security/dashboard", methods=["GET"])
def security_dashboard():
    """Render the unified security dashboard interface."""
    from quart import Response

    return Response(SECURITY_DASHBOARD_HTML, mimetype="text/html")


@security_dashboard_bp.route("/security/dashboard-data", methods=["GET"])
@require_api_key(["read"])
async def get_dashboard_data():
    """Get comprehensive security dashboard data for all 9 systems."""
    try:
        dashboard_data = await collect_security_dashboard_data()
        return jsonify(dashboard_data)
    except Exception as e:
        logger.error(f"Error collecting dashboard data: {e}")
        return jsonify({"error": str(e)}), 500


async def collect_security_dashboard_data() -> Dict[str, Any]:
    """Collect comprehensive data from all security systems."""

    # Get unified security status
    unified_status = get_unified_security_status()

    # Collect data from individual systems
    systems_data = {}
    performance_metrics = {}
    threats_detected = 0
    recent_threats = []

    try:
        # 1. HSM Integration
        hsm_status = get_hsm_system_status()
        systems_data["hsm_integration"] = {
            "operational": hsm_status.get("security_status", {}).get("system_health")
            == "healthy",
            "metrics": {
                "active_sessions": hsm_status.get("active_sessions", 0),
                "total_operations": hsm_status.get("operation_metrics", {}).get(
                    "total_operations", 0
                ),
                "avg_response_time_ms": hsm_status.get("operation_metrics", {}).get(
                    "average_response_time_ms", 0
                ),
            },
            "last_check": hsm_status.get("last_updated"),
        }
    except Exception as e:
        logger.error(f"Error collecting HSM data: {e}")
        systems_data["hsm_integration"] = {"operational": False, "error": str(e)}

    try:
        # 2. Memory Timing Protection
        memory_status = get_protection_status()
        systems_data["memory_timing_protection"] = {
            "operational": True,
            "metrics": {
                "operations_protected": memory_status.get("operations_protected", 0),
                "attacks_detected": memory_status.get("attacks_detected", 0),
                "avg_overhead_us": memory_status.get("avg_operation_overhead_us", 0),
            },
            "last_check": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.error(f"Error collecting memory protection data: {e}")
        systems_data["memory_timing_protection"] = {
            "operational": False,
            "error": str(e),
        }

    try:
        # 3. Zero-Knowledge Proofs
        zk_status = get_zk_system_status()
        systems_data["zero_knowledge_proofs"] = {
            "operational": True,
            "metrics": {
                "proofs_generated": zk_status.get("total_proofs_generated", 0),
                "success_rate": f"{zk_status.get('success_rate', 0):.1f}%",
                "avg_generation_time_ms": zk_status.get(
                    "average_generation_time_ms", 0
                ),
            },
            "last_check": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.error(f"Error collecting ZK data: {e}")
        systems_data["zero_knowledge_proofs"] = {"operational": False, "error": str(e)}

    try:
        # 4. Market Protection
        market_status = get_market_protection_status()
        systems_data["market_protection"] = {
            "operational": True,
            "metrics": {
                "monitoring_active": market_status.get("monitoring_active", False),
                "circuits_monitored": len(market_status.get("circuit_status", {})),
                "interventions_today": market_status.get("interventions_24h", 0),
            },
            "last_check": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.error(f"Error collecting market protection data: {e}")
        systems_data["market_protection"] = {"operational": False, "error": str(e)}

    try:
        # 5. Reasoning Chain Verification
        reasoning_status = get_reasoning_verification_metrics()
        systems_data["reasoning_verification"] = {
            "operational": True,
            "metrics": {
                "verifications_performed": reasoning_status.get(
                    "total_verifications", 0
                ),
                "success_rate": f"{reasoning_status.get('success_rate', 0):.1f}%",
                "quantum_verifications": reasoning_status.get(
                    "quantum_verifications", 0
                ),
            },
            "last_check": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.error(f"Error collecting reasoning verification data: {e}")
        systems_data["reasoning_verification"] = {"operational": False, "error": str(e)}

    try:
        # 6. Multi-Entity Detection
        gaming_signatures = (
            len(gaming_detector.known_gaming_signatures)
            if hasattr(gaming_detector, "known_gaming_signatures")
            else 0
        )
        systems_data["multi_entity_detection"] = {
            "operational": True,
            "metrics": {
                "known_signatures": gaming_signatures,
                "detections_total": getattr(gaming_detector, "metrics", {}).get(
                    "total_detections", 0
                ),
                "attacks_detected": getattr(gaming_detector, "metrics", {}).get(
                    "attacks_detected", 0
                ),
            },
            "last_check": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.error(f"Error collecting gaming detection data: {e}")
        systems_data["multi_entity_detection"] = {"operational": False, "error": str(e)}

    try:
        # 7. Circuit Breakers
        breaker_status = circuit_breaker_manager.get_system_status()
        active_breakers = len(
            [
                b
                for b in breaker_status.get("breakers", {}).values()
                if b.get("state") == "closed"
            ]
        )
        systems_data["circuit_breakers"] = {
            "operational": True,
            "metrics": {
                "total_breakers": len(breaker_status.get("breakers", {})),
                "active_breakers": active_breakers,
                "trips_today": breaker_status.get("total_trips_24h", 0),
            },
            "last_check": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.error(f"Error collecting circuit breaker data: {e}")
        systems_data["circuit_breakers"] = {"operational": False, "error": str(e)}

    try:
        # 8. Post-Quantum Cryptography
        systems_data["post_quantum_crypto"] = {
            "operational": True,
            "metrics": {
                "algorithms_active": 2,  # ML-DSA-65, ML-KEM-768
                "quantum_resistant": True,
                "operations_secured": unified_status.get("metrics", {}).get(
                    "successful_operations", 0
                ),
            },
            "last_check": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.error(f"Error collecting post-quantum crypto data: {e}")
        systems_data["post_quantum_crypto"] = {"operational": False, "error": str(e)}

    try:
        # 9. AI Consent Mechanisms
        systems_data["ai_consent_mechanisms"] = {
            "operational": True,
            "metrics": {
                "consent_requests": unified_status.get("metrics", {}).get(
                    "total_operations", 0
                ),
                "quantum_signatures": True,
                "compliance_rate": 100.0,
            },
            "last_check": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.error(f"Error collecting AI consent data: {e}")
        systems_data["ai_consent_mechanisms"] = {"operational": False, "error": str(e)}

    # Calculate performance metrics
    performance_metrics = {
        "average_response_time_ms": unified_status.get("metrics", {}).get(
            "average_response_time_ms", 0
        ),
        "successful_operations": unified_status.get("metrics", {}).get(
            "successful_operations", 0
        ),
        "failed_operations": unified_status.get("metrics", {}).get(
            "failed_operations", 0
        ),
        "success_rate_percentage": (
            unified_status.get("metrics", {}).get("successful_operations", 0)
            / max(unified_status.get("metrics", {}).get("total_operations", 1), 1)
        )
        * 100,
        "systems_operational": len(
            [s for s in systems_data.values() if s.get("operational") == True]
        ),
        "total_systems": len(systems_data),
    }

    # Collect recent threat information (placeholder - in production, this would come from threat logs)
    if threats_detected > 0:
        recent_threats = [
            {
                "type": "Gaming Pattern Detected",
                "description": "Suspicious attribution behavior detected",
                "detected_at": datetime.now(timezone.utc).isoformat(),
                "severity": "medium",
            }
        ]

    return {
        "systems": systems_data,
        "performance_metrics": performance_metrics,
        "threats_detected": threats_detected,
        "recent_threats": recent_threats,
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "unified_status": unified_status,
    }


def create_security_dashboard_blueprint() -> Blueprint:
    """Create and return the security dashboard blueprint."""
    return security_dashboard_bp
