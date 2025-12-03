#!/usr/bin/env python3
"""
Test script for UATP Production API

Tests the new mobile and WebAuthn endpoints.
"""

import asyncio
import json

import httpx


API_BASE = "http://localhost:9090"
API_KEY = "test-api-key"

headers = {"Content-Type": "application/json", "X-API-Key": API_KEY}


async def test_mobile_health():
    """Test mobile health endpoint."""
    print("\n🔍 Testing Mobile Health Endpoint...")

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE}/api/v1/mobile/health")

        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "capabilities" in data

    print("✅ Mobile health check passed")


async def test_mobile_single_capsule():
    """Test single capsule creation from mobile."""
    print("\n🔍 Testing Mobile Single Capsule Creation...")

    payload = {
        "device_id": "test-device-001",
        "platform": "ios",
        "messages": [
            {
                "role": "user",
                "content": "What is the capital of France?",
                "timestamp": "2025-01-15T10:00:00Z",
            },
            {
                "role": "assistant",
                "content": "The capital of France is Paris.",
                "timestamp": "2025-01-15T10:00:02Z",
            },
        ],
        "metadata": {"app_version": "1.0.0", "os_version": "iOS 17.2"},
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE}/api/v1/mobile/capture/single", headers=headers, json=payload
        )

        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "capsule_id" in data
        assert data["status"] == "sealed"

    print("✅ Mobile capsule creation passed")
    return data["capsule_id"]


async def test_mobile_batch_capsules():
    """Test batch capsule submission."""
    print("\n🔍 Testing Mobile Batch Capsule Submission...")

    payload = {
        "device_id": "test-device-002",
        "capsules": [
            {
                "client_id": "offline-001",
                "messages": [
                    {"role": "user", "content": "Test 1"},
                    {"role": "assistant", "content": "Response 1"},
                ],
            },
            {
                "client_id": "offline-002",
                "messages": [
                    {"role": "user", "content": "Test 2"},
                    {"role": "assistant", "content": "Response 2"},
                ],
            },
            {
                "client_id": "offline-003",
                "messages": [
                    {"role": "user", "content": "Test 3"},
                    {"role": "assistant", "content": "Response 3"},
                ],
            },
        ],
        "metadata": {"offline_duration_seconds": 300},
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE}/api/v1/mobile/capture/batch", headers=headers, json=payload
        )

        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")

        assert response.status_code in [200, 207]  # 200 all success, 207 partial
        data = response.json()
        assert data["total_submitted"] == 3
        assert data["successful"] + data["failed"] == 3

    print("✅ Batch capsule submission passed")


async def test_mobile_list_capsules():
    """Test listing capsules for mobile."""
    print("\n🔍 Testing Mobile Capsule List...")

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE}/api/v1/mobile/capsules/list?page=0&limit=10", headers=headers
        )

        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "capsules" in data
        assert "page" in data

    print("✅ Mobile capsule list passed")


async def test_mobile_stats():
    """Test mobile stats endpoint."""
    print("\n🔍 Testing Mobile Stats...")

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE}/api/v1/mobile/stats", headers=headers)

        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "stats" in data

    print("✅ Mobile stats passed")


async def test_webauthn_health():
    """Test WebAuthn health endpoint."""
    print("\n🔍 Testing WebAuthn Health...")

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE}/api/v1/webauthn/health")

        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "rp_id" in data

    print("✅ WebAuthn health check passed")


async def test_webauthn_registration_begin():
    """Test WebAuthn registration initiation."""
    print("\n🔍 Testing WebAuthn Registration Begin...")

    payload = {
        "user_id": "test-user-001",
        "user_name": "test@example.com",
        "user_display_name": "Test User",
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE}/api/v1/webauthn/register/begin", headers=headers, json=payload
        )

        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "options" in data
        assert "challenge" in data["options"]

    print("✅ WebAuthn registration begin passed")
    return data["options"]["challenge"]


async def test_webauthn_authentication_begin():
    """Test WebAuthn authentication initiation."""
    print("\n🔍 Testing WebAuthn Authentication Begin...")

    payload = {"user_id": "test-user-001"}

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE}/api/v1/webauthn/authenticate/begin", json=payload
        )

        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "options" in data

    print("✅ WebAuthn authentication begin passed")


async def run_all_tests():
    """Run all API tests."""
    print("=" * 60)
    print("UATP Production API Test Suite")
    print("=" * 60)

    try:
        # Mobile API tests
        await test_mobile_health()
        capsule_id = await test_mobile_single_capsule()
        await test_mobile_batch_capsules()
        await test_mobile_list_capsules()
        await test_mobile_stats()

        # WebAuthn API tests
        await test_webauthn_health()
        challenge = await test_webauthn_registration_begin()
        await test_webauthn_authentication_begin()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print(f"\n📊 Summary:")
        print(f"  - Mobile API: 5/5 tests passed")
        print(f"  - WebAuthn API: 3/3 tests passed")
        print(f"  - Created capsule: {capsule_id}")
        print(f"  - WebAuthn challenge: {challenge[:20]}...")

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        raise
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        raise


if __name__ == "__main__":
    print("\n🚀 Starting UATP API tests...")
    print("📝 Make sure the server is running on http://localhost:9090\n")

    asyncio.run(run_all_tests())
