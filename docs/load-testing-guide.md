# Load Testing Guide

## Overview

This guide covers how to effectively load test the async and sync Cassandra clients to measure and compare their performance characteristics.

## Load Testing Tools

### 1. Locust (Python-based)

**Best for**: Interactive testing, gradual load increase, web-based monitoring

#### Installation
```bash
cd load-testing
pip install -r requirements.txt
```

#### Running Tests

**Interactive Mode (Web UI)**
```bash
# Test async app
locust -f locustfile.py --host http://localhost:8001

# Test sync app  
locust -f locustfile.py --host http://localhost:8002

# Open browser to http://localhost:8089
```

**Headless Mode (CLI)**
```bash
# Run for 5 minutes with 100 users
locust -f locustfile.py \
  --headless \
  --host http://localhost:8001 \
  --users 100 \
  --spawn-rate 10 \
  --run-time 5m \
  --html results/report.html
```

#### Test Scenarios in locustfile.py

1. **CassandraUser** - CRUD operations mix
   - 30% Create users
   - 50% Read users
   - 20% List users
   - 10% Update users
   - 10% Batch operations

2. **StreamingUser** - Streaming operations
   - 60% Stream sensor data
   - 30% Stream documents
   - 10% Generate test data

3. **MixedWorkloadUser** - Realistic workload
   - 80% CRUD operations
   - 20% Streaming operations

### 2. k6 (JavaScript-based)

**Best for**: CI/CD integration, complex scenarios, detailed metrics

#### Installation
```bash
# macOS
brew install k6

# Linux
sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
echo "deb https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
sudo apt-get update
sudo apt-get install k6

# Windows
choco install k6
```

#### Running Tests

```bash
# Basic test
k6 run k6-script.js --env BASE_URL=http://localhost:8001

# Custom settings
k6 run k6-script.js \
  --env BASE_URL=http://localhost:8001 \
  --vus 50 \
  --duration 5m \
  --out json=results/k6-results.json
```

#### Test Scenarios in k6-script.js

1. **Gradual Ramp-up**
   - 0 → 10 users over 30s
   - 10 → 50 users over 1m
   - Hold 50 users for 3m
   - 50 → 100 users over 1m
   - Hold 100 users for 3m
   - Ramp down to 0

2. **Spike Test**
   - Normal load (5 users)
   - Spike to 200 users in 5s
   - Hold for 30s
   - Return to normal

3. **Constant Load**
   - 25 users for 10 minutes

### 3. Comparison Script (compare.py)

**Best for**: Direct performance comparison, automated reporting

```bash
cd load-testing
python compare.py
```

This script:
- Runs identical workloads against both apps
- Measures response times and throughput
- Generates comparison charts
- Saves results to `results/comparison_[timestamp].json`

## Test Scenarios

### 1. Baseline Performance Test

**Purpose**: Establish single-user performance characteristics

```bash
# Using Locust
locust -f locustfile.py --host http://localhost:8001 \
  --headless --users 1 --spawn-rate 1 --run-time 2m

# Using k6
k6 run k6-script.js --env BASE_URL=http://localhost:8001 --vus 1 --duration 2m
```

**Metrics to observe**:
- Average response time
- P95/P99 latency
- Requests per second
- Error rate (should be 0%)

### 2. Load Test

**Purpose**: Measure performance under normal expected load

```bash
# 50 concurrent users for 10 minutes
locust -f locustfile.py --host http://localhost:8001 \
  --headless --users 50 --spawn-rate 5 --run-time 10m

# Compare both apps
./run-tests.sh
```

**Metrics to observe**:
- Response time degradation
- Throughput plateau
- Error rate increase
- Resource utilization

### 3. Stress Test

**Purpose**: Find the breaking point

```bash
# Gradually increase to 500 users
k6 run k6-script.js --env BASE_URL=http://localhost:8001 \
  --stage '5m:500' --stage '5m:500' --stage '2m:0'
```

**Metrics to observe**:
- Maximum throughput
- Point of first errors
- Response time at breaking point
- Recovery behavior

### 4. Spike Test

**Purpose**: Test sudden traffic increases

```bash
# Use k6 spike scenario
k6 run k6-script.js --env BASE_URL=http://localhost:8001 \
  --scenario spike_test
```

**Metrics to observe**:
- Response time during spike
- Error rate during spike
- Recovery time
- Connection pool behavior

### 5. Soak Test

**Purpose**: Find memory leaks and degradation

