"""
AI Rights Dashboard Web Interface
================================

This module provides a web-based dashboard for monitoring AI agent rights,
financial performance, and system operations in real-time.
"""

import asyncio
import json
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from flask_socketio import SocketIO, emit

from src.events.event_system import get_event_bus

from .analytics_engine import initialize_analytics_engine

logger = logging.getLogger(__name__)


class DashboardWebServer:
    """Web server for the AI Rights Dashboard."""

    def __init__(self, host: str = "localhost", port: int = 5000):
        self.host = host
        self.port = port
        self.app = Flask(
            __name__,
            template_folder=str(Path(__file__).parent / "templates"),
            static_folder=str(Path(__file__).parent / "static"),
        )
        self.app.config["SECRET_KEY"] = "uatp_dashboard_secret_key"
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")

        self.analytics_engine = None
        self.event_bus = None
        self.real_time_enabled = True
        self._setup_routes()
        self._setup_socket_events()

        logger.info(f"Dashboard web server initialized on {host}:{port}")

    def _setup_routes(self):
        """Set up Flask routes."""

        @self.app.route("/")
        def dashboard_home():
            """Main dashboard page."""
            return render_template("dashboard.html")

        @self.app.route("/api/stats")
        async def get_stats():
            """Get dashboard statistics."""
            try:
                if not self.analytics_engine:
                    return jsonify({"error": "Analytics engine not initialized"}), 500

                stats = await self.analytics_engine.get_dashboard_stats()
                return jsonify(
                    {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "stats": {
                            # Agent statistics
                            "total_agents": stats.total_agents,
                            "active_citizens": stats.active_citizens,
                            "pending_applications": stats.pending_applications,
                            "citizenship_success_rate": round(
                                stats.citizenship_success_rate, 2
                            ),
                            # Financial statistics
                            "total_ip_assets": stats.total_ip_assets,
                            "total_asset_value": round(stats.total_asset_value, 2),
                            "active_bonds": stats.active_bonds,
                            "total_bond_value": round(stats.total_bond_value, 2),
                            "total_dividends_paid": round(
                                stats.total_dividends_paid, 2
                            ),
                            "average_yield": round(
                                stats.average_yield * 100, 2
                            ),  # Convert to percentage
                            # System statistics
                            "total_events": stats.total_events,
                            "events_per_minute": round(stats.events_per_minute, 1),
                            "system_uptime": round(
                                stats.system_uptime / 3600, 2
                            ),  # Convert to hours
                            "processing_rate": round(stats.processing_rate, 2),
                            # Risk and compliance
                            "compliance_issues": stats.compliance_issues,
                            "high_risk_agents": stats.high_risk_agents,
                            "failed_assessments": stats.failed_assessments,
                            # Performance metrics
                            "avg_assessment_score": round(
                                stats.avg_assessment_score, 3
                            ),
                            "top_performing_assets": stats.top_performing_assets[:5],
                            "recent_activity": stats.recent_activity[:10],
                        },
                    }
                )
            except Exception as e:
                logger.error(f"Error getting stats: {e}")
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api/detailed-metrics")
        async def get_detailed_metrics():
            """Get detailed metrics."""
            try:
                if not self.analytics_engine:
                    return jsonify({"error": "Analytics engine not initialized"}), 500

                metrics = await self.analytics_engine.get_detailed_metrics()
                return jsonify(
                    {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "metrics": metrics,
                    }
                )
            except Exception as e:
                logger.error(f"Error getting detailed metrics: {e}")
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api/agent/<agent_id>")
        async def get_agent_profile(agent_id: str):
            """Get detailed agent profile."""
            try:
                if not self.analytics_engine:
                    return jsonify({"error": "Analytics engine not initialized"}), 500

                profile = await self.analytics_engine.get_agent_profile(agent_id)
                return jsonify(
                    {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "profile": profile,
                    }
                )
            except Exception as e:
                logger.error(f"Error getting agent profile: {e}")
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api/trends")
        async def get_performance_trends():
            """Get performance trends."""
            try:
                if not self.analytics_engine:
                    return jsonify({"error": "Analytics engine not initialized"}), 500

                days = request.args.get("days", 7, type=int)
                trends = await self.analytics_engine.get_performance_trends(days)
                return jsonify(
                    {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "trends": trends,
                    }
                )
            except Exception as e:
                logger.error(f"Error getting trends: {e}")
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api/export")
        def export_metrics():
            """Export metrics."""
            try:
                if not self.analytics_engine:
                    return jsonify({"error": "Analytics engine not initialized"}), 500

                format_type = request.args.get("format", "json")
                exported_data = self.analytics_engine.export_metrics(format_type)

                return jsonify(
                    {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "format": format_type,
                        "data": json.loads(exported_data)
                        if format_type == "json"
                        else exported_data,
                    }
                )
            except Exception as e:
                logger.error(f"Error exporting metrics: {e}")
                return jsonify({"error": str(e)}), 500

        @self.app.route("/health")
        def health_check():
            """Health check endpoint."""
            return jsonify(
                {
                    "status": "healthy",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "analytics_engine": self.analytics_engine is not None,
                    "event_bus": self.event_bus is not None,
                }
            )

    def _setup_socket_events(self):
        """Set up WebSocket events for real-time updates."""

        @self.socketio.on("connect")
        def handle_connect():
            """Handle client connection."""
            logger.info("Client connected")
            emit("status", {"message": "Connected to AI Rights Dashboard"})

        @self.socketio.on("disconnect")
        def handle_disconnect():
            """Handle client disconnection."""
            logger.info("Client disconnected")

        @self.socketio.on("subscribe_real_time")
        def handle_subscribe_real_time():
            """Handle real-time subscription."""
            logger.info("Client subscribed to real-time updates")
            emit("real_time_status", {"subscribed": True})

        @self.socketio.on("request_stats")
        def handle_request_stats():
            """Handle stats request via WebSocket."""
            asyncio.create_task(self._send_stats_update())

    async def _send_stats_update(self):
        """Send stats update via WebSocket."""
        try:
            if self.analytics_engine:
                stats = await self.analytics_engine.get_dashboard_stats()
                self.socketio.emit(
                    "stats_update",
                    {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "stats": {
                            "total_agents": stats.total_agents,
                            "active_citizens": stats.active_citizens,
                            "total_events": stats.total_events,
                            "processing_rate": round(stats.processing_rate, 2),
                            "compliance_issues": stats.compliance_issues,
                        },
                    },
                )
        except Exception as e:
            logger.error(f"Error sending stats update: {e}")

    async def initialize(self):
        """Initialize analytics engine and event system."""
        try:
            self.event_bus = get_event_bus()
            self.analytics_engine = await initialize_analytics_engine(self.event_bus)
            logger.info("Dashboard analytics initialized")
        except Exception as e:
            logger.error(f"Error initializing dashboard: {e}")

    def start_real_time_updates(self):
        """Start real-time updates via WebSocket."""

        async def update_loop():
            while self.real_time_enabled:
                await self._send_stats_update()
                await asyncio.sleep(5)  # Update every 5 seconds

        # Run update loop in background
        def run_updates():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(update_loop())

        update_thread = threading.Thread(target=run_updates, daemon=True)
        update_thread.start()
        logger.info("Real-time updates started")

    def run(self, debug: bool = False):
        """Run the dashboard web server."""
        self.socketio.run(self.app, host=self.host, port=self.port, debug=debug)


