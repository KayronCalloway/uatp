#!/usr/bin/env python3
"""
Locust Load Testing for UATP Capsule Engine
===========================================

This file provides Locust-based load testing for the UATP API endpoints.
Run with: locust -f locustfile.py --host=http://localhost:8000
"""

import json
import random
import string
import time
from datetime import datetime
from locust import HttpUser, task, between


class UATPUser(HttpUser):
    """Simulated user for UATP load testing."""

    wait_time = between(1, 3)  # Wait 1-3 seconds between requests

    def on_start(self):
        """Called when user starts."""
        self.user_id = f"load_test_user_{random.randint(1000, 9999)}"
        self.session_id = f"session_{int(time.time())}_{random.randint(100, 999)}"
        self.created_capsules = []

        # Try to authenticate (if auth is enabled)
        self.auth_token = None
        # self.authenticate()  # Uncomment if authentication is required

    def authenticate(self):
        """Authenticate user (if auth is enabled)."""

        auth_data = {"username": self.user_id, "password": "test_password"}

        # Try to register first
        response = self.client.post("/auth/register", json=auth_data)

        # Then login
        response = self.client.post("/auth/login", json=auth_data)

        if response.status_code == 200:
            data = response.json()
            self.auth_token = data.get("access_token")

    def get_auth_headers(self):
        """Get authentication headers."""
        if self.auth_token:
            return {"Authorization": f"Bearer {self.auth_token}"}
        return {}

    @task(3)
    def create_capsule(self):
        """Create a new capsule."""

        capsule_data = {
            "capsule_id": f"load_test_{self.user_id}_{int(time.time() * 1000)}",
            "type": "interaction_capsule",
            "platform": "load_test",
            "user_id": self.user_id,
            "session_id": self.session_id,
            "model": "test-model",
            "user_message": f"Load test message {random.randint(1, 1000)}",
            "ai_response": f"Test response {random.randint(1, 1000)} for load testing",
            "significance_score": random.uniform(0.5, 5.0),
            "confidence_score": random.uniform(0.6, 1.0),
            "timestamp": datetime.now().isoformat(),
            "metadata": {
                "test": True,
                "load_test_user": self.user_id,
                "iteration": random.randint(1, 100),
            },
        }

        with self.client.post(
            "/api/capsules",
            json=capsule_data,
            headers=self.get_auth_headers(),
            catch_response=True,
        ) as response:
            if response.status_code in [200, 201]:
                try:
                    data = response.json()
                    capsule_id = data.get("capsule_id")
                    if capsule_id:
                        self.created_capsules.append(capsule_id)
                        response.success()
                    else:
                        response.failure("No capsule_id in response")
                except:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"HTTP {response.status_code}")

    @task(5)
    def list_capsules(self):
        """List capsules."""

        params = {"limit": random.randint(10, 50), "offset": random.randint(0, 100)}

        with self.client.get(
            "/api/capsules",
            params=params,
            headers=self.get_auth_headers(),
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "capsules" in data:
                        response.success()
                    else:
                        response.failure("No capsules in response")
                except:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"HTTP {response.status_code}")

    @task(2)
    def get_capsule(self):
        """Get a specific capsule."""

        if not self.created_capsules:
            # If no capsules created yet, skip this task
            return

        capsule_id = random.choice(self.created_capsules)

        with self.client.get(
            f"/api/capsules/{capsule_id}",
            headers=self.get_auth_headers(),
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "capsule" in data:
                        response.success()
                    else:
                        response.failure("No capsule in response")
                except:
                    response.failure("Invalid JSON response")
            elif response.status_code == 404:
                # Capsule not found, remove from list
                self.created_capsules.remove(capsule_id)
                response.success()  # This is expected behavior
            else:
                response.failure(f"HTTP {response.status_code}")

    @task(2)
    def search_capsules(self):
        """Search capsules."""

        search_terms = [
            "load test",
            "test message",
            "response",
            "capsule",
            "benchmark",
            "performance",
        ]

        params = {"q": random.choice(search_terms), "limit": random.randint(5, 20)}

        with self.client.get(
            "/api/capsules/search",
            params=params,
            headers=self.get_auth_headers(),
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "results" in data:
                        response.success()
                    else:
                        response.failure("No results in response")
                except:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"HTTP {response.status_code}")

    @task(1)
    def get_capsule_stats(self):
        """Get capsule statistics."""

        with self.client.get(
            "/api/capsules/stats", headers=self.get_auth_headers(), catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "stats" in data:
                        response.success()
                    else:
                        response.failure("No stats in response")
                except:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"HTTP {response.status_code}")

    @task(1)
    def health_check(self):
        """Health check endpoint."""

        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "status" in data:
                        response.success()
                    else:
                        response.failure("No status in response")
                except:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"HTTP {response.status_code}")


