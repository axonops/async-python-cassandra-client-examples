# Monitoring and Dashboards Guide

## Overview

This guide covers the monitoring stack, available metrics, and how to use the dashboards effectively.

## Monitoring Stack Components

### 1. Prometheus
- **Purpose**: Metrics collection and storage
- **URL**: http://localhost:9090
- **Retention**: 15 days (default)

### 2. Grafana
- **Purpose**: Visualization and dashboards
- **URL**: http://localhost:3000
- **Credentials**: admin/admin

### 3. Loki
- **Purpose**: Log aggregation
- **URL**: http://localhost:3100
- **Access**: Through Grafana

### 4. Promtail
- **Purpose**: Log shipping
- **Configuration**: Automatic container log collection

## Available Dashboards

### 1. Performance Comparison Dashboard

**Purpose**: Side-by-side comparison of async vs sync performance

**Key Panels**:
- **Request Rate Comparison**: Real-time RPS for both applications
- **Response Time Percentiles**: P95 and P99 latencies
- **Error Rate**: Percentage of failed requests
- **Requests by Endpoint**: Distribution of traffic
- **Cassandra Connection Pool**: Active connections and pool utilization
- **Query Duration by Operation**: Database operation performance

**Usage**:
```
1. Open Grafana: http://localhost:3000
2. Navigate to Dashboards → Performance Comparison
3. Select time range (e.g., Last 30 minutes)
4. Run load tests to see real-time comparisons
```

### 2. Cassandra Operations Dashboard

**Purpose**: Detailed view of database operations

**Key Panels**:
- **Query Rate by Operation Type**: INSERT, SELECT, UPDATE, DELETE rates
- **Query Error Rate**: Failed queries percentage
- **Query Latency Percentiles**: P50, P95, P99 by operation
- **Query Rate by Table**: Which tables receive most traffic
- **Batch Operation Metrics**: Batch size and performance

**Useful Queries**:
```promql
# Query rate by operation
sum(rate(cassandra_queries_total[5m])) by (operation)

# Error rate
sum(rate(cassandra_queries_total{status="error"}[5m])) / sum(rate(cassandra_queries_total[5m]))

# P95 latency by operation
histogram_quantile(0.95, sum(rate(cassandra_query_duration_seconds_bucket[5m])) by (operation, le))
```

### 3. System Resources Dashboard

**Purpose**: Infrastructure and resource monitoring

**Key Panels**:
- **CPU Usage**: Per application CPU utilization
- **Memory Usage**: RSS memory consumption
- **Open File Descriptors**: Connection and file handle usage
- **System Memory**: Overall system memory usage
- **Resource Usage Summary**: Tabular view of all resources

## Key Metrics Explained

### HTTP Metrics

```
http_requests_total{method, endpoint, status}
- Total number of HTTP requests
- Labels: HTTP method, endpoint path, status code

http_request_duration_seconds{method, endpoint}
- Request latency histogram
- Use for calculating percentiles

http_request_size_bytes{method, endpoint}
- Request payload size
- Useful for bandwidth monitoring

http_response_size_bytes{method, endpoint}
- Response payload size
- Track data transfer volumes
```

### Cassandra Metrics

```
cassandra_queries_total{operation, table, status}
- Total database queries
- Labels: operation type, table name, success/error

cassandra_query_duration_seconds{operation, table}
- Query execution time
- Critical for database performance

cassandra_connection_pool_size
- Current pool size
- Monitor for pool exhaustion

cassandra_active_connections
- Currently active connections
- Should be < pool size
```

### Application Metrics

```
app_concurrent_operations{operation_type}
- Number of concurrent operations
- Track concurrency patterns

app_stream_buffer_size{stream_type}
- Streaming buffer utilization
- Monitor for backpressure

process_cpu_seconds_total
- CPU time consumed
- Calculate CPU percentage

process_resident_memory_bytes
- Memory usage (RSS)
- Monitor for memory leaks
```

## Creating Custom Queries

### Prometheus Query Examples

```promql
# Request rate difference between apps
(sum(rate(http_requests_total{job="async-app"}[5m])) - 
 sum(rate(http_requests_total{job="sync-app"}[5m]))) / 
 sum(rate(http_requests_total{job="sync-app"}[5m])) * 100

# Top 5 slowest endpoints
topk(5, 
  histogram_quantile(0.95, 
    sum(rate(http_request_duration_seconds_bucket[5m])) by (endpoint, le)
  )
)

# Error rate by endpoint
sum(rate(http_requests_total{status=~"5.."}[5m])) by (endpoint) / 
sum(rate(http_requests_total[5m])) by (endpoint)

# Connection pool utilization
cassandra_active_connections / cassandra_connection_pool_size * 100
```

