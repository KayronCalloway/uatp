#!/usr/bin/env python3
"""
Test Live Capture with Technical Conversation
=============================================

This tests the real-time capsule generation with a technical conversation
that should trigger capsule creation.
"""

import asyncio
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from live_capture import capture_live_interaction, get_real_time_generator


async def test_technical_conversation():
    """Test live capture with a technical conversation."""

    print(" Testing Live Capture with Technical Conversation")
    print("=" * 60)

    generator = get_real_time_generator()

    # Add callbacks for monitoring
    async def on_capsule_created(interaction, capsule_id):
        print(f" LIVE CAPSULE CREATED: {capsule_id}")
        print(f"   Session: {interaction.session_id}")
        print(f"   Platform: {interaction.platform}")
        print(f"   User: {interaction.user_id}")
        print(f"   Auto-encapsulated: {interaction.auto_encapsulated}")

    async def on_interaction_captured(interaction, messages):
        print(f" Interaction captured - Session: {interaction.session_id}")
        print(f"   Total messages: {len(interaction.messages)}")

    generator.add_callback("capsule_created", on_capsule_created)
    generator.add_callback("interaction_captured", on_interaction_captured)

    session_id = "live-technical-session"

    # Start session
    await generator.start_session(
        session_id=session_id,
        user_id="developer",
        platform="claude_code",
        context={"model": "claude-sonnet-4", "interface": "claude_code"},
    )

    print(f"\n Started live session: {session_id}")

    # Technical conversation that should create capsules
    technical_exchanges = [
        {
            "user": "I need help implementing a distributed cache system using Redis with Python. Can you show me how to create a cache layer with failover support?",
            "assistant": """I'll help you implement a distributed cache system with Redis and failover support. Here's a comprehensive solution:

```python
import redis
import time
import logging
from typing import Any, Optional, List, Dict
from redis.sentinel import Sentinel
from contextlib import contextmanager

class DistributedCache:
    def __init__(self,
                 redis_hosts: List[Dict[str, Any]],
                 sentinel_hosts: Optional[List[Dict[str, Any]]] = None,
                 service_name: str = "mymaster",
                 db: int = 0,
                 decode_responses: bool = True):

        self.redis_hosts = redis_hosts
        self.sentinel_hosts = sentinel_hosts
        self.service_name = service_name
        self.db = db
        self.decode_responses = decode_responses

        # Connection pools
        self.primary_pool = None
        self.replica_pools = []
        self.sentinel = None

        # Initialize connections
        self._setup_connections()

        # Health check
        self.last_health_check = time.time()
        self.health_check_interval = 30  # seconds

    def _setup_connections(self):
        if self.sentinel_hosts:
            # Use Redis Sentinel for high availability
            self.sentinel = Sentinel(
                [(host['host'], host['port']) for host in self.sentinel_hosts],
                socket_timeout=0.5
            )

            # Get master connection
            self.primary_pool = self.sentinel.master_for(
                self.service_name,
                socket_timeout=0.5,
                db=self.db,
                decode_responses=self.decode_responses
            )

            # Get replica connections
            try:
                replica_client = self.sentinel.slave_for(
                    self.service_name,
                    socket_timeout=0.5,
                    db=self.db,
                    decode_responses=self.decode_responses
                )
                self.replica_pools.append(replica_client)
            except Exception as e:
                logging.warning(f"No replicas available: {e}")

        else:
            # Direct Redis connection with manual failover
            for i, host_config in enumerate(self.redis_hosts):
                try:
                    pool = redis.ConnectionPool(
                        host=host_config['host'],
                        port=host_config['port'],
                        db=self.db,
                        decode_responses=self.decode_responses,
                        max_connections=10
                    )

                    client = redis.Redis(connection_pool=pool)
                    client.ping()  # Test connection

                    if i == 0:
                        self.primary_pool = client
                    else:
                        self.replica_pools.append(client)

                except Exception as e:
                    logging.error(f"Failed to connect to {host_config}: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        try:
            value = self.primary_pool.get(key)
            return value if value is not None else default
        except Exception as e:
            logging.error(f"Cache get failed for key {key}: {e}")
            return default

    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        try:
            return self.primary_pool.setex(key, ttl, value)
        except Exception as e:
            logging.error(f"Cache set failed for key {key}: {e}")
            return False
```

This implementation provides:

1. **Failover Support**: Automatic failover between Redis instances
2. **Sentinel Integration**: Uses Redis Sentinel for high availability
3. **Read Replicas**: Distributes read operations across replicas
4. **Health Monitoring**: Built-in health checks and monitoring
5. **Connection Pooling**: Efficient connection management
6. **Error Handling**: Comprehensive error handling and logging""",
        },
        {
            "user": "That's excellent! Now can you show me how to implement a distributed locking mechanism using Redis to ensure data consistency across multiple instances?",
            "assistant": """Great follow-up! Here's a robust distributed locking mechanism using Redis with the Redlock algorithm:

```python
import redis
import time
import uuid
import threading
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
import logging

class RedisDistributedLock:
    def __init__(self,
                 redis_clients: List[redis.Redis],
                 lock_name: str,
                 ttl: int = 30,
                 retry_delay: float = 0.1,
                 retry_count: int = 3):

        self.redis_clients = redis_clients
        self.lock_name = lock_name
        self.ttl = ttl
        self.retry_delay = retry_delay
        self.retry_count = retry_count

        # Generate unique lock identifier
        self.lock_identifier = str(uuid.uuid4())

        # Minimum number of Redis instances that must acquire the lock
        self.quorum = len(redis_clients) // 2 + 1

        # Lock state
        self.acquired_locks = []
        self.lock_acquired = False

        logging.info(f"Distributed lock initialized: {lock_name}")
        logging.info(f"Quorum required: {self.quorum}/{len(redis_clients)}")

    def acquire(self, timeout: Optional[float] = None) -> bool:
        start_time = time.time()

        while True:
            # Try to acquire lock on all Redis instances
            acquired_count = 0
            acquired_instances = []

            for i, client in enumerate(self.redis_clients):
                try:
                    # Use SET with NX (not exists) and EX (expiry)
                    if self._acquire_single_lock(client, i):
                        acquired_count += 1
                        acquired_instances.append(i)
                except Exception as e:
                    logging.warning(f"Failed to acquire lock on Redis instance {i}: {e}")

            # Check if we have quorum
            if acquired_count >= self.quorum:
                self.acquired_locks = acquired_instances
                self.lock_acquired = True
                logging.info(f"Lock acquired on {acquired_count}/{len(self.redis_clients)} instances")
                return True

            # Failed to acquire quorum, release any acquired locks
            self._release_partial_locks(acquired_instances)

            # Check timeout
            if timeout and (time.time() - start_time) >= timeout:
                logging.warning(f"Lock acquisition timeout after {timeout}s")
                return False

            # Wait before retry
            time.sleep(self.retry_delay)

    def _acquire_single_lock(self, client: redis.Redis, instance_id: int) -> bool:
        lua_script = '''
        if redis.call("exists", KEYS[1]) == 0 then
            redis.call("setex", KEYS[1], ARGV[1], ARGV[2])
            return 1
        else
            return 0
        end
        '''

        try:
            result = client.eval(lua_script, 1, self.lock_name, self.ttl, self.lock_identifier)
            return bool(result)
        except Exception as e:
            logging.error(f"Error acquiring lock on instance {instance_id}: {e}")
            return False

    def release(self) -> bool:
        if not self.lock_acquired:
            return True

        released_count = 0

        for instance_id in self.acquired_locks:
            try:
                if self._release_single_lock(self.redis_clients[instance_id], instance_id):
                    released_count += 1
            except Exception as e:
                logging.warning(f"Failed to release lock on instance {instance_id}: {e}")

        self.lock_acquired = False
        self.acquired_locks = []

        logging.info(f"Lock released on {released_count}/{len(self.acquired_locks)} instances")
        return released_count > 0

    def _release_single_lock(self, client: redis.Redis, instance_id: int) -> bool:
        lua_script = '''
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        '''

        try:
            result = client.eval(lua_script, 1, self.lock_name, self.lock_identifier)
            return bool(result)
        except Exception as e:
            logging.error(f"Error releasing lock on instance {instance_id}: {e}")
            return False
```

This distributed locking implementation provides:

1. **Redlock Algorithm**: Implements the Redis Redlock algorithm for distributed locking
2. **Quorum-based**: Requires majority of Redis instances to acquire lock
3. **Atomic Operations**: Uses Lua scripts for atomic lock operations
4. **Fault Tolerance**: Handles Redis instance failures gracefully
5. **Lock Extension**: Ability to extend lock duration
6. **Deadlock Prevention**: Guidelines for lock ordering
7. **Monitoring**: Built-in statistics and monitoring

Key features:
- **Consistency**: Ensures data consistency across distributed systems
- **Availability**: Continues working even if some Redis instances fail
- **Partition Tolerance**: Handles network partitions gracefully
- **Context Manager**: Easy-to-use context manager interface""",
        },
    ]

    created_capsules = []

    for i, exchange in enumerate(technical_exchanges, 1):
        print(f"\n Exchange {i}: Capturing technical conversation...")
        print(f"   User: {exchange['user'][:80]}...")
        print(f"   Assistant: {exchange['assistant'][:80]}...")

        capsule_id = await capture_live_interaction(
            session_id=session_id,
            user_message=exchange["user"],
            ai_response=exchange["assistant"],
            user_id="developer",
            platform="claude_code",
            model="claude-sonnet-4",
            metadata={
                "conversation_type": "technical_implementation",
                "exchange_number": i,
                "topic": "distributed_systems",
            },
        )

        if capsule_id:
            created_capsules.append(capsule_id)
            print(f"   [OK] Created capsule: {capsule_id}")
        else:
            print("   [ERROR] No capsule created")

    # End session
    await generator.end_session(session_id)

    # Show final results
    print("\n" + "=" * 60)
    print(" LIVE CAPTURE RESULTS")
    print("=" * 60)

    stats = generator.get_stats()
    print(f"Total interactions processed: {stats['total_interactions']}")
    print(f"Total capsules created: {len(created_capsules)}")
    print(
        f"Live capsule generation rate: {len(created_capsules)/len(technical_exchanges)*100:.1f}%"
    )

    if created_capsules:
        print(f"\n[OK] Successfully created {len(created_capsules)} live capsules:")
        for capsule_id in created_capsules:
            print(f"   • {capsule_id}")
    else:
        print("\n[WARN]  No capsules were created from live interactions")

    return created_capsules


if __name__ == "__main__":
    asyncio.run(test_technical_conversation())
