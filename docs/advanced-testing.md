# Advanced Testing Scenarios

## Overview

This guide covers advanced testing scenarios for blackbox testing of distributed systems. Since we're testing from outside the application, we use infrastructure-level tools and network manipulation to simulate real-world failure conditions.

## Testing Approaches for Blackbox Testing

### 1. Network-Level Failures

Since we can't modify the application code, we simulate failures at the network level using tools like:
- **tc (Traffic Control)**: Network latency and packet loss
- **iptables**: Connection blocking
- **Docker network**: Network partitioning
- **Toxiproxy**: Programmable network conditions

### 2. Resource Constraints

Using Docker and cgroups to limit:
- CPU throttling
- Memory restrictions
- I/O limitations
- Connection limits

### 3. Infrastructure Chaos

Using container orchestration to:
- Kill containers
- Pause processes
- Corrupt network packets
- Simulate node failures

## Failure Scenario Implementations

### 1. Connection Failure Recovery Testing

#### Approach: Network Partition Simulation

```bash
#!/bin/bash
# test-connection-recovery.sh

echo "Testing connection failure recovery..."

# 1. Start baseline test
echo "Phase 1: Establishing baseline..."
curl -X POST http://localhost:3001/api/async/users -H "Content-Type: application/json" \
  -d '{"username":"test_before","email":"before@test.com"}'

# 2. Create network partition
echo "Phase 2: Creating network partition..."
docker network disconnect async-cassandra-perf_cassandra-network \
  async-cassandra-perf_cassandra_1

# 3. Monitor application behavior
echo "Phase 3: Testing during partition (should see errors)..."
for i in {1..10}; do
  curl -w "\nStatus: %{http_code} Time: %{time_total}s\n" \
    http://localhost:8001/health
  sleep 1
done

# 4. Restore network
echo "Phase 4: Restoring network..."
docker network connect async-cassandra-perf_cassandra-network \
  async-cassandra-perf_cassandra_1

# 5. Test recovery
echo "Phase 5: Testing recovery..."
for i in {1..20}; do
  curl -w "\nStatus: %{http_code} Time: %{time_total}s\n" \
    http://localhost:8001/health
  sleep 2
done

# 6. Verify functionality
echo "Phase 6: Verifying full recovery..."
curl -X POST http://localhost:8001/api/v1/users -H "Content-Type: application/json" \
  -d '{"username":"test_after","email":"after@test.com"}'
```

#### Using Toxiproxy for Controlled Failures

```yaml
# docker-compose.toxiproxy.yml
services:
  toxiproxy:
    image: ghcr.io/shopify/toxiproxy:2.5.0
    ports:
      - "8474:8474"  # API
      - "19042:19042"  # Proxied Cassandra
    networks:
      - cassandra-network

  async-app-toxic:
    extends:
      service: async-app
    environment:
      - CASSANDRA_HOSTS=toxiproxy
      - CASSANDRA_PORT=19042
```

```python
# configure-toxiproxy.py
import requests

# Create proxy
requests.post('http://localhost:8474/proxies', json={
    'name': 'cassandra',
    'listen': '0.0.0.0:19042',
    'upstream': 'cassandra:9042'
})

# Add latency toxic
requests.post('http://localhost:8474/proxies/cassandra/toxics', json={
    'name': 'latency',
    'type': 'latency',
    'stream': 'downstream',
    'toxicity': 1.0,
    'attributes': {
        'latency': 5000,  # 5 second latency
        'jitter': 1000    # ±1 second jitter
    }
})

# Simulate connection drops
requests.post('http://localhost:8474/proxies/cassandra/toxics', json={
    'name': 'timeout',
    'type': 'timeout',
    'stream': 'downstream',
    'toxicity': 0.2,  # 20% of connections timeout
    'attributes': {
        'timeout': 0  # Immediate timeout
    }
})
```

### 2. Cassandra Node Failure Simulation

#### Multi-Node Cassandra Setup

```yaml
# docker-compose.cassandra-cluster.yml
services:
  cassandra1:
    image: cassandra:5.0
    environment:
      - CASSANDRA_CLUSTER_NAME=TestCluster
      - CASSANDRA_SEEDS=cassandra1
      - CASSANDRA_DC=dc1
    networks:
      - cassandra-network

  cassandra2:
    image: cassandra:5.0
    environment:
      - CASSANDRA_CLUSTER_NAME=TestCluster
      - CASSANDRA_SEEDS=cassandra1
      - CASSANDRA_DC=dc1
    depends_on:
      - cassandra1
    networks:
      - cassandra-network

  cassandra3:
    image: cassandra:5.0
    environment:
      - CASSANDRA_CLUSTER_NAME=TestCluster
      - CASSANDRA_SEEDS=cassandra1
      - CASSANDRA_DC=dc1
    depends_on:
      - cassandra1
    networks:
      - cassandra-network
```