# Create dashboard HTML template
def create_dashboard_template():
    """Create the dashboard HTML template."""
    template_dir = Path(__file__).parent / "templates"
    template_dir.mkdir(exist_ok=True)

    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Rights Dashboard - UATP Capsule Engine</title>
    <script src="https://cdn.socket.io/4.0.0/socket.io.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }

        .header {
            background: rgba(255, 255, 255, 0.95);
            padding: 1rem 2rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .header h1 {
            color: #4a5568;
            font-size: 1.8rem;
        }

        .status-indicator {
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: bold;
        }

        .status-online {
            background: #48bb78;
            color: white;
        }

        .status-offline {
            background: #f56565;
            color: white;
        }

        .dashboard-container {
            padding: 2rem;
            max-width: 1400px;
            margin: 0 auto;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }

        .stat-card {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            transition: transform 0.2s ease;
        }

        .stat-card:hover {
            transform: translateY(-2px);
        }

        .stat-card h3 {
            color: #4a5568;
            margin-bottom: 1rem;
            font-size: 1.1rem;
        }

        .stat-value {
            font-size: 2rem;
            font-weight: bold;
            color: #2d3748;
            margin-bottom: 0.5rem;
        }

        .stat-label {
            color: #718096;
            font-size: 0.9rem;
        }

        .chart-container {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 2rem;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }

        .activity-feed {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }

        .activity-item {
            padding: 0.75rem;
            border-left: 4px solid #667eea;
            margin-bottom: 0.5rem;
            background: #f7fafc;
            border-radius: 0 8px 8px 0;
        }

        .activity-time {
            font-size: 0.8rem;
            color: #718096;
        }

        .loading {
            text-align: center;
            padding: 2rem;
            color: #718096;
        }

        .error {
            background: #fed7d7;
            color: #c53030;
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
        }

        .success {
            background: #c6f6d5;
            color: #22543d;
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
        }

        .controls {
            display: flex;
            gap: 1rem;
            margin-bottom: 2rem;
            flex-wrap: wrap;
        }

        .btn {
            padding: 0.75rem 1.5rem;
            border: none;
            border-radius: 8px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .btn-primary {
            background: #667eea;
            color: white;
        }

        .btn-primary:hover {
            background: #5a67d8;
        }

        .btn-secondary {
            background: #e2e8f0;
            color: #4a5568;
        }

        .btn-secondary:hover {
            background: #cbd5e0;
        }

        @media (max-width: 768px) {
            .dashboard-container {
                padding: 1rem;
            }

            .stats-grid {
                grid-template-columns: 1fr;
            }

            .header {
                padding: 1rem;
                flex-direction: column;
                gap: 1rem;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1> AI Rights Dashboard</h1>
        <div id="connection-status" class="status-indicator status-offline">Connecting...</div>
    </div>

    <div class="dashboard-container">
        <div class="controls">
            <button class="btn btn-primary" onclick="refreshStats()"> Refresh</button>
            <button class="btn btn-secondary" onclick="exportMetrics()"> Export Data</button>
            <button class="btn btn-secondary" onclick="toggleRealTime()"> Real-time: <span id="realtime-status">Off</span></button>
        </div>

        <div id="error-container"></div>

        <div class="stats-grid">
            <div class="stat-card">
                <h3> AI Agents</h3>
                <div class="stat-value" id="total-agents">-</div>
                <div class="stat-label">Total Registered Agents</div>
            </div>

            <div class="stat-card">
                <h3> Active Citizens</h3>
                <div class="stat-value" id="active-citizens">-</div>
                <div class="stat-label">Citizenship Success Rate: <span id="success-rate">-%</span></div>
            </div>

            <div class="stat-card">
                <h3> Total Asset Value</h3>
                <div class="stat-value" id="total-asset-value">$-</div>
                <div class="stat-label"><span id="total-assets">-</span> IP Assets</div>
            </div>

            <div class="stat-card">
                <h3> Active Bonds</h3>
                <div class="stat-value" id="active-bonds">-</div>
                <div class="stat-label">Total Value: $<span id="bond-value">-</span></div>
            </div>

            <div class="stat-card">
                <h3> Dividends Paid</h3>
                <div class="stat-value" id="dividends-paid">$-</div>
                <div class="stat-label">Average Yield: <span id="avg-yield">-%</span></div>
            </div>

            <div class="stat-card">
                <h3> System Health</h3>
                <div class="stat-value" id="system-health">-</div>
                <div class="stat-label">Events/min: <span id="events-per-min">-</span></div>
            </div>
        </div>

        <div class="chart-container">
            <h3> Performance Overview</h3>
            <canvas id="performance-chart" width="400" height="200"></canvas>
        </div>

        <div class="activity-feed">
            <h3> Recent Activity</h3>
            <div id="activity-list">
                <div class="loading">Loading recent activity...</div>
            </div>
        </div>
    </div>

    <script>
        let socket;
        let realTimeEnabled = false;
        let performanceChart;

        // Initialize dashboard
        document.addEventListener('DOMContentLoaded', function() {
            initializeSocket();
            initializeChart();
            refreshStats();
        });

        function initializeSocket() {
            socket = io();

            socket.on('connect', function() {
                updateConnectionStatus(true);
                showMessage('Connected to AI Rights Dashboard', 'success');
            });

            socket.on('disconnect', function() {
                updateConnectionStatus(false);
                showMessage('Disconnected from dashboard', 'error');
            });

            socket.on('stats_update', function(data) {
                if (realTimeEnabled) {
                    updateStatsDisplay(data.stats);
                }
            });
        }

        function initializeChart() {
            const ctx = document.getElementById('performance-chart').getContext('2d');
            performanceChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                    datasets: [{
                        label: 'Events Processed',
                        data: [12, 19, 3, 5, 2, 3, 9],
                        borderColor: 'rgb(102, 126, 234)',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'top',
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }

        function updateConnectionStatus(connected) {
            const statusEl = document.getElementById('connection-status');
            if (connected) {
                statusEl.textContent = 'Online';
                statusEl.className = 'status-indicator status-online';
            } else {
                statusEl.textContent = 'Offline';
                statusEl.className = 'status-indicator status-offline';
            }
        }

        async function refreshStats() {
            try {
                showMessage('Refreshing dashboard data...', 'info');
                const response = await fetch('/api/stats');
                const data = await response.json();

                if (data.error) {
                    throw new Error(data.error);
                }

                updateStatsDisplay(data.stats);
                await loadRecentActivity();
                showMessage('Dashboard updated successfully', 'success');
            } catch (error) {
                console.error('Error refreshing stats:', error);
                showMessage('Error refreshing dashboard: ' + error.message, 'error');
            }
        }

        function updateStatsDisplay(stats) {
            document.getElementById('total-agents').textContent = stats.total_agents || 0;
            document.getElementById('active-citizens').textContent = stats.active_citizens || 0;
            document.getElementById('success-rate').textContent = (stats.citizenship_success_rate || 0).toFixed(1) + '%';

            document.getElementById('total-asset-value').textContent = '$' + formatNumber(stats.total_asset_value || 0);
            document.getElementById('total-assets').textContent = stats.total_ip_assets || 0;

            document.getElementById('active-bonds').textContent = stats.active_bonds || 0;
            document.getElementById('bond-value').textContent = formatNumber(stats.total_bond_value || 0);

            document.getElementById('dividends-paid').textContent = '$' + formatNumber(stats.total_dividends_paid || 0);
            document.getElementById('avg-yield').textContent = (stats.average_yield || 0).toFixed(2) + '%';

            document.getElementById('system-health').textContent = stats.compliance_issues > 0 ? '[WARN] Issues' : '[OK] Good';
            document.getElementById('events-per-min').textContent = (stats.events_per_minute || 0).toFixed(1);
        }

        async function loadRecentActivity() {
            try {
                const response = await fetch('/api/stats');
                const data = await response.json();

                const activityList = document.getElementById('activity-list');
                if (data.stats && data.stats.recent_activity) {
                    activityList.innerHTML = data.stats.recent_activity.slice(0, 10).map(activity => `
                        <div class="activity-item">
                            <strong>${activity.agent_id}</strong> - ${activity.total_activities} activities
                            <div class="activity-time">Last activity: ${activity.last_activity ? new Date(activity.last_activity).toLocaleString() : 'N/A'}</div>
                        </div>
                    `).join('');
                } else {
                    activityList.innerHTML = '<div class="loading">No recent activity</div>';
                }
            } catch (error) {
                console.error('Error loading activity:', error);
                document.getElementById('activity-list').innerHTML = '<div class="error">Error loading activity</div>';
            }
        }

        function toggleRealTime() {
            realTimeEnabled = !realTimeEnabled;
            document.getElementById('realtime-status').textContent = realTimeEnabled ? 'On' : 'Off';

            if (realTimeEnabled) {
                socket.emit('subscribe_real_time');
                showMessage('Real-time updates enabled', 'success');
            } else {
                showMessage('Real-time updates disabled', 'info');
            }
        }

        async function exportMetrics() {
            try {
                showMessage('Exporting metrics...', 'info');
                const response = await fetch('/api/export?format=json');
                const data = await response.json();

                const blob = new Blob([JSON.stringify(data.data, null, 2)],
                                     { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `uatp-metrics-${new Date().toISOString().split('T')[0]}.json`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);

                showMessage('Metrics exported successfully', 'success');
            } catch (error) {
                console.error('Error exporting metrics:', error);
                showMessage('Error exporting metrics: ' + error.message, 'error');
            }
        }

        function formatNumber(num) {
            if (num >= 1e6) {
                return (num / 1e6).toFixed(1) + 'M';
            } else if (num >= 1e3) {
                return (num / 1e3).toFixed(1) + 'K';
            }
            return num.toLocaleString();
        }

        function showMessage(message, type = 'info') {
            const container = document.getElementById('error-container');
            const div = document.createElement('div');
            div.className = type;
            div.textContent = message;
            container.appendChild(div);

            setTimeout(() => {
                container.removeChild(div);
            }, 5000);
        }

        // Auto-refresh every 30 seconds if real-time is disabled
        setInterval(() => {
            if (!realTimeEnabled) {
                refreshStats();
            }
        }, 30000);
    </script>
</body>
</html>
    """

    with open(template_dir / "dashboard.html", "w") as f:
        f.write(html_content)

    logger.info("Dashboard template created")


# Initialize dashboard on import
create_dashboard_template()
