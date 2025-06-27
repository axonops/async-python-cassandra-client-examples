from pydantic_settings import BaseSettings
from pydantic import validator
from typing import List, Optional, Union


class Settings(BaseSettings):
    # Cassandra Configuration
    cassandra_hosts: Union[str, List[str]] = "localhost"
    cassandra_port: int = 9042
    cassandra_keyspace: str = "perftest"
    cassandra_username: Optional[str] = None
    cassandra_password: Optional[str] = None
    cassandra_datacenter: str = "datacenter1"
    
    # Application Configuration
    app_port: int = 8000
    workers: int = 4
    log_level: str = "INFO"
    
    # Performance Testing
    max_connections: int = 100
    connection_timeout: int = 10
    request_timeout: int = 30
    batch_size: int = 100
    stream_buffer_size: int = 1000
    
    # Monitoring
    prometheus_endpoint: str = "http://prometheus:9090"
    grafana_endpoint: str = "http://grafana:3000"
    loki_endpoint: str = "http://loki:3100"
    
    @validator('cassandra_hosts', pre=True)
    def parse_cassandra_hosts(cls, v):
        if isinstance(v, str):
            return [host.strip() for host in v.split(',')]
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()