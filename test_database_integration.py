#!/usr/bin/env python3
"""
Test Database Integration
========================

This script tests the database integration with the real-time capsule generator.
"""

import asyncio
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from filters.sqlite_capsule_creator import (
    get_sqlite_capsule_creator,
    initialize_sqlite_capsule_creator,
)
from live_capture import get_real_time_generator, capture_live_interaction


async def test_database_integration():
    """Test database integration with real-time generator."""

    print("🧪 Testing Database Integration with Real-Time Generator")
    print("=" * 60)

    # Initialize SQLite capsule creator
    creator = await initialize_sqlite_capsule_creator()

    if not creator._db_connected:
        print("❌ Database not connected - test failed")
        return False

    print("✅ Database connected successfully")

    # Update real-time generator to use database creator
    generator = get_real_time_generator()

    # Test technical conversation that should create capsules
    technical_conversation = {
        "user": "I need help implementing a Redis-based session store for my web application. Can you show me how to create a secure session management system?",
        "assistant": """I'll help you implement a secure Redis-based session store. Here's a comprehensive solution:

```python
import redis
import json
import secrets
import hashlib
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Any

class RedisSessionStore:
    def __init__(self, redis_host='localhost', redis_port=6379, redis_db=0):
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            decode_responses=True
        )
        self.session_prefix = 'session:'
        self.default_ttl = 3600  # 1 hour
        
    def generate_session_id(self) -> str:
        # Generate cryptographically secure session ID
        random_bytes = secrets.token_bytes(32)
        timestamp = str(int(time.time()))
        hash_input = random_bytes + timestamp.encode()
        return hashlib.sha256(hash_input).hexdigest()
    
    def create_session(self, user_data: Dict[str, Any], ttl: int = None) -> str:
        session_id = self.generate_session_id()
        session_key = f"{self.session_prefix}{session_id}"
        
        session_data = {
            'user_data': user_data,
            'created_at': datetime.now().isoformat(),
            'last_accessed': datetime.now().isoformat(),
            'ip_address': user_data.get('ip_address'),
            'user_agent': user_data.get('user_agent')
        }
        
        ttl = ttl or self.default_ttl
        self.redis_client.setex(
            session_key, 
            ttl, 
            json.dumps(session_data)
        )
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        session_key = f"{self.session_prefix}{session_id}"
        session_data = self.redis_client.get(session_key)
        
        if session_data:
            data = json.loads(session_data)
            # Update last accessed time
            data['last_accessed'] = datetime.now().isoformat()
            self.redis_client.setex(
                session_key, 
                self.default_ttl, 
                json.dumps(data)
            )
            return data
        
        return None
    
    def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        session_data = self.get_session(session_id)
        if session_data:
            session_data['user_data'].update(updates)
            session_key = f"{self.session_prefix}{session_id}"
            self.redis_client.setex(
                session_key, 
                self.default_ttl, 
                json.dumps(session_data)
            )
            return True
        return False
    
    def destroy_session(self, session_id: str) -> bool:
        session_key = f"{self.session_prefix}{session_id}"
        return bool(self.redis_client.delete(session_key))
    
    def cleanup_expired_sessions(self) -> int:
        # Redis handles expiration automatically, but we can clean up manually
        pattern = f"{self.session_prefix}*"
        keys = self.redis_client.keys(pattern)
        
        expired_count = 0
        for key in keys:
            ttl = self.redis_client.ttl(key)
            if ttl == -1:  # No expiration set
                self.redis_client.expire(key, self.default_ttl)
            elif ttl == -2:  # Key doesn't exist
                expired_count += 1
        
        return expired_count

# Usage example
session_store = RedisSessionStore()

# Create session
user_data = {
    'user_id': 123,
    'username': 'john_doe',
    'email': 'john@example.com',
    'ip_address': '192.168.1.100',
    'user_agent': 'Mozilla/5.0...'
}

session_id = session_store.create_session(user_data)
print(f"Created session: {session_id}")

# Get session
session = session_store.get_session(session_id)
if session:
    print(f"Session data: {session['user_data']}")

# Update session
session_store.update_session(session_id, {'last_action': 'login'})

# Destroy session
session_store.destroy_session(session_id)
```

This implementation provides:

1. **Secure Session IDs**: Uses cryptographically secure random generation
2. **Automatic Expiration**: Redis TTL handles session expiration
3. **Session Management**: Create, read, update, delete operations
4. **Security Features**: IP and user agent tracking
5. **Cleanup**: Automatic and manual cleanup of expired sessions
6. **JSON Storage**: Structured session data storage

Additional security considerations:
- Use HTTPS to protect session IDs in transit
- Implement session rotation after privilege escalation
- Add rate limiting to prevent session fixation attacks
- Consider using Redis AUTH for additional security""",
    }

    session_id = "database-integration-test"

    print(f"\n📝 Testing with technical conversation...")
    print(f"   User: {technical_conversation['user'][:60]}...")
    print(f"   Assistant: {technical_conversation['assistant'][:60]}...")

    # Capture the interaction
    capsule_id = await capture_live_interaction(
        session_id=session_id,
        user_message=technical_conversation["user"],
        ai_response=technical_conversation["assistant"],
        user_id="database-tester",
        platform="claude_code",
        model="claude-sonnet-4",
        metadata={
            "test_type": "database_integration",
            "expected_outcome": "database_capsule_creation",
        },
    )

    if capsule_id:
        print(f"✅ Live capsule created: {capsule_id}")
    else:
        print(f"❌ No capsule created")

    # Get database statistics
    stats = await creator.get_capsule_stats()
    print(f"\n📊 Database Statistics:")
    print(f"   Total capsules: {stats['total_capsules']}")
    print(f"   Auto-filtered capsules: {stats['auto_filtered_capsules']}")
    print(f"   Storage backend: {stats['storage_backend']}")

    # Get recent capsules
    recent = await creator.get_recent_capsules(3)
    if recent:
        print(f"\n🔄 Recent Database Capsules:")
        for capsule in recent:
            print(
                f"   • {capsule['capsule_id']} ({capsule['platform']}) - {capsule['significance_score']:.2f}"
            )

    return stats["total_capsules"] > 0


async def main():
    """Main test function."""

    print("🚀 Database Integration Test")
    print("Testing real-time capsule generation with database storage")
    print("=" * 70)

    try:
        success = await test_database_integration()

        if success:
            print(f"\n✅ DATABASE INTEGRATION TEST PASSED!")
            print(f"   Real-time generator is working with database storage")
            print(f"   Capsules are being stored in SQLite database")
            print(f"   System is ready for production use")
        else:
            print(f"\n❌ DATABASE INTEGRATION TEST FAILED!")
            print(f"   Check database connection and configuration")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