#### Node Failure Test Script

```bash
#!/bin/bash
# test-node-failure.sh

# 1. Verify cluster health
echo "Checking cluster status..."
docker-compose exec cassandra1 nodetool status

# 2. Run baseline load test
echo "Running baseline test..."
locust -f locustfile.py --headless --users 10 --spawn-rate 2 \
  --run-time 30s --host http://localhost:8001 \
  --csv results/baseline

# 3. Kill one node
echo "Killing cassandra2..."
docker-compose stop cassandra2

# 4. Run test during failure
echo "Testing with node down..."
locust -f locustfile.py --headless --users 10 --spawn-rate 2 \
  --run-time 60s --host http://localhost:8001 \
  --csv results/one-node-down

# 5. Kill second node (testing minority)
echo "Killing cassandra3 (cluster minority)..."
docker-compose stop cassandra3

# 6. Test with minority nodes
echo "Testing with only one node..."
locust -f locustfile.py --headless --users 10 --spawn-rate 2 \
  --run-time 30s --host http://localhost:8001 \
  --csv results/minority-nodes

# 7. Restore nodes
echo "Restoring nodes..."
docker-compose start cassandra2 cassandra3

# 8. Wait for cluster recovery
sleep 60

# 9. Final test
echo "Final test after recovery..."
locust -f locustfile.py --headless --users 10 --spawn-rate 2 \
  --run-time 30s --host http://localhost:8001 \
  --csv results/recovered
```

### 3. Network Latency Injection

#### Using Linux Traffic Control (tc)

```bash
#!/bin/bash
# inject-latency.sh

# Function to add latency to a container
add_latency() {
    container=$1
    latency=$2
    jitter=$3
    
    docker exec $container tc qdisc add dev eth0 root netem \
      delay ${latency}ms ${jitter}ms distribution normal
}

# Function to remove latency
remove_latency() {
    container=$1
    docker exec $container tc qdisc del dev eth0 root netem
}

# Test scenarios
echo "Testing normal latency..."
python compare.py > results/normal-latency.json

echo "Adding 100ms latency to Cassandra..."
add_latency "async-cassandra-perf_cassandra_1" 100 20

echo "Testing with high latency..."
python compare.py > results/high-latency.json

echo "Adding extreme latency (500ms)..."
remove_latency "async-cassandra-perf_cassandra_1"
add_latency "async-cassandra-perf_cassandra_1" 500 100

echo "Testing with extreme latency..."
python compare.py > results/extreme-latency.json

echo "Cleaning up..."
remove_latency "async-cassandra-perf_cassandra_1"
```

#### Network Bandwidth Limitation

```bash
#!/bin/bash
# limit-bandwidth.sh

# Limit bandwidth to 1Mbps
docker exec async-cassandra-perf_cassandra_1 \
  tc qdisc add dev eth0 root tbf rate 1mbit burst 32kbit latency 400ms

# Run test
echo "Testing with limited bandwidth..."
curl -X GET "http://localhost:8001/api/v1/stream/large-dataset/10000" \
  -o /dev/null -w "Time: %{time_total}s\n"

# Remove limitation
docker exec async-cassandra-perf_cassandra_1 tc qdisc del dev eth0 root
```

### 4. Memory Pressure Testing

#### Memory Limit Testing

```bash
#!/bin/bash
# test-memory-pressure.sh

# 1. Update docker-compose with memory limits
cat > docker-compose.override.yml << EOF
services:
  async-app:
    deploy:
      resources:
        limits:
          memory: 256M
  sync-app:
    deploy:
      resources:
        limits:
          memory: 256M
EOF

# 2. Restart services with limits
docker-compose up -d

# 3. Generate memory pressure
echo "Creating memory pressure with large operations..."
for i in {1..100}; do
  curl -X POST "http://localhost:8001/api/v1/users/batch" \
    -H "Content-Type: application/json" \
    -d '[
      {"username":"user1","email":"user1@test.com","profile_data":{"data":"'$(head -c 10000 /dev/urandom | base64)'"}},
      {"username":"user2","email":"user2@test.com","profile_data":{"data":"'$(head -c 10000 /dev/urandom | base64)'"}}
    ]' &
done

wait

# 4. Monitor memory usage
docker stats --no-stream

# 5. Check for OOM kills
docker-compose logs | grep -i "killed\|oom"
```

### 5. Chaos Testing Framework

#### Pumba - Chaos Testing for Docker

