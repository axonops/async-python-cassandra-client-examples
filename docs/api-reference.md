# API Reference

## Overview

Both the async and sync applications expose identical REST APIs. The only difference is the underlying Cassandra client implementation.

- **Async API Base URL**: `http://localhost:8001`
- **Sync API Base URL**: `http://localhost:8002`

## Authentication

Currently, no authentication is required (development only). In production, implement JWT or OAuth2.

## Common Headers

```http
Content-Type: application/json
Accept: application/json
```

## Endpoints

### Health Check

#### GET /health
Check service health and Cassandra connectivity.

**Response**
```json
{
  "status": "healthy",
  "cassandra": "healthy",
  "app_type": "async"  // or "sync"
}
```

### User Management

#### POST /api/v1/users
Create a new user.

**Request Body**
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "profile_data": {
    "bio": "Software developer",
    "location": "San Francisco",
    "interests": ["coding", "music"]
  }
}
```

**Response** (201 Created)
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "john_doe",
  "email": "john@example.com",
  "created_at": "2024-01-15T10:30:00Z",
  "profile_data": {
    "bio": "Software developer",
    "location": "San Francisco",
    "interests": ["coding", "music"]
  }
}
```

#### GET /api/v1/users/{user_id}
Retrieve a user by ID.

**Path Parameters**
- `user_id` (UUID) - User's unique identifier

**Response** (200 OK)
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "john_doe",
  "email": "john@example.com",
  "created_at": "2024-01-15T10:30:00Z",
  "profile_data": {...}
}
```

**Error Response** (404 Not Found)
```json
{
  "detail": "User not found"
}
```

#### GET /api/v1/users
List users with pagination.

**Query Parameters**
- `page` (int, optional) - Page number (default: 1)
- `page_size` (int, optional) - Items per page (default: 20, max: 1000)
- `username` (string, optional) - Filter by username

**Response** (200 OK)
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "john_doe",
    "email": "john@example.com",
    "created_at": "2024-01-15T10:30:00Z",
    "profile_data": {...}
  },
  // ... more users
]
```

#### PUT /api/v1/users/{user_id}
Update a user.

**Path Parameters**
- `user_id` (UUID) - User's unique identifier

**Request Body**
```json
{
  "username": "john_doe_updated",
  "email": "john.new@example.com",
  "profile_data": {
    "bio": "Senior software developer"
  }
}
```

**Response** (200 OK)
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "john_doe_updated",
  "email": "john.new@example.com",
  "created_at": "2024-01-15T10:30:00Z",
  "profile_data": {
    "bio": "Senior software developer"
  }
}
```

#### DELETE /api/v1/users/{user_id}
Delete a user.

**Path Parameters**
- `user_id` (UUID) - User's unique identifier

**Response** (200 OK)
```json
{
  "message": "User deleted successfully"
}
```

#### POST /api/v1/users/batch
Create multiple users in a single request.

**Request Body**
```json
[
  {
    "username": "user1",
    "email": "user1@example.com",
    "profile_data": {}
  },
  {
    "username": "user2",
    "email": "user2@example.com",
    "profile_data": {}
  }
]
```

**Response** (200 OK)
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "username": "user1",
    "email": "user1@example.com",
    "created_at": "2024-01-15T10:30:00Z",
    "profile_data": {}
  },
  {
    "id": "550e8400-e29b-41d4-a716-446655440002",
    "username": "user2",
    "email": "user2@example.com",
    "created_at": "2024-01-15T10:30:00Z",
    "profile_data": {}
  }
]
```

### Document Management

#### POST /api/v1/documents
Create a new document.

**Request Body**
```json
{
  "title": "My Document",
  "content": "This is the document content...",
  "tags": ["important", "project-a"]
}
```

