"""
Mock Cache implementation for testing.
"""


class MockCache:
    """A simple in-memory cache for testing."""

    def __init__(self):
        self._cache = {}

    async def get(self, key):
        """Get a value from the cache."""
        return self._cache.get(key)

    async def set(self, key, value, expire=None):
        """Set a value in the cache with optional expiration."""
        self._cache[key] = value

    async def delete(self, key):
        """Delete a key from the cache."""
        if key in self._cache:
            del self._cache[key]

    async def clear(self):
        """Clear all values from the cache."""
        self._cache = {}

    async def connect(self):
        """Mock connection method."""
        pass

    async def disconnect(self):
        """Mock disconnection method."""
        pass