```bash
# Install Pumba
docker pull gaiaadm/pumba

# Random container kills
docker run -it --rm -v /var/run/docker.sock:/var/run/docker.sock \
  gaiaadm/pumba --random --interval 30s kill \
  --signal SIGKILL "re2:.*async-app.*"

# Network delay chaos
docker run -it --rm -v /var/run/docker.sock:/var/run/docker.sock \
  gaiaadm/pumba netem --duration 1m delay \
  --time 100 --jitter 30 "re2:.*cassandra.*"

# Packet loss simulation
docker run -it --rm -v /var/run/docker.sock:/var/run/docker.sock \
  gaiaadm/pumba netem --duration 2m loss \
  --percent 10 "re2:.*app.*"
```

#### Chaos Testing Script

```python
# chaos-test.py
import subprocess
import time
import random
import threading

class ChaosTest:
    def __init__(self):
        self.chaos_active = False
        
    def network_partition(self, duration=30):
        """Randomly partition network"""
        print(f"Creating network partition for {duration}s...")
        subprocess.run([
            "docker", "network", "disconnect", 
            "async-cassandra-perf_cassandra-network",
            "async-cassandra-perf_cassandra_1"
        ])
        time.sleep(duration)
        subprocess.run([
            "docker", "network", "connect",
            "async-cassandra-perf_cassandra-network", 
            "async-cassandra-perf_cassandra_1"
        ])
        
    def cpu_stress(self, container, duration=30):
        """Stress CPU in container"""
        print(f"Stressing CPU in {container} for {duration}s...")
        subprocess.run([
            "docker", "exec", container,
            "stress", "--cpu", "8", "--timeout", f"{duration}s"
        ])
        
    def memory_stress(self, container, duration=30):
        """Stress memory in container"""
        print(f"Stressing memory in {container} for {duration}s...")
        subprocess.run([
            "docker", "exec", container,
            "stress", "--vm", "2", "--vm-bytes", "128M",
            "--timeout", f"{duration}s"
        ])
        
    def random_chaos(self):
        """Apply random chaos"""
        chaos_functions = [
            lambda: self.network_partition(random.randint(10, 30)),
            lambda: self.cpu_stress("async-cassandra-perf_async-app_1", random.randint(10, 30)),
            lambda: self.memory_stress("async-cassandra-perf_async-app_1", random.randint(10, 30)),
        ]
        
        while self.chaos_active:
            chaos = random.choice(chaos_functions)
            chaos()
            time.sleep(random.randint(30, 60))

# Run chaos test
chaos = ChaosTest()
chaos.chaos_active = True

# Start chaos in background
chaos_thread = threading.Thread(target=chaos.random_chaos)
chaos_thread.start()

# Run load test during chaos
subprocess.run([
    "locust", "-f", "locustfile.py",
    "--headless", "--users", "50",
    "--spawn-rate", "5", "--run-time", "10m",
    "--host", "http://localhost:8001",
    "--csv", "results/chaos-test"
])

# Stop chaos
chaos.chaos_active = False
chaos_thread.join()
```

## Monitoring During Failure Tests

### Key Metrics to Track

1. **Availability Metrics**
   - Request success rate
   - Health check status
   - Connection pool utilization

2. **Performance Metrics**
   - Response time during failures
   - Throughput degradation
   - Recovery time

3. **Error Patterns**
   - Error types distribution
   - Retry success rates
   - Timeout frequencies

### Grafana Queries for Failure Analysis

```promql
# Service availability
(1 - (sum(rate(http_requests_total{status=~"5.."}[1m])) / sum(rate(http_requests_total[1m])))) * 100

# Recovery time (time to return to baseline)
deriv(http_request_duration_seconds_sum[5m]) < 0

# Connection failures
increase(cassandra_connection_errors_total[5m])

# Retry effectiveness
sum(rate(cassandra_retries_total{status="success"}[5m])) / 
sum(rate(cassandra_retries_total[5m])) * 100
```

## Best Practices for Blackbox Failure Testing

1. **Isolation**: Run failure tests in isolated environments
2. **Gradual Escalation**: Start with simple failures, increase complexity
3. **Monitoring**: Always monitor both applications during tests
4. **Documentation**: Record exact failure conditions and results
5. **Automation**: Script repeatable test scenarios
6. **Recovery Validation**: Always verify full recovery

## Tools Summary

| Tool | Purpose | Installation |
|------|---------|--------------|
| tc | Network latency/loss | Built into Linux |
| iptables | Connection blocking | Built into Linux |
| Toxiproxy | Programmable failures | Docker image |
| Pumba | Chaos testing | Docker image |
| stress | Resource stress | apt-get install stress |
| Locust | Load generation | pip install locust |

## Next Steps

1. **Build Test Suite**: Create automated failure test suite
2. **Define SLOs**: Set availability and performance targets
3. **Regular Testing**: Schedule periodic chaos tests
4. **Runbooks**: Document recovery procedures
5. **Improve Resilience**: Use findings to improve applications