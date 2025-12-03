#!/usr/bin/env python3
"""
UATP Capsule API Client Test
============================

This script tests the UATP Capsule API endpoints to ensure they're working correctly.
"""

import asyncio
import aiohttp
import json
import sys
from datetime import datetime, timedelta


class UATPAPIClient:
    """Simple API client for testing UATP Capsule API."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def get_health(self):
        """Test health check endpoint."""
        async with self.session.get(f"{self.base_url}/api/health") as response:
            return await response.json(), response.status

    async def get_capsules(self, **params):
        """Test get capsules endpoint."""
        async with self.session.get(
            f"{self.base_url}/api/capsules", params=params
        ) as response:
            return await response.json(), response.status

    async def get_capsule(self, capsule_id: str):
        """Test get specific capsule endpoint."""
        async with self.session.get(
            f"{self.base_url}/api/capsules/{capsule_id}"
        ) as response:
            return await response.json(), response.status

    async def search_capsules(self, search_data: dict):
        """Test search capsules endpoint."""
        async with self.session.post(
            f"{self.base_url}/api/capsules/search",
            json=search_data,
            headers={"Content-Type": "application/json"},
        ) as response:
            return await response.json(), response.status

    async def get_stats(self):
        """Test stats endpoint."""
        async with self.session.get(f"{self.base_url}/api/capsules/stats") as response:
            return await response.json(), response.status

    async def get_recent(self, limit: int = 5):
        """Test recent capsules endpoint."""
        async with self.session.get(
            f"{self.base_url}/api/capsules/recent", params={"limit": limit}
        ) as response:
            return await response.json(), response.status


async def test_api_endpoints():
    """Test all API endpoints."""

    print("🧪 Testing UATP Capsule API Endpoints")
    print("=" * 40)

    async with UATPAPIClient() as client:
        # Test health check
        print("\n1. Health Check")
        try:
            health_data, status = await client.get_health()
            print(f"   Status: {status}")
            print(f"   Health: {health_data.get('status', 'unknown')}")
            print(
                f"   Database: {health_data.get('database', {}).get('connected', False)}"
            )
        except Exception as e:
            print(f"   ❌ Error: {e}")

        # Test get capsules
        print("\n2. Get Capsules")
        try:
            capsules_data, status = await client.get_capsules(limit=5)
            print(f"   Status: {status}")
            print(f"   Capsules: {len(capsules_data.get('capsules', []))}")
            print(
                f"   Total: {capsules_data.get('pagination', {}).get('total_count', 0)}"
            )
        except Exception as e:
            print(f"   ❌ Error: {e}")

        # Test get specific capsule
        print("\n3. Get Specific Capsule")
        try:
            capsules_data, _ = await client.get_capsules(limit=1)
            if capsules_data.get("capsules"):
                first_capsule_id = capsules_data["capsules"][0]["capsule_id"]
                capsule_data, status = await client.get_capsule(first_capsule_id)
                print(f"   Status: {status}")
                print(f"   Capsule ID: {capsule_data.get('capsule_id', 'unknown')}")
                print(f"   Platform: {capsule_data.get('platform', 'unknown')}")
            else:
                print("   ⚠️ No capsules available for testing")
        except Exception as e:
            print(f"   ❌ Error: {e}")

        # Test search
        print("\n4. Search Capsules")
        try:
            search_data = {
                "query": "code",
                "filters": {
                    "platforms": ["claude_code", "windsurf"],
                    "significance_range": {"min": 0.5},
                },
                "sort_by": "significance",
                "sort_order": "desc",
                "limit": 3,
            }
            search_results, status = await client.search_capsules(search_data)
            print(f"   Status: {status}")
            print(f"   Results: {len(search_results.get('capsules', []))}")
            print(
                f"   Total: {search_results.get('pagination', {}).get('total_count', 0)}"
            )
        except Exception as e:
            print(f"   ❌ Error: {e}")

        # Test stats
        print("\n5. Get Statistics")
        try:
            stats_data, status = await client.get_stats()
            print(f"   Status: {status}")
            basic_stats = stats_data.get("basic_stats", {})
            print(f"   Total Capsules: {basic_stats.get('total_capsules', 0)}")
            print(
                f"   Storage Backend: {basic_stats.get('storage_backend', 'unknown')}"
            )

            analytics = stats_data.get("analytics", {})
            platforms = analytics.get("platforms", {})
            print(f"   Platforms: {list(platforms.keys())}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

        # Test recent capsules
        print("\n6. Get Recent Capsules")
        try:
            recent_data, status = await client.get_recent(limit=3)
            print(f"   Status: {status}")
            print(f"   Recent: {len(recent_data.get('capsules', []))}")

            for capsule in recent_data.get("capsules", [])[:2]:
                print(
                    f"   • {capsule.get('capsule_id', 'unknown')[:20]}... ({capsule.get('platform', 'unknown')})"
                )
        except Exception as e:
            print(f"   ❌ Error: {e}")

        # Test filtering
        print("\n7. Test Filtering")
        try:
            filtered_data, status = await client.get_capsules(
                platform="claude_code", min_significance=1.0, limit=3
            )
            print(f"   Status: {status}")
            print(f"   Filtered Results: {len(filtered_data.get('capsules', []))}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

    print("\n✅ API testing completed!")


if __name__ == "__main__":
    asyncio.run(test_api_endpoints())
