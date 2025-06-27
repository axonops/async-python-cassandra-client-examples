# Performance Tuning Guide

## Overview

This guide provides strategies for optimizing both the async and sync Cassandra client applications for maximum performance.

## Cassandra Tuning

### 1. Connection Pool Configuration

#### Async Client (async-cassandra)
```python
# In app/database.py
client = await create_client(
    contact_points=settings.cassandra_hosts,
    port=settings.cassandra_port,
    pool_size=100,  # Increase for high concurrency
    min_pool_size=25,  # Maintain minimum connections
    max_pool_size=200,  # Cap maximum connections
    pool_timeout=30,  # Connection acquisition timeout
    idle_time=120,  # Keep connections alive
)
```

#### Sync Client (cassandra-driver)
```python
# In app/database.py
cluster = Cluster(
    contact_points=settings.cassandra_hosts,
    port=settings.cassandra_port,
    protocol_version=4,
    executor_threads=8,  # Increase for more parallelism
    connection_class=LibevConnection,  # Use libev for better performance
)

# Per-host connection limits
cluster.set_core_connections_per_host(LOCAL, 2)
cluster.set_max_connections_per_host(LOCAL, 8)
cluster.set_core_connections_per_host(REMOTE, 1)
cluster.set_max_connections_per_host(REMOTE, 2)
```

### 2. Query Optimization

#### Prepared Statements
```python
# Async app
stmt = await session.prepare("""
    SELECT * FROM users WHERE username = ?
""")
result = await session.execute(stmt, [username])

# Sync app
stmt = session.prepare("""
    SELECT * FROM users WHERE username = ?
""")
result = session.execute(stmt, [username])
```

#### Batch Operations
```python
# Async app - Use native batching
batch = session.prepare_batch()
for user in users:
    batch.add(insert_stmt, user.dict())
await session.execute_batch(batch)

# Sync app - Use BatchStatement
from cassandra.query import BatchStatement
batch = BatchStatement()
for user in users:
    batch.add(insert_stmt, user.dict())
session.execute(batch)
```

#### Pagination
```python
# Use fetch_size for large results
statement = SimpleStatement(
    "SELECT * FROM large_table",
    fetch_size=1000  # Fetch 1000 rows at a time
)
```

### 3. Consistency Levels

Balance consistency with performance:

```python
from cassandra.query import ConsistencyLevel

# For writes - use LOCAL_QUORUM for durability
write_stmt = SimpleStatement(
    "INSERT INTO ...",
    consistency_level=ConsistencyLevel.LOCAL_QUORUM
)

# For reads - use LOCAL_ONE for speed
read_stmt = SimpleStatement(
    "SELECT * FROM ...",
    consistency_level=ConsistencyLevel.LOCAL_ONE
)
```

## Application Tuning

### 1. FastAPI Configuration

#### Worker Processes
```python
# In Dockerfile or startup command
CMD ["uvicorn", "app.main:app", "--workers", "4", "--loop", "uvloop"]
```

#### Async Optimizations
```python
# Use uvloop for better async performance
import uvloop
import asyncio

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
```

### 2. Resource Limits

#### Docker Resource Configuration
```yaml
# docker-compose.yml
services:
  async-app:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G
```

#### System Limits
```bash
# Increase file descriptor limits
ulimit -n 65536

# In Docker container
RUN echo "* soft nofile 65536" >> /etc/security/limits.conf
RUN echo "* hard nofile 65536" >> /etc/security/limits.conf
```

### 3. Caching Strategies

#### In-Memory Caching
```python
from functools import lru_cache
from cachetools import TTLCache

# Simple LRU cache
@lru_cache(maxsize=1000)
async def get_user_cached(user_id: str):
    return await get_user(user_id)

# TTL cache for time-sensitive data
cache = TTLCache(maxsize=1000, ttl=300)  # 5 minute TTL

async def get_cached_data(key: str):
    if key in cache:
        return cache[key]
    
    data = await fetch_from_cassandra(key)
    cache[key] = data
    return data
```

#### Redis Caching
```python
import aioredis

# Async Redis client
redis = await aioredis.create_redis_pool('redis://localhost')

async def get_user_with_cache(user_id: str):
    # Try cache first
    cached = await redis.get(f"user:{user_id}")
    if cached:
        return json.loads(cached)
    
    # Fetch from Cassandra
    user = await get_user_from_cassandra(user_id)
    
    # Cache for 5 minutes
    await redis.setex(f"user:{user_id}", 300, json.dumps(user))
    return user
```

## Monitoring and Profiling

