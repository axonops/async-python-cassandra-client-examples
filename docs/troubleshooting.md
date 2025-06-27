# Troubleshooting Guide

## Common Issues and Solutions

### 1. Services Won't Start

#### Cassandra Fails to Start

**Symptoms**: 
- Container exits immediately
- "Cannot allocate memory" errors

**Solutions**:
```bash
# Increase Docker memory allocation
# Docker Desktop → Settings → Resources → Memory: 6GB+

# Check logs
docker-compose logs cassandra

# If data corruption
docker-compose down -v  # Warning: deletes all data
docker-compose up -d
```

#### Application Won't Connect to Cassandra

**Symptoms**:
- "Connection refused" errors
- "NoHostAvailable" exceptions

**Solutions**:
```bash
# Ensure Cassandra is healthy
docker-compose ps
# Should show (healthy) not (health: starting)

# Wait longer for Cassandra
docker-compose stop async-app sync-app
sleep 30
docker-compose start async-app sync-app

# Check Cassandra is listening
docker-compose exec cassandra netstat -tlnp | grep 9042
```

### 2. Performance Issues

#### Slow Response Times

**Diagnosis**:
```bash
# Check resource usage
docker stats

# Check connection pool
curl http://localhost:8001/metrics | grep cassandra_connection

# Check slow queries
docker-compose exec cassandra nodetool toppartitions
```

**Solutions**:
```python
# Increase connection pool
MAX_CONNECTIONS=200

# Add query timeout
REQUEST_TIMEOUT=60

# Use prepared statements
stmt = session.prepare("SELECT * FROM users WHERE id = ?")
```

#### High Memory Usage

**Symptoms**:
- Increasing RSS memory
- OOM kills

**Solutions**:
```yaml
# docker-compose.yml - Add memory limits
services:
  async-app:
    deploy:
      resources:
        limits:
          memory: 2G

# Python - Add garbage collection
import gc
gc.collect()  # Force garbage collection
```

### 3. Connection Issues

#### Connection Pool Exhaustion

**Symptoms**:
- "Pool is exhausted" errors
- Timeouts acquiring connections

**Solutions**:
```python
# Increase pool size
pool_size=200
pool_timeout=30

# Monitor pool usage
from prometheus_client import Gauge
pool_gauge = Gauge('connection_pool_available', 'Available connections')
pool_gauge.set(pool.available_connections)
```

#### Connection Timeouts

**Symptoms**:
- "OperationTimedOut" errors
- Sporadic failures

**Solutions**:
```bash
# Increase timeouts in .env
CONNECTION_TIMEOUT=30
REQUEST_TIMEOUT=60

# Check network latency
docker-compose exec async-app ping cassandra
```

### 4. Data Issues

#### Data Not Persisting

**Symptoms**:
- Data disappears after restart
- Writes seem successful but reads fail

**Solutions**:
```python
# Check consistency level
from cassandra.query import ConsistencyLevel
session.default_consistency_level = ConsistencyLevel.QUORUM

# Verify write
result = session.execute("INSERT INTO ... IF NOT EXISTS")
if not result.was_applied:
    logger.error("Write not applied")
```

#### Query Errors

**Symptoms**:
- "InvalidRequest" exceptions
- "Undefined column" errors

**Solutions**:
```bash
# Verify schema
docker-compose exec cassandra cqlsh -e "DESC KEYSPACE perftest"

# Recreate tables
docker-compose exec cassandra cqlsh -e "DROP KEYSPACE perftest"
docker-compose restart async-app sync-app
```

### 5. Monitoring Issues

#### Metrics Not Showing

**Symptoms**:
- Empty Grafana dashboards
- Prometheus targets down

**Solutions**:
```bash
# Check Prometheus targets
open http://localhost:9090/targets

# Verify metrics endpoint
curl http://localhost:8001/metrics
curl http://localhost:8002/metrics

# Restart monitoring stack
docker-compose restart prometheus grafana
```

#### Logs Not Appearing

**Symptoms**:
- No logs in Loki
- Grafana shows no log data

**Solutions**:
```bash
# Check Promtail
docker-compose logs promtail

# Verify log format
docker-compose logs async-app | head -10

# Restart log pipeline
docker-compose restart loki promtail
```

## Debugging Techniques

### 1. Application Debugging

#### Enable Debug Logging
```python
# Set in .env
LOG_LEVEL=DEBUG

# Or in code
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### Add Request Tracing
```python
import uuid
from fastapi import Request

@app.middleware("http")
async def add_trace_id(request: Request, call_next):
    trace_id = str(uuid.uuid4())
    request.state.trace_id = trace_id
    logger.info(f"Request {trace_id}: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response {trace_id}: {response.status_code}")
    return response
