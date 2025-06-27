from async_cassandra import create_client
from typing import Optional
import logging
from .config import settings

logger = logging.getLogger(__name__)


class CassandraClient:
    def __init__(self):
        self.client: Optional[object] = None
        self.session: Optional[object] = None
    
    async def connect(self):
        try:
            self.client = await create_client(
                contact_points=settings.cassandra_hosts,
                port=settings.cassandra_port,
                auth_provider={
                    'username': settings.cassandra_username,
                    'password': settings.cassandra_password
                } if settings.cassandra_username else None,
                protocol_version=4,
                connection_timeout=settings.connection_timeout,
                request_timeout=settings.request_timeout,
                pool_size=settings.max_connections
            )
            
            self.session = await self.client.connect()
            
            # Create keyspace if not exists
            await self.session.execute(f"""
                CREATE KEYSPACE IF NOT EXISTS {settings.cassandra_keyspace}
                WITH replication = {{
                    'class': 'SimpleStrategy',
                    'replication_factor': 1
                }}
            """)
            
            await self.session.set_keyspace(settings.cassandra_keyspace)
            
            # Create tables
            await self._create_tables()
            
            logger.info("Connected to Cassandra successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Cassandra: {e}")
            raise
    
    async def _create_tables(self):
        # Users table
        await self.session.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id UUID PRIMARY KEY,
                username TEXT,
                email TEXT,
                created_at TIMESTAMP,
                profile_data TEXT
            )
        """)
        
        # Create indexes
        await self.session.execute("""
            CREATE INDEX IF NOT EXISTS users_username_idx ON users (username)
        """)
        
        await self.session.execute("""
            CREATE INDEX IF NOT EXISTS users_email_idx ON users (email)
        """)
        
        # Sensor data table (time-series)
        await self.session.execute("""
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
        await self.session.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id UUID PRIMARY KEY,
                title TEXT,
                content TEXT,
                tags LIST<TEXT>,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        """)
        
        await self.session.execute("""
            CREATE INDEX IF NOT EXISTS documents_title_idx ON documents (title)
        """)
    
    async def close(self):
        if self.session:
            await self.session.close()
        if self.client:
            await self.client.close()
    
    def get_session(self):
        return self.session


db = CassandraClient()