### 1. Application Profiling

#### CPU Profiling
```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Run your code
await some_async_function()

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)  # Top 20 functions
```

#### Memory Profiling
```python
from memory_profiler import profile

@profile
async def memory_intensive_function():
    # Your code here
    pass
```

#### Async Profiling
```python
import aiomonitor
import asyncio

async def main():
    # Start aiomonitor for async debugging
    async with aiomonitor.start_monitor(
        loop=asyncio.get_event_loop(),
        port=50101
    ):
        # Your async code
        await run_application()
```

### 2. Performance Metrics

#### Custom Metrics
```python
from prometheus_client import Histogram, Counter
import time

# Track specific operations
query_duration = Histogram(
    'custom_query_duration_seconds',
    'Custom query duration',
    ['query_type']
)

@query_duration.labels(query_type='complex_join').time()
async def complex_query():
    # Your query logic
    pass
```

## Optimization Strategies

### 1. Async-Specific Optimizations

#### Concurrent Operations
```python
# Bad - Sequential
results = []
for user_id in user_ids:
    user = await get_user(user_id)
    results.append(user)

# Good - Concurrent
tasks = [get_user(user_id) for user_id in user_ids]
results = await asyncio.gather(*tasks)
```

#### Connection Reuse
```python
# Reuse session across requests
async def get_db_session():
    # Return existing session
    return db.get_session()

# Don't create new connections per request
```

### 2. Sync-Specific Optimizations

#### Thread Pool Tuning
```python
from concurrent.futures import ThreadPoolExecutor

# Increase thread pool for sync operations
executor = ThreadPoolExecutor(max_workers=50)

# Use for CPU-bound operations
result = await loop.run_in_executor(
    executor, 
    cpu_intensive_function, 
    data
)
```

### 3. Query Patterns

#### Denormalization
```python
# Instead of multiple queries
user = get_user(user_id)
profile = get_profile(user_id)
settings = get_settings(user_id)

# Use denormalized model
user_data = get_user_complete(user_id)  # All data in one query
```

#### Materialized Views
```sql
CREATE MATERIALIZED VIEW users_by_email AS
    SELECT * FROM users
    WHERE email IS NOT NULL
    PRIMARY KEY (email, id);
```

## Common Performance Issues

### 1. Connection Pool Exhaustion

**Symptoms**: Timeouts, connection errors

**Solution**:
```python
# Increase pool size
pool_size=200

# Add connection timeout
pool_timeout=30

# Monitor pool usage
pool_stats = session.get_pool_stats()
```

### 2. Memory Leaks

**Symptoms**: Increasing memory usage over time

**Solution**:
```python
# Properly close resources
async def process_data():
    try:
        result = await query_data()
        return result
    finally:
        # Clean up
        await cleanup_resources()

# Use context managers
async with session.transaction() as tx:
    await tx.execute(query)
```

### 3. Slow Queries

**Symptoms**: High latency, timeouts

**Solution**:
```python
# Add query timeouts
statement = SimpleStatement(
    query,
    timeout=10  # 10 second timeout
)

# Use ALLOW FILTERING sparingly
# Better: Create appropriate indexes
CREATE INDEX ON users (email);
```

## Performance Benchmarks

### Expected Performance Metrics

| Metric | Async Client | Sync Client |
|--------|--------------|-------------|
| Single User RPS | 500-800 | 400-600 |
| 50 Users RPS | 3000-5000 | 2000-3500 |
| P95 Latency | 10-20ms | 15-30ms |
| Memory per Connection | 2-3MB | 3-5MB |

### Tuning Checklist

- [ ] Connection pool sized appropriately
- [ ] Prepared statements used
- [ ] Batch operations where applicable
- [ ] Appropriate consistency levels
- [ ] Caching implemented
- [ ] Monitoring in place
- [ ] Resource limits set
- [ ] Query timeouts configured
- [ ] Indexes created
- [ ] Denormalization considered

## Environment-Specific Tuning

### Development
```env
MAX_CONNECTIONS=10
WORKERS=2
LOG_LEVEL=DEBUG
```

### Testing
```env
MAX_CONNECTIONS=50
WORKERS=4
LOG_LEVEL=INFO
```

### Production
```env
MAX_CONNECTIONS=200
WORKERS=8
LOG_LEVEL=WARNING
```

## Next Steps

1. **Baseline**: Establish current performance metrics
2. **Profile**: Identify bottlenecks
3. **Optimize**: Apply relevant tuning strategies
4. **Test**: Verify improvements
5. **Monitor**: Track performance over time