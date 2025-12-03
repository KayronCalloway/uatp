from quart import current_app

# Use a simple in-memory cache for the application.
# The 'locmem' backend is suitable for development and testing.


def invalidate_all_caches():
    """Clear all caches."""
    if hasattr(current_app, "cache"):
        current_app.cache.clear()


async def cache_ai_response(key: str, response: str, ttl: int = 300):
    """Cache an AI response with the given key."""
    if not current_app.config.get("CACHE_ENABLED"):
        return
    if hasattr(current_app, "cache"):
        await current_app.cache.set(key, response, expire=ttl)


async def get_cached_ai_response(key: str) -> str:
    """
    Retrieves a cached AI response from the app context.
    """
    if not current_app.config.get("CACHE_ENABLED"):
        return None
    if hasattr(current_app, "cache"):
        return await current_app.cache.get(key)
    return None