### Grafana Variables

Create dashboard variables for dynamic filtering:

```
# Application selector
Query: label_values(http_requests_total, job)
Variable: $app

# Endpoint selector  
Query: label_values(http_requests_total{job="$app"}, endpoint)
Variable: $endpoint

# Time range
Built-in: $__interval, $__range
```

## Log Analysis with Loki

### Viewing Logs

1. Open Grafana → Explore
2. Select Loki as data source
3. Use LogQL queries:

```logql
# All async app logs
{job="containerlogs", container_name="async-app"}

# Error logs only
{job="containerlogs", container_name="async-app"} |= "ERROR"

# Specific endpoint logs
{job="containerlogs", container_name="async-app"} |= "/api/v1/users" |= "POST"

# JSON parsing
{job="containerlogs", container_name="async-app"} | json | status >= 500
```

### Correlating Logs with Metrics

1. Find spike in error rate on dashboard
2. Click and drag to zoom time range
3. Switch to Explore tab
4. Query logs for same time range
5. Identify root cause

## Alerting Setup

### Example Alert Rules

Create `prometheus/alerts.yml`:

```yaml
groups:
  - name: performance
    rules:
      - alert: HighErrorRate
        expr: sum(rate(http_requests_total{status=~"5.."}[5m])) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is above 5% for 5 minutes"
      
      - alert: SlowResponseTime
        expr: histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le)) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Slow response times"
          description: "95th percentile latency is above 1 second"
      
      - alert: ConnectionPoolExhaustion
        expr: cassandra_active_connections / cassandra_connection_pool_size > 0.9
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Connection pool nearly exhausted"
          description: "Connection pool is at 90% capacity"
```

### Grafana Alerts

1. Edit panel → Alert tab
2. Create alert condition:
   ```
   WHEN avg() OF query(A, 5m, now) IS ABOVE 0.1
   ```
3. Configure notification channels
4. Set alert frequency

## Performance Monitoring Best Practices

### 1. Baseline Establishment

```bash
# Record normal operation metrics
curl -X POST http://localhost:9090/api/v1/admin/tsdb/snapshot

# Document typical values:
# - Normal RPS: 500-1000
# - Normal P95 latency: 20-50ms
# - Normal error rate: <0.1%
```

### 2. Dashboard Organization

- **Overview Dashboard**: High-level health indicators
- **Detailed Dashboards**: Specific component deep-dives
- **Troubleshooting Dashboard**: Error rates, slow queries, resource issues

### 3. Metric Retention

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    monitor: 'cassandra-perf'

# Retention policy
storage:
  tsdb:
    retention.time: 30d
    retention.size: 10GB
```

## Troubleshooting with Metrics

### High Latency Investigation

1. Check overall latency trend
2. Break down by endpoint
3. Check Cassandra query duration
4. Verify connection pool status
5. Review resource utilization

### Error Spike Investigation

1. Identify error rate increase
2. Filter by endpoint and status code
3. Check corresponding logs
4. Review Cassandra errors
5. Verify system resources

### Performance Degradation

1. Compare current vs baseline metrics
2. Check for gradual trends
3. Identify correlating factors
4. Review recent changes
5. Analyze resource consumption

## Monitoring Automation

### Automated Reports

```python
# generate_report.py
import requests
from datetime import datetime, timedelta

# Query Prometheus
end = datetime.now()
start = end - timedelta(hours=24)

query = 'avg(rate(http_requests_total[5m]))'
response = requests.get(
    'http://localhost:9090/api/v1/query_range',
    params={
        'query': query,
        'start': start.timestamp(),
        'end': end.timestamp(),
        'step': '5m'
    }
)

# Process and save results
```

### Continuous Monitoring

```bash
# Add to crontab
*/5 * * * * /path/to/check_metrics.sh

# check_metrics.sh
#!/bin/bash
ERROR_RATE=$(curl -s 'http://localhost:9090/api/v1/query?query=sum(rate(http_requests_total{status=~"5.."}[5m]))' | jq '.data.result[0].value[1]')

if (( $(echo "$ERROR_RATE > 0.05" | bc -l) )); then
    echo "High error rate: $ERROR_RATE" | mail -s "Alert: High Error Rate" admin@example.com
fi
```

## Next Steps

1. **Familiarize**: Explore all dashboards during normal operation
2. **Customize**: Add panels for specific use cases
3. **Alert Setup**: Configure alerts for critical metrics
4. **Documentation**: Document normal ranges and thresholds
5. **Integration**: Connect to incident management systems