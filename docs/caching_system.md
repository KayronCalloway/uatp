# UATP Capsule Engine Caching System

## Overview

The UATP Capsule Engine implements a thread-safe, configurable caching system to optimize performance and reduce memory usage. The caching system helps mitigate the O(n) memory growth identified in the security audit by minimizing redundant operations such as chain loading and cryptographic verification.

## Architecture

The caching system is built around a Least Recently Used (LRU) cache with Time-To-Live (TTL) support. Key components include:

1. **Core Cache Module** (`api/cache.py`): Implements the base caching functionality including:
   - Thread-safe LRU cache with TTL support
   - Decorators for easy function result caching
   - Helper functions for chain and verification caching

2. **API Integration** (`api/server.py`): Applies caching to key API endpoints:
   - `list_capsules`: Caches chain data for 30 seconds
   - `get_capsule`: Caches capsule retrieval for 60 seconds
   - `verify_capsule`: Caches verification results for 5 minutes
   - `get_capsule_stats`: Caches statistics for 2 minutes
   - `get_chain_forks`: Caches fork analysis for 5 minutes

3. **Cache Invalidation**: Automatic invalidation when the chain is modified:
   - `create_capsule`: Invalidates chain cache when new capsules are added

## Usage

### Caching Function Results

To cache any function result, use the `cache_response` decorator:

```python
from api.cache import cache_response

@cache_response(ttl_seconds=60)  # Cache for 60 seconds
def my_expensive_function(arg1, arg2):
    # Perform expensive operations
    return result
```

### Chain Caching

For chain-related caching operations, use these functions:

```python
from api.cache import get_cached_chain, cache_chain, invalidate_chain_cache

# Check if chain is in cache
cached_chain = get_cached_chain(chain_id)
if cached_chain is None:
    # Load chain and cache it
    chain = list(engine.load_chain())
    cache_chain(chain_id, chain)
else:
    # Use cached chain
    chain = cached_chain

# Invalidate chain cache when chain is modified
invalidate_chain_cache(chain_id)
```

### Verification Result Caching

For cryptographic verification caching:

```python
from api.cache import get_cached_verification, cache_verification_result

# Check for cached verification result
cached_result = get_cached_verification(capsule_id)
if cached_result is not None:
    # Use cached verification result
    is_valid = cached_result
else:
    # Perform verification and cache result
    is_valid = engine.verify_capsule(capsule)
    cache_verification_result(capsule_id, is_valid)
```

## Configuration

The caching system is configurable via environment variables or settings:

- `UATP_CACHE_SIZE`: Maximum number of items in the cache (default: 1000)
- `UATP_CACHE_ENABLED`: Toggle to enable/disable caching (default: True)
- `UATP_CHAIN_CACHE_TTL`: Default TTL for chain caching in seconds (default: 60)
- `UATP_VERIFICATION_CACHE_TTL`: Default TTL for verification result caching in seconds (default: 300)

## Performance Considerations

1. **Memory Usage**: The cache size should be tuned based on available system memory and chain size.
2. **TTL Settings**: Adjust TTL based on:
   - Chain update frequency
   - API access patterns
   - Performance requirements
3. **Cache Invalidation**: Critical for data consistency when chain content changes.

## Best Practices

1. Always invalidate related caches when modifying the chain.
2. Use appropriate TTL values for different types of data.
3. Include cache hit/miss metrics in monitoring.
4. Consider adding transaction-based caching for complex operations.
5. Regularly review and tune caching parameters based on production metrics.

## Future Enhancements

1. Distributed caching support for multi-instance deployments
2. More granular cache invalidation strategies
3. Cache warming for frequently accessed capsules
4. Advanced cache statistics and monitoring

## Troubleshooting

### Common Issues

1. **Stale Data**: If you observe stale data, check if cache invalidation is properly implemented where chain modifications occur.
2. **High Memory Usage**: Reduce cache size or TTL if memory consumption is too high.
3. **Cache Thrashing**: Increase cache size if hit rates are low due to eviction.

### Debugging

The caching system includes detailed logging to help diagnose issues:
- Cache hits and misses are logged at DEBUG level
- Cache invalidation is logged at DEBUG level
- Cache errors are logged at ERROR level

To enable verbose logging for debugging cache issues:

```python
import logging
logging.getLogger('uatp_api').setLevel(logging.DEBUG)
```