class UATPMonitoringUser(HttpUser):
    """User for testing monitoring endpoints."""

    wait_time = between(5, 10)  # Longer wait time for monitoring

    @task(1)
    def health_check(self):
        """Basic health check."""
        self.client.get("/health")

    @task(1)
    def detailed_health_check(self):
        """Detailed health check."""
        self.client.get("/health/detailed")

    @task(1)
    def metrics(self):
        """Get metrics."""
        self.client.get("/metrics")

    @task(1)
    def metrics_summary(self):
        """Get metrics summary."""
        self.client.get("/metrics/summary")


class UATPAuthUser(HttpUser):
    """User for testing authentication endpoints."""

    wait_time = between(2, 5)

    def on_start(self):
        """Called when user starts."""
        self.username = f"auth_test_user_{random.randint(1000, 9999)}"
        self.password = "test_password_123"
        self.auth_token = None

    @task(1)
    def register_and_login(self):
        """Register and login user."""

        # Register
        register_data = {
            "username": self.username,
            "email": f"{self.username}@test.com",
            "password": self.password,
        }

        response = self.client.post("/auth/register", json=register_data)

        if response.status_code in [200, 201]:
            # Login
            login_data = {"username": self.username, "password": self.password}

            response = self.client.post("/auth/login", json=login_data)

            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")

    @task(2)
    def get_user_info(self):
        """Get current user info."""

        if not self.auth_token:
            return

        headers = {"Authorization": f"Bearer {self.auth_token}"}
        self.client.get("/auth/me", headers=headers)

    @task(1)
    def refresh_token(self):
        """Refresh token."""

        if not self.auth_token:
            return

        # This would need a refresh token from the login response
        # For now, just test the endpoint exists
        self.client.post("/auth/refresh", json={"refresh_token": "dummy"})


# Additional configuration for different test scenarios
class UATPReadOnlyUser(HttpUser):
    """User that only performs read operations."""

    wait_time = between(1, 2)

    @task(10)
    def list_capsules(self):
        """List capsules."""
        self.client.get("/api/capsules")

    @task(5)
    def search_capsules(self):
        """Search capsules."""
        search_terms = ["test", "capsule", "message"]
        params = {"q": random.choice(search_terms)}
        self.client.get("/api/capsules/search", params=params)

    @task(2)
    def get_stats(self):
        """Get statistics."""
        self.client.get("/api/capsules/stats")

    @task(1)
    def health_check(self):
        """Health check."""
        self.client.get("/health")


class UATPWriteHeavyUser(HttpUser):
    """User that performs mostly write operations."""

    wait_time = between(0.5, 1.5)

    def on_start(self):
        """Called when user starts."""
        self.user_id = f"write_heavy_user_{random.randint(1000, 9999)}"

    @task(8)
    def create_capsule(self):
        """Create capsules frequently."""

        capsule_data = {
            "capsule_id": f"write_heavy_{self.user_id}_{int(time.time() * 1000)}",
            "type": "interaction_capsule",
            "platform": "write_test",
            "user_id": self.user_id,
            "user_message": f"Write heavy test message {random.randint(1, 1000)}",
            "ai_response": f"Write heavy response {random.randint(1, 1000)}",
            "significance_score": random.uniform(1.0, 3.0),
            "timestamp": datetime.now().isoformat(),
        }

        self.client.post("/api/capsules", json=capsule_data)

    @task(1)
    def list_capsules(self):
        """Occasionally list capsules."""
        self.client.get("/api/capsules", params={"limit": 10})

    @task(1)
    def health_check(self):
        """Health check."""
        self.client.get("/health")


# Usage examples:
#
# Basic load test:
# locust -f locustfile.py --host=http://localhost:8000
#
# Specific user class:
# locust -f locustfile.py --host=http://localhost:8000 UATPReadOnlyUser
#
# Custom load pattern:
# locust -f locustfile.py --host=http://localhost:8000 --users=50 --spawn-rate=5 --run-time=5m
#
# Headless mode:
# locust -f locustfile.py --host=http://localhost:8000 --headless --users=20 --spawn-rate=2 --run-time=2m
