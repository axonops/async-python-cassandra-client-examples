# Getting Started

## Prerequisites

Before starting, ensure you have:

- Docker Desktop installed (version 20.10+)
- Docker Compose (usually included with Docker Desktop)
- 8GB+ available RAM
- Git for cloning the repository
- (Optional) Python 3.11+ for local development

## Quick Start (5 minutes)

### 1. Clone the Repository

```bash
git clone <repository-url>
cd async-python-cassandra-client-examples
```

### 2. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env if you need custom settings (optional)
# nano .env
```

### 3. Start the Stack

```bash
# Start all services
docker-compose up -d

# Wait for services to be healthy (about 2-3 minutes)
docker-compose ps

# Check logs if needed
docker-compose logs -f cassandra
```

### 4. Verify Services

Open your browser and check:
- Web UI: http://localhost:3001
- Async API Docs: http://localhost:8001/docs
- Sync API Docs: http://localhost:8002/docs
- Grafana: http://localhost:3000 (login: admin/admin)

### 5. Run Your First Test

```bash
# Navigate to load testing directory
cd load-testing

# Install Python dependencies
pip install -r requirements.txt

# Run a quick comparison test
python compare.py
```

## Step-by-Step Setup

### Step 1: Understanding the Services

When you run `docker-compose up`, the following services start:

1. **Cassandra** - Database (takes 1-2 minutes to initialize)
2. **Async App** - FastAPI with async-cassandra client
3. **Sync App** - FastAPI with standard cassandra-driver
4. **Prometheus** - Metrics collection
5. **Grafana** - Dashboards and visualization
6. **Loki** - Log aggregation
7. **Web UI** - Interactive testing interface

### Step 2: Initial Data Setup

The applications automatically create the keyspace and tables on startup:

```sql
-- Keyspace
CREATE KEYSPACE IF NOT EXISTS perftest 
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};

-- Tables created automatically:
-- - users
-- - sensor_data  
-- - documents
```

### Step 3: Testing the APIs

#### Create a User (Async API)
```bash
curl -X POST http://localhost:8001/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "profile_data": {"location": "San Francisco"}
  }'
```

#### Create a User (Sync API)
```bash
curl -X POST http://localhost:8002/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser2",
    "email": "test2@example.com",
    "profile_data": {"location": "New York"}
  }'
```

#### List Users
```bash
# Async API
curl http://localhost:8001/api/v1/users

# Sync API
curl http://localhost:8002/api/v1/users
```

### Step 4: Using the Web UI

1. Open http://localhost:3001
2. Navigate to "CRUD Operations"
3. Select either "Async App" or "Sync App"
4. Try creating, reading, updating, and deleting records

### Step 5: Running Load Tests

#### Option 1: Locust (Web-based)
```bash
cd load-testing
locust -f locustfile.py --host http://localhost:8001

# Open http://localhost:8089
# Enter number of users and spawn rate
# Start the test
```

#### Option 2: k6 (CLI-based)
```bash
# Install k6 first: https://k6.io/docs/getting-started/installation/
k6 run k6-script.js --env BASE_URL=http://localhost:8001
```

#### Option 3: Automated Comparison
```bash
python compare.py
# This runs identical tests against both apps and generates a report
```

### Step 6: Viewing Results

1. **Grafana Dashboards**
   - Open http://localhost:3000
   - Login with admin/admin
   - Navigate to Dashboards → Performance Comparison

2. **Test Reports**
   - Check `load-testing/results/` for test outputs
   - HTML reports from Locust
   - JSON data from k6
   - PNG charts from compare.py

## Common Tasks

### Starting Fresh
```bash
# Stop all services and remove data
docker-compose down -v

# Start again
docker-compose up -d
```

### Checking Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f async-app
docker-compose logs -f sync-app
```

### Accessing Cassandra
```bash
# Connect to Cassandra
docker-compose exec cassandra cqlsh

# In cqlsh:
USE perftest;
SELECT COUNT(*) FROM users;
```

### Scaling Services
```bash
# Run with more workers
docker-compose up -d --scale async-app=3
```

## Troubleshooting Quick Fixes

### Cassandra Won't Start
```bash
# Increase Docker memory to 6GB+
# Check Docker Desktop → Preferences → Resources
```

### Port Already in Use
```bash
# Find what's using the port
lsof -i :8001

# Change port in docker-compose.yml
# or stop the conflicting service
```

### Slow Performance
```bash
# Check resource usage
docker stats

# Restart services
docker-compose restart async-app sync-app
```

## Next Steps

1. **Run Performance Tests**: See [Load Testing Guide](./load-testing-guide.md)
2. **Explore Metrics**: See [Monitoring Guide](./monitoring.md)
3. **Optimize Performance**: See [Performance Tuning](./performance-tuning.md)
4. **API Details**: See [API Reference](./api-reference.md)