```bash
# Run for 1 hour with moderate load
locust -f locustfile.py --host http://localhost:8001 \
  --headless --users 25 --spawn-rate 5 --run-time 1h
```

**Metrics to observe**:
- Memory usage over time
- Response time trend
- Error rate trend
- Connection pool stability

## Interpreting Results

### Key Metrics

1. **Throughput (RPS)**
   - Higher is better
   - Look for plateau points
   - Compare async vs sync

2. **Response Time**
   - Lower is better
   - Focus on P95/P99, not just average
   - Watch for outliers

3. **Error Rate**
   - Should be < 0.1% under normal load
   - Any errors under light load indicate issues
   - Timeout errors vs. connection errors

4. **Resource Utilization**
   - CPU usage should scale linearly
   - Memory should stabilize
   - Connection pool efficiency

### Performance Comparison

After running tests on both apps:

1. **Calculate Improvement**
   ```
   Improvement % = ((Async RPS - Sync RPS) / Sync RPS) × 100
   ```

2. **Latency Reduction**
   ```
   Latency Reduction % = ((Sync P95 - Async P95) / Sync P95) × 100
   ```

3. **Efficiency Gain**
   ```
   Efficiency = RPS / CPU Usage
   ```

### Common Patterns

1. **Async Advantages**
   - Better under high concurrency
   - Lower memory per connection
   - More efficient I/O handling
   - Better for streaming operations

2. **Sync Advantages**
   - Simpler debugging
   - More predictable behavior
   - Better tool support
   - Easier profiling

## Monitoring During Tests

### Grafana Dashboards

1. Open http://localhost:3000
2. Navigate to "Performance Comparison" dashboard
3. Set time range to "Last 5 minutes"
4. Watch real-time metrics during tests

### Key Panels to Watch

1. **Request Rate Comparison**
   - Shows RPS for both apps
   - Should see clear difference under load

2. **Response Time Percentiles**
   - P95 and P99 latencies
   - Async should show lower values

3. **Error Rate**
   - Should remain near 0%
   - Spikes indicate overload

4. **Connection Pool Metrics**
   - Active connections
   - Pool utilization
   - Connection wait time

### Command-line Monitoring

```bash
# Watch Docker stats
docker stats

# Monitor Cassandra
docker-compose exec cassandra nodetool status
docker-compose exec cassandra nodetool tpstats

# Application logs
docker-compose logs -f async-app sync-app
```

## Best Practices

### 1. Test Methodology

- **Warm-up**: Always warm up the applications before testing
- **Isolation**: Test one app at a time for accurate results
- **Repeatability**: Run each test at least 3 times
- **Documentation**: Record test conditions and environment

### 2. Environment Preparation

```bash
# Reset environment before tests
docker-compose down
docker-compose up -d
sleep 60  # Wait for services to stabilize

# Pre-populate data
curl -X POST http://localhost:8001/api/v1/sensor-data/generate/10000
```

### 3. Realistic Workloads

- Use think time between requests
- Vary request patterns
- Include read/write mix
- Test with realistic data sizes

### 4. Progressive Testing

1. Start with single user
2. Test with expected load
3. Increase to 2x expected
4. Find breaking point
5. Run extended duration tests

## Troubleshooting

### High Error Rates

```bash
# Check connection limits
docker-compose exec async-app cat /proc/sys/net/core/somaxconn

# Increase if needed
docker-compose exec async-app sysctl -w net.core.somaxconn=1024
```

### Inconsistent Results

- Ensure consistent environment
- Check for background processes
- Monitor system resources
- Verify network conditions

### Out of Memory

```bash
# Increase container memory
docker-compose down
# Edit docker-compose.yml to add memory limits
docker-compose up -d
```

## Automated Testing

### CI/CD Integration

```yaml
# .github/workflows/performance.yml
name: Performance Tests
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Start services
        run: docker-compose up -d
      - name: Wait for services
        run: sleep 60
      - name: Run tests
        run: |
          cd load-testing
          python compare.py
      - name: Upload results
        uses: actions/upload-artifact@v2
        with:
          name: performance-results
          path: load-testing/results/
```

### Scheduled Tests

```bash
# Add to crontab for nightly tests
0 2 * * * cd /path/to/project && ./load-testing/run-tests.sh
```

## Next Steps

1. **Establish Baselines**: Run tests to establish performance baselines
2. **Set Thresholds**: Define acceptable performance criteria
3. **Regular Testing**: Schedule regular performance tests
4. **Track Trends**: Monitor performance over time
5. **Optimize**: Use results to guide optimization efforts