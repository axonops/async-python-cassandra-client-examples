from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from cassandra.policies import DCAwareRoundRobinPolicy
from typing import Optional
import logging
from .config import settings

logger = logging.getLogger(__name__)


class CassandraClient:
    def __init__(self):
        self.cluster: Optional[Cluster] = None
        self.session: Optional[object] = None
    
    def connect(self):
        try:
            auth_provider = None
            if settings.cassandra_username and settings.cassandra_password:
                auth_provider = PlainTextAuthProvider(
                    username=settings.cassandra_username,
                    password=settings.cassandra_password
                )
            
            self.cluster = Cluster(
                contact_points=settings.cassandra_hosts,
                port=settings.cassandra_port,
                auth_provider=auth_provider,
                protocol_version=4,
                load_balancing_policy=DCAwareRoundRobinPolicy(
                    local_dc=settings.cassandra_datacenter
                ),
                connect_timeout=settings.connection_timeout,
                control_connection_timeout=settings.connection_timeout,
                idle_heartbeat_interval=30,
                connection_class=None,
                max_schema_agreement_wait=10,
                compression=True
            )
            
            # Set pool size
            self.cluster.set_core_connections_per_host(1, settings.max_connections // 4)
            self.cluster.set_max_connections_per_host(1, settings.max_connections)
            
            self.session = self.cluster.connect()
            self.session.default_timeout = settings.request_timeout
            
            # Create keyspace if not exists
            self.session.execute(f"""
                CREATE KEYSPACE IF NOT EXISTS {settings.cassandra_keyspace}
                WITH replication = {{
                    'class': 'SimpleStrategy',
                    'replication_factor': 1
                }}
            """)
            
            self.session.set_keyspace(settings.cassandra_keyspace)
            
            # Create tables
            self._create_tables()
            
            logger.info("Connected to Cassandra successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Cassandra: {e}")
            raise
    
    def _create_tables(self):
        # Users table
        self.session.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id UUID PRIMARY KEY,
                username TEXT,
                email TEXT,
                created_at TIMESTAMP,
                profile_data TEXT
            )
        """)
        
        # Create indexes
        self.session.execute("""
            CREATE INDEX IF NOT EXISTS users_username_idx ON users (username)
        """)
        
        self.session.execute("""
            CREATE INDEX IF NOT EXISTS users_email_idx ON users (email)
        """)
        
        # Sensor data table (time-series)
        self.session.execute("""
            CREATE TABLE IF NOT EXISTS sensor_data (
                device_id UUID,
                timestamp TIMESTAMP,
                temperature FLOAT,
                humidity FLOAT,
                pressure FLOAT,
                metadata TEXT,
                PRIMARY KEY (device_id, timestamp)
            ) WITH CLUSTERING ORDER BY (timestamp DESC)
        """)
        
        # Documents table
        self.session.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id UUID PRIMARY KEY,
                title TEXT,
                content TEXT,
                tags LIST<TEXT>,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        """)
        
        self.session.execute("""
            CREATE INDEX IF NOT EXISTS documents_title_idx ON documents (title)
        """)
    
    def close(self):
        if self.session:
            self.session.shutdown()
        if self.cluster:
            self.cluster.shutdown()
    
    def get_session(self):
        return self.session


db = CassandraClient()