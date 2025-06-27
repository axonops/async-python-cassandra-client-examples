from prometheus_client import Counter, Histogram, Gauge, generate_latest
import time
from functools import wraps
from typing import Callable
import asyncio

# Request metrics
request_count = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

request_size = Histogram(
    'http_request_size_bytes',
    'HTTP request size in bytes',
    ['method', 'endpoint']
)

response_size = Histogram(
    'http_response_size_bytes',
    'HTTP response size in bytes',
    ['method', 'endpoint']
)

# Cassandra metrics
cassandra_query_duration = Histogram(
    'cassandra_query_duration_seconds',
    'Cassandra query duration in seconds',
    ['operation', 'table']
)

cassandra_query_count = Counter(
    'cassandra_queries_total',
    'Total Cassandra queries',
    ['operation', 'table', 'status']
)

cassandra_connection_pool_size = Gauge(
    'cassandra_connection_pool_size',
    'Current Cassandra connection pool size'
)

cassandra_active_connections = Gauge(
    'cassandra_active_connections',
    'Number of active Cassandra connections'
)

# Application metrics
concurrent_operations = Gauge(
    'app_concurrent_operations',
    'Number of concurrent operations',
    ['operation_type']
)

stream_buffer_size = Gauge(
    'app_stream_buffer_size',
    'Current stream buffer size in bytes',
    ['stream_type']
)


def track_request_metrics(endpoint: str):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            method = kwargs.get('request', args[0] if args else None)
            method_name = method.method if hasattr(method, 'method') else 'UNKNOWN'
            
            try:
                result = await func(*args, **kwargs)
                status = getattr(result, 'status_code', 200)
                request_count.labels(
                    method=method_name,
                    endpoint=endpoint,
                    status=status
                ).inc()
                return result
            except Exception as e:
                request_count.labels(
                    method=method_name,
                    endpoint=endpoint,
                    status=500
                ).inc()
                raise
            finally:
                duration = time.time() - start_time
                request_duration.labels(
                    method=method_name,
                    endpoint=endpoint
                ).observe(duration)
        
        return wrapper
    return decorator


def track_cassandra_operation(operation: str, table: str):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                cassandra_query_count.labels(
                    operation=operation,
                    table=table,
                    status='success'
                ).inc()
                return result
            except Exception as e:
                cassandra_query_count.labels(
                    operation=operation,
                    table=table,
                    status='error'
                ).inc()
                raise
            finally:
                duration = time.time() - start_time
                cassandra_query_duration.labels(
                    operation=operation,
                    table=table
                ).observe(duration)
        
        return wrapper
    return decorator


class MetricsMiddleware:
    async def __call__(self, request, call_next):
        start_time = time.time()
        
        # Track request size
        content_length = request.headers.get('content-length')
        if content_length:
            request_size.labels(
                method=request.method,
                endpoint=request.url.path
            ).observe(int(content_length))
        
        response = await call_next(request)
        
        # Track response metrics
        duration = time.time() - start_time
        request_duration.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)
        
        request_count.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()
        
        # Track response size
        if hasattr(response, 'headers') and 'content-length' in response.headers:
            response_size.labels(
                method=request.method,
                endpoint=request.url.path
            ).observe(int(response.headers['content-length']))
        
        return response


async def get_metrics():
    return generate_latest()