**Response** (201 Created)
```json
{
  "id": "650e8400-e29b-41d4-a716-446655440000",
  "title": "My Document",
  "content": "This is the document content...",
  "tags": ["important", "project-a"],
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

#### GET /api/v1/documents/{document_id}
Retrieve a document by ID.

**Path Parameters**
- `document_id` (UUID) - Document's unique identifier

**Response** (200 OK)
```json
{
  "id": "650e8400-e29b-41d4-a716-446655440000",
  "title": "My Document",
  "content": "This is the document content...",
  "tags": ["important", "project-a"],
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### Streaming Operations

#### GET /api/v1/stream/sensor-data
Stream sensor data with optional filtering.

**Query Parameters**
- `device_id` (UUID, optional) - Filter by device
- `start_time` (datetime, optional) - Start timestamp
- `end_time` (datetime, optional) - End timestamp
- `batch_size` (int, optional) - Records per batch (default: 100)

**Response** (200 OK)
```
Content-Type: application/x-ndjson

{"device_id":"550e8400-e29b-41d4-a716-446655440000","timestamp":"2024-01-15T10:30:00Z","temperature":22.5,"humidity":45.0,"pressure":1013.25,"metadata":{}}
{"device_id":"550e8400-e29b-41d4-a716-446655440000","timestamp":"2024-01-15T10:31:00Z","temperature":22.6,"humidity":44.8,"pressure":1013.20,"metadata":{}}
...
```

#### POST /api/v1/sensor-data/generate/{count}
Generate test sensor data.

**Path Parameters**
- `count` (int) - Number of records to generate (max: 10000)

**Query Parameters**
- `device_id` (UUID, optional) - Device ID to use

**Response** (200 OK)
```json
{
  "message": "Generated 1000 sensor data records",
  "device_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

#### GET /api/v1/stream/large-dataset/{size}
Stream synthetic data for testing.

**Path Parameters**
- `size` (int) - Number of records to stream

**Response** (200 OK)
```
Content-Type: application/x-ndjson

{"index":0,"timestamp":"2024-01-15T10:30:00Z","data":"Record 0 of 1000","value":0.0}
{"index":1,"timestamp":"2024-01-15T10:30:01Z","data":"Record 1 of 1000","value":1.5}
...
```

#### GET /api/v1/stream/documents
Stream documents with optional filtering.

**Query Parameters**
- `page_size` (int, optional) - Records per batch (default: 100)
- `title_filter` (string, optional) - Filter by title

**Response** (200 OK)
```
Content-Type: application/x-ndjson

{"id":"650e8400-e29b-41d4-a716-446655440000","title":"Document 1","content":"Content preview...","tags":["tag1"],"created_at":"2024-01-15T10:30:00Z","updated_at":"2024-01-15T10:30:00Z"}
{"id":"650e8400-e29b-41d4-a716-446655440001","title":"Document 2","content":"Content preview...","tags":["tag2"],"created_at":"2024-01-15T10:31:00Z","updated_at":"2024-01-15T10:31:00Z"}
...
```

### Metrics

#### GET /metrics
Prometheus-format metrics endpoint.

**Response** (200 OK)
```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",endpoint="/api/v1/users",status="200"} 42.0

# HELP http_request_duration_seconds HTTP request duration in seconds
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{method="GET",endpoint="/api/v1/users",le="0.005"} 10.0
...
```

## Error Responses

All endpoints follow a consistent error response format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

Common HTTP status codes:
- `400` - Bad Request (invalid input)
- `404` - Not Found (resource doesn't exist)
- `422` - Unprocessable Entity (validation error)
- `500` - Internal Server Error
- `503` - Service Unavailable (Cassandra connection issue)

## Rate Limiting

Currently not implemented. In production, consider:
- 1000 requests per minute per IP
- 100 concurrent connections per IP
- Larger limits for authenticated users

## WebSocket Support

Not currently implemented. Future versions may include:
- Real-time metrics streaming
- Live query results
- Push notifications

## Examples

### cURL Examples

```bash
# Create a user
curl -X POST http://localhost:8001/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@example.com"}'

# Get user
curl http://localhost:8001/api/v1/users/550e8400-e29b-41d4-a716-446655440000

# Stream sensor data
curl http://localhost:8001/api/v1/stream/sensor-data?batch_size=10

# Generate test data
curl -X POST http://localhost:8001/api/v1/sensor-data/generate/1000
```

### Python Examples

```python
import requests
import json

# Create user
user_data = {
    "username": "python_user",
    "email": "python@example.com",
    "profile_data": {"language": "Python"}
}
response = requests.post(
    "http://localhost:8001/api/v1/users",
    json=user_data
)
user = response.json()
print(f"Created user: {user['id']}")

# Stream data
import requests

response = requests.get(
    "http://localhost:8001/api/v1/stream/sensor-data",
    params={"batch_size": 100},
    stream=True
)

for line in response.iter_lines():
    if line:
        data = json.loads(line)
        print(f"Temperature: {data['temperature']}°C")
```

### JavaScript Examples

```javascript
// Create user
const userData = {
  username: 'js_user',
  email: 'js@example.com',
  profile_data: { language: 'JavaScript' }
};

fetch('http://localhost:8001/api/v1/users', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(userData)
})
.then(response => response.json())
.then(user => console.log('Created user:', user.id));

// Stream data
const response = await fetch('http://localhost:8001/api/v1/stream/sensor-data?batch_size=10');
const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  
  const lines = decoder.decode(value).split('\n');
  for (const line of lines) {
    if (line) {
      const data = JSON.parse(line);
      console.log(`Temperature: ${data.temperature}°C`);
    }
  }
}
```