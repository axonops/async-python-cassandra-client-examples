# Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                            Load Testing Tools                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐ │
│  │   Locust    │  │     k6      │  │  compare.py │  │  Web UI   │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └───────────┘ │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │ HTTP Requests
┌─────────────────────────────────┴───────────────────────────────────┐
│                          Application Layer                           │
│  ┌─────────────────────────┐  ┌─────────────────────────┐          │
│  │     Async FastAPI       │  │      Sync FastAPI       │          │
│  │  ┌─────────────────┐    │  │   ┌─────────────────┐   │          │
│  │  │ async-cassandra │    │  │   │ cassandra-driver│   │          │
│  │  └─────────────────┘    │  │   └─────────────────┘   │          │
│  │   Port: 8001            │  │    Port: 8002           │          │
│  └─────────────────────────┘  └─────────────────────────┘          │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │ CQL Protocol
┌─────────────────────────────────┴───────────────────────────────────┐
│                         Data Layer                                   │
│                    ┌─────────────────────┐                          │
│                    │  Cassandra Cluster  │                          │
│                    │    (3 nodes)        │                          │
│                    └─────────────────────┘                          │
└─────────────────────────────────────────────────────────────────────┘
                                  │ Metrics
┌─────────────────────────────────┴───────────────────────────────────┐
│                       Monitoring Stack                               │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌──────────────┐ │
│  │ Prometheus │  │  Grafana   │  │    Loki    │  │   Promtail   │ │
│  └────────────┘  └────────────┘  └────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. FastAPI Applications

Both applications implement identical functionality but use different Cassandra clients:

#### Async Application (`apps/async-app/`)
- **Framework**: FastAPI with async/await support
- **Cassandra Client**: async-cassandra (from TestPyPI)
- **Key Features**:
  - Non-blocking I/O operations
  - Concurrent request handling
  - Async connection pooling
  - Stream processing with async generators

#### Sync Application (`apps/sync-app/`)
- **Framework**: FastAPI (async framework, sync database operations)
- **Cassandra Client**: cassandra-driver (official DataStax driver)
- **Key Features**:
  - Traditional blocking I/O
  - Thread-based concurrency
  - Standard connection pooling
  - Stream processing with generators

### 2. Data Models

#### User Model
```python
{
  "id": "UUID",
  "username": "string",
  "email": "string",
  "created_at": "datetime",
  "profile_data": "JSON"
}
```

#### SensorData Model (Time-Series)
```python
{
  "device_id": "UUID",
  "timestamp": "datetime",
  "temperature": "float",
  "humidity": "float",
  "pressure": "float",
  "metadata": "JSON"
}
```

#### Document Model
```python
{
  "id": "UUID",
  "title": "string",
  "content": "text",
  "tags": ["string"],
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### 3. API Endpoints

Both applications expose identical endpoints:

#### CRUD Operations
- `POST /api/v1/users` - Create user
- `GET /api/v1/users/{id}` - Get user by ID
- `GET /api/v1/users` - List users with pagination
- `PUT /api/v1/users/{id}` - Update user
- `DELETE /api/v1/users/{id}` - Delete user
- `POST /api/v1/users/batch` - Batch create users
- Similar endpoints for documents

#### Streaming Operations
- `GET /api/v1/stream/sensor-data` - Stream sensor data
- `GET /api/v1/stream/documents` - Stream documents
- `GET /api/v1/stream/large-dataset/{size}` - Stream synthetic data
- `POST /api/v1/sensor-data/generate/{count}` - Generate test data

#### Monitoring
- `GET /health` - Health check endpoint
- `GET /metrics` - Prometheus metrics endpoint

### 4. Monitoring Stack

#### Prometheus
- **Purpose**: Time-series metrics collection
- **Scrape Interval**: 5 seconds for apps, 15 seconds for infrastructure
- **Key Metrics**:
  - HTTP request rate, duration, and errors
  - Cassandra query performance
  - Connection pool statistics
  - Resource utilization

#### Grafana
- **Purpose**: Metrics visualization and dashboards
- **Pre-configured Dashboards**:
  - Performance Comparison Dashboard
  - Cassandra Operations Dashboard
  - System Resources Dashboard
- **Features**:
  - Real-time updates
  - Historical analysis
  - Alert configuration

#### Loki & Promtail
- **Purpose**: Centralized log aggregation
- **Features**:
  - Structured JSON logging
  - Log correlation with metrics
  - Query and filtering capabilities

### 5. Load Testing Architecture

#### Locust
- **Type**: Python-based, distributed load testing
- **Features**:
  - User behavior simulation
  - Gradual ramp-up scenarios
  - Web UI for real-time monitoring
  - Distributed testing support

#### k6
- **Type**: JavaScript-based, developer-centric load testing
- **Features**:
  - Scenario-based testing
  - Built-in performance metrics
  - Threshold validation
  - CI/CD integration friendly

#### Custom Comparison Tool
- **Purpose**: Direct side-by-side performance comparison
- **Features**:
  - Identical workload generation
  - Statistical analysis
  - Visualization of results
  - Automated report generation

## Deployment Architecture

### Docker Compose Services

```yaml
services:
  cassandra:       # 3-node Cassandra cluster
  async-app:       # Async FastAPI application
  sync-app:        # Sync FastAPI application
  prometheus:      # Metrics collection
  grafana:         # Visualization
  loki:           # Log aggregation
  promtail:       # Log shipping
  web-ui:         # React-based UI
```

### Network Architecture
- All services communicate via Docker bridge network
- External ports exposed:
  - 8001: Async API
  - 8002: Sync API
  - 3000: Grafana
  - 3001: Web UI
  - 9090: Prometheus
  - 9042: Cassandra

### Resource Allocation
- Cassandra: 512MB heap (development)
- Applications: 4 workers each
- Monitoring: Minimal resources
- Recommended: 8GB+ RAM for full stack

## Security Considerations

### Current Implementation
- No authentication on APIs (development only)
- Grafana: Default admin/admin credentials
- All services on same network
- No TLS/SSL encryption

### Production Recommendations
- Implement API authentication (JWT/OAuth2)
- Enable TLS for all endpoints
- Network segmentation
- Secrets management
- Rate limiting
- Input validation