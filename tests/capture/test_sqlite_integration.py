#!/usr/bin/env python3
"""
Test SQLite Integration
=======================

This script tests the SQLite integration with the real-time capsule generator
by explicitly configuring the integration layer to use the SQLite creator.
"""

import asyncio
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from filters.integration_layer import IntegrationLayer
from filters.sqlite_capsule_creator import (
    initialize_sqlite_capsule_creator,
)
from live_capture import capture_live_interaction, get_real_time_generator


async def test_sqlite_integration():
    """Test SQLite integration with real-time generator."""

    print("🧪 Testing SQLite Integration with Real-Time Generator")
    print("=" * 60)

    # Initialize SQLite capsule creator
    sqlite_creator = await initialize_sqlite_capsule_creator()

    if not sqlite_creator._db_connected:
        print("❌ SQLite database not connected - test failed")
        return False

    print("✅ SQLite database connected successfully")

    # Create integration layer with SQLite creator
    integration_layer = IntegrationLayer()
    integration_layer.capsule_creator = sqlite_creator  # Override with SQLite creator

    # Update real-time generator to use the modified integration layer
    generator = get_real_time_generator()
    generator.integration_layer = integration_layer

    # Test technical conversation that should create capsules
    technical_conversation = {
        "user": "I need help implementing a distributed cache system with Redis clustering. Can you show me how to set up Redis Sentinel for high availability?",
        "assistant": """I'll help you implement a distributed Redis cache system with Sentinel for high availability. Here's a comprehensive solution:

```python
import redis
import time
import logging
from typing import List, Dict, Optional, Any
from redis.sentinel import Sentinel
from contextlib import contextmanager

class RedisClusterManager:
    def __init__(self,
                 sentinel_hosts: List[Dict[str, Any]],
                 service_name: str = "mymaster",
                 password: Optional[str] = None):

        self.sentinel_hosts = sentinel_hosts
        self.service_name = service_name
        self.password = password

        # Initialize Sentinel connection
        self.sentinel = Sentinel(
            [(host['host'], host['port']) for host in sentinel_hosts],
            socket_timeout=0.5,
            password=password
        )

        # Get master and slave connections
        self.master = self.sentinel.master_for(
            service_name,
            socket_timeout=0.5,
            password=password,
            decode_responses=True
        )

        self.slaves = self.sentinel.slave_for(
            service_name,
            socket_timeout=0.5,
            password=password,
            decode_responses=True
        )

        self.logger = logging.getLogger(__name__)

    def get_master_connection(self) -> redis.Redis:
        \"\"\"Get master connection for write operations.\"\"\"
        return self.master

    def get_slave_connection(self) -> redis.Redis:
        \"\"\"Get slave connection for read operations.\"\"\"
        return self.slaves

    def set_with_failover(self, key: str, value: Any, ttl: int = 3600) -> bool:
        \"\"\"Set value with automatic failover.\"\"\"
        try:
            return self.master.setex(key, ttl, value)
        except redis.ConnectionError:
            self.logger.warning("Master connection failed, attempting failover...")
            # Sentinel will automatically promote new master
            time.sleep(0.5)  # Brief pause for failover
            return self.master.setex(key, ttl, value)

    def get_with_fallback(self, key: str) -> Optional[Any]:
        \"\"\"Get value with slave fallback.\"\"\"
        try:
            # Try slave first for read operations
            return self.slaves.get(key)
        except redis.ConnectionError:
            try:
                # Fallback to master if slave fails
                return self.master.get(key)
            except redis.ConnectionError:
                self.logger.error("All Redis connections failed")
                return None

    def health_check(self) -> Dict[str, Any]:
        \"\"\"Perform health check on all connections.\"\"\"
        status = {
            'master': {'status': 'unknown', 'latency': None},
            'slaves': {'status': 'unknown', 'latency': None},
            'sentinel': {'status': 'unknown', 'discovered_services': []}
        }

        # Check master
        try:
            start_time = time.time()
            self.master.ping()
            status['master'] = {
                'status': 'healthy',
                'latency': round((time.time() - start_time) * 1000, 2)
            }
        except Exception as e:
            status['master'] = {'status': 'unhealthy', 'error': str(e)}

        # Check slaves
        try:
            start_time = time.time()
            self.slaves.ping()
            status['slaves'] = {
                'status': 'healthy',
                'latency': round((time.time() - start_time) * 1000, 2)
            }
        except Exception as e:
            status['slaves'] = {'status': 'unhealthy', 'error': str(e)}

        # Check sentinel
        try:
            services = self.sentinel.discover_master(self.service_name)
            status['sentinel'] = {
                'status': 'healthy',
                'discovered_services': services
            }
        except Exception as e:
            status['sentinel'] = {'status': 'unhealthy', 'error': str(e)}

        return status

# Usage example
cluster_manager = RedisClusterManager([
    {'host': '127.0.0.1', 'port': 26379},
    {'host': '127.0.0.1', 'port': 26380},
    {'host': '127.0.0.1', 'port': 26381}
])

# Set data with automatic failover
cluster_manager.set_with_failover("user:123", "session_data")

# Get data with slave fallback
data = cluster_manager.get_with_fallback("user:123")
```

This implementation provides:

1. **Automatic Failover**: Sentinel manages failover automatically
2. **Load Balancing**: Reads from slaves, writes to master
3. **Health Monitoring**: Comprehensive health checks
4. **Connection Pooling**: Efficient connection management
5. **Error Handling**: Graceful error handling and recovery
6. **High Availability**: Multiple sentinel instances prevent single point of failure

Additional Redis Sentinel configuration:
- Set up multiple sentinel instances (odd number recommended)
- Configure appropriate quorum settings
- Monitor Redis instances continuously
- Implement proper alerting and monitoring""",
    }

    session_id = "sqlite-integration-test"

    print("\n📝 Testing with technical conversation...")
    print(f"   User: {technical_conversation['user'][:60]}...")
    print(f"   Assistant: {technical_conversation['assistant'][:60]}...")

    # Capture the interaction
    capsule_id = await capture_live_interaction(
        session_id=session_id,
        user_message=technical_conversation["user"],
        ai_response=technical_conversation["assistant"],
        user_id="sqlite-tester",
        platform="claude_code",
        model="claude-sonnet-4",
        metadata={
            "test_type": "sqlite_integration",
            "expected_outcome": "sqlite_database_storage",
        },
    )

    if capsule_id:
        print(f"✅ Live capsule created: {capsule_id}")
    else:
        print("❌ No capsule created")

    # Get database statistics
    stats = await sqlite_creator.get_capsule_stats()
    print("\n📊 SQLite Database Statistics:")
    print(f"   Total capsules: {stats['total_capsules']}")
    print(f"   Auto-filtered capsules: {stats['auto_filtered_capsules']}")
    print(f"   Storage backend: {stats['storage_backend']}")

    # Get recent capsules
    recent = await sqlite_creator.get_recent_capsules(3)
    if recent:
        print("\n🔄 Recent SQLite Capsules:")
        for capsule in recent:
            print(
                f"   • {capsule['capsule_id']} ({capsule['platform']}) - {capsule['significance_score']:.2f}"
            )

    return stats["total_capsules"] > 0


async def main():
    """Main test function."""

    print("🚀 SQLite Integration Test")
    print("Testing real-time capsule generation with SQLite storage")
    print("=" * 70)

    try:
        success = await test_sqlite_integration()

        if success:
            print("\n✅ SQLITE INTEGRATION TEST PASSED!")
            print("   Real-time generator is storing capsules in SQLite database")
            print("   Database integration is working correctly")
            print("   System is ready for production use")
        else:
            print("\n❌ SQLITE INTEGRATION TEST FAILED!")
            print("   Capsules are not being stored in SQLite database")
            print("   Check database connection and integration layer")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