```

#### Profile Slow Endpoints
```python
import time
from functools import wraps

def profile_endpoint(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        duration = time.time() - start
        if duration > 1.0:  # Log slow requests
            logger.warning(f"{func.__name__} took {duration:.2f}s")
        return result
    return wrapper
```

### 2. Cassandra Debugging

#### Check Cluster Status
```bash
docker-compose exec cassandra nodetool status
docker-compose exec cassandra nodetool info
docker-compose exec cassandra nodetool tpstats
```

#### Monitor Queries
```bash
# Enable query logging
docker-compose exec cassandra cqlsh
> TRACING ON;
> SELECT * FROM perftest.users LIMIT 1;
> SHOW SESSION <trace_id>;
```

#### Analyze Table Statistics
```bash
docker-compose exec cassandra nodetool tablestats perftest
docker-compose exec cassandra nodetool tablehistograms perftest users
```

### 3. Docker Debugging

#### Container Inspection
```bash
# Check container details
docker inspect async-cassandra-perf_async-app_1

# View container processes
docker-compose top

# Access container shell
docker-compose exec async-app /bin/sh
```

#### Network Debugging
```bash
# List networks
docker network ls

# Inspect network
docker network inspect async-cassandra-perf_cassandra-network

# Test connectivity
docker-compose exec async-app nc -zv cassandra 9042
```

## Performance Diagnostics

### 1. Load Test Analysis

```bash
# Generate flame graph
docker-compose exec async-app py-spy record -o profile.svg -d 30 -p 1

# Memory profiling
docker-compose exec async-app python -m memory_profiler app/main.py
```

### 2. Query Performance

```sql
-- Find slow queries
SELECT * FROM system_traces.events 
WHERE source = 'cassandra' 
  AND activity LIKE '%query%' 
  AND duration > 10000;

-- Check table sizes
SELECT table_name, mean_partition_size, max_partition_size 
FROM system.size_estimates 
WHERE keyspace_name = 'perftest';
```

## Error Reference

### Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| `NoHostAvailable` | Cassandra not ready | Wait for health check |
| `OperationTimedOut` | Query too slow | Increase timeout, optimize query |
| `Pool is exhausted` | Too many concurrent requests | Increase pool size |
| `InvalidRequest` | Schema mismatch | Verify table structure |
| `ReadTimeout` | Large result set | Use pagination |
| `WriteTimeout` | Large batch | Reduce batch size |
| `Connection refused` | Service not running | Check container status |

## Recovery Procedures

### 1. Full System Reset
```bash
#!/bin/bash
# reset.sh
docker-compose down -v
docker system prune -f
docker-compose build --no-cache
docker-compose up -d
```

### 2. Data Recovery
```bash
# Backup before reset
docker-compose exec cassandra nodetool snapshot perftest

# Find snapshot
docker-compose exec cassandra find /var/lib/cassandra/data -name "*.db"

# Restore from snapshot
docker-compose exec cassandra nodetool refresh perftest users
```

### 3. Service Recovery
```bash
# Restart specific service
docker-compose restart async-app

# Recreate service
docker-compose up -d --force-recreate async-app

# Scale service
docker-compose up -d --scale async-app=2
```

## Preventive Measures

### 1. Health Checks
```yaml
# docker-compose.yml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```

### 2. Resource Limits
```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 2G
    reservations:
      cpus: '1.0'
      memory: 1G
```

### 3. Monitoring Alerts
```yaml
# prometheus/alerts.yml
- alert: ServiceDown
  expr: up{job=~"async-app|sync-app"} == 0
  for: 5m
  annotations:
    summary: "Service {{ $labels.job }} is down"
```

## Getting Help

### 1. Collect Diagnostics
```bash
# Create diagnostic bundle
./scripts/collect-diagnostics.sh

# Includes:
# - Container logs
# - Resource usage
# - Configuration
# - Metrics snapshot
```

### 2. Useful Commands Summary
```bash
# Quick health check
curl http://localhost:8001/health
curl http://localhost:8002/health

# View real-time logs
docker-compose logs -f --tail=100

# Check resource usage
docker stats --no-stream

# Cassandra status
docker-compose exec cassandra nodetool status
```

### 3. Debug Checklist
- [ ] Check container status: `docker-compose ps`
- [ ] Review logs: `docker-compose logs [service]`
- [ ] Verify connectivity: health endpoints
- [ ] Check resources: `docker stats`
- [ ] Review metrics: Grafana dashboards
- [ ] Test queries: Direct CQL queries
- [ ] Verify configuration: Environment variables