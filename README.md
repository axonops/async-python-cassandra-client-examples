# Async Python Cassandra Client Performance Testing Framework

A comprehensive performance testing framework to evaluate the async-python-cassandra client against the standard Python Cassandra driver.

## Overview

This framework provides:
- Two identical FastAPI applications (async and sync implementations)
- Performance testing endpoints
- Real-time monitoring with Prometheus and Grafana
- Load testing capabilities
- Interactive web UI for testing and visualization

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+ (for local development)
- 8GB+ RAM recommended

### Running with Local Cassandra

```bash
# Clone the repository
git clone <repository-url>
cd async-python-cassandra-client-examples

# Copy environment variables
cp .env.example .env

# Start all services
docker-compose up -d

# Wait for services to be healthy
docker-compose ps

# View logs
docker-compose logs -f
```

### Running with External Cassandra

```bash
# Set your Cassandra cluster details
export CASSANDRA_HOSTS=cassandra1.example.com,cassandra2.example.com
export CASSANDRA_USERNAME=your_username
export CASSANDRA_PASSWORD=your_password

# Use the external compose file
docker-compose -f docker-compose.external.yml up -d
```

## Service URLs

- **Async App**: http://localhost:8001
- **Sync App**: http://localhost:8002  
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Web UI**: http://localhost:3001

## API Endpoints

### CRUD Operations

- `POST /api/v1/users` - Create user
- `GET /api/v1/users/{id}` - Get user by ID
- `GET /api/v1/users` - List users with pagination
- `PUT /api/v1/users/{id}` - Update user
- `DELETE /api/v1/users/{id}` - Delete user
- `POST /api/v1/documents` - Create document
- `GET /api/v1/documents/{id}` - Get document


### Streaming

- `GET /api/v1/stream/sensor-data` - Stream sensor data
- `GET /api/v1/stream/large-dataset/{size}` - Stream large dataset
- `GET /api/v1/stream/documents` - Stream documents

## Performance Testing

Performance testing should be done using external load testing tools that generate concurrent requests from outside the application. This provides accurate measurements of how the applications handle real-world load.

### Quick Performance Comparison

```bash
# Run automated comparison tests
cd load-testing
python compare.py
```

This will run identical workloads against both applications and generate a comparison report with visualizations.

### Load Testing with Locust

```bash
# Install dependencies
pip install -r load-testing/requirements.txt

# Run Locust tests
cd load-testing
locust -f locustfile.py --host http://localhost:8001

# Run k6 tests (requires k6 installation)
k6 run k6-script.js --env BASE_URL=http://localhost:8001

# Run comprehensive test suite
./run-tests.sh
```

### Load Testing Best Practices

1. **Always test from external clients**: Never simulate load from within the application itself
2. **Test both applications identically**: Use the same workload patterns for fair comparison
3. **Monitor resource usage**: Watch CPU, memory, and connection pool metrics during tests
4. **Test different scenarios**:
   - Light load (baseline performance)
   - Normal load (expected traffic)
   - Heavy load (peak traffic)
   - Stress test (beyond capacity)

## Monitoring

### Grafana Dashboards

1. Navigate to http://localhost:3000
2. Login with admin/admin
3. Import provided dashboards from `monitoring/grafana/dashboards/`

### Key Metrics

- Request rate and latency
- Cassandra query performance
- Connection pool statistics
- Resource utilization
- Error rates

## Development

### Local Development Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install async app dependencies
cd apps/async-app
pip install -r requirements.txt

# Run async app locally
python -m app.main

# In another terminal, run sync app
cd apps/sync-app
pip install -r requirements.txt
python -m app.main
```

### Running Tests

```bash
# Unit tests
pytest apps/async-app/tests
pytest apps/sync-app/tests

# Integration tests
docker-compose up -d
pytest integration-tests/
```

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Web UI    │     │   Grafana   │     │ Prometheus  │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                    │
       ├───────────────────┴────────────────────┤
       │                                        │
┌──────▼──────┐     ┌──────────────┐    ┌──────▼──────┐
│  Async App  │     │              │    │  Sync App   │
│  (FastAPI)  │     │   Cassandra  │    │  (FastAPI)  │
│async-client │────▶│    Cluster   │◀───│ sync-driver │
└─────────────┘     └──────────────┘    └─────────────┘
```

## Configuration

Key environment variables:

```env
# Cassandra settings
CASSANDRA_HOSTS=localhost
CASSANDRA_PORT=9042
CASSANDRA_KEYSPACE=perftest
CASSANDRA_USERNAME=
CASSANDRA_PASSWORD=

# Performance settings
MAX_CONNECTIONS=100
CONNECTION_TIMEOUT=10
REQUEST_TIMEOUT=30
BATCH_SIZE=100
STREAM_BUFFER_SIZE=1000

# Application settings
APP_PORT=8000
WORKERS=4
LOG_LEVEL=INFO
```

## Troubleshooting

### Common Issues

1. **Cassandra not starting**: Increase Docker memory allocation
2. **Connection refused**: Wait for Cassandra health check to pass
3. **Metrics not showing**: Check Prometheus targets at http://localhost:9090/targets

### Debug Commands

```bash
# Check service health
docker-compose ps

# View logs
docker-compose logs -f cassandra
docker-compose logs -f async-app

# Access Cassandra shell
docker-compose exec cassandra cqlsh

# Restart a service
docker-compose restart async-app
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details