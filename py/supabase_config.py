"""
Supabase Configuration and Setup
Handles connection, authentication, and database operations for the migration.
"""
import os
import asyncio
from typing import Dict, Any, Optional, List
from supabase import create_client, Client
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import logging
load_dotenv()
logger = logging.getLogger(__name__)
class SupabaseConfig:
    """Centralized Supabase configuration and connection management"""
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_anon_key = os.getenv('SUPABASE_KEY')
        self.supabase_service_role_key = os.getenv('SUPABASE_SERVICE_KEY')
        self.postgres_url = os.getenv('DATABASE_URL')
        self.postgres_url_non_pooling = os.getenv('DATABASE_URL')
        self._validate_config()
        self.client: Client = None
        self.service_client: Client = None
        self.engine = None
        self.async_engine = None
        self.async_session_maker = None
    def _validate_config(self):
        """Validate that all required environment variables are set"""
        required_vars = [
            'SUPABASE_URL',
            'SUPABASE_KEY',
            'SUPABASE_SERVICE_KEY',
            'DATABASE_URL'
        ]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {missing_vars}")
    def initialize_clients(self):
        """Initialize Supabase clients and database connections"""
        try:
            self.client = create_client(
                self.supabase_url,
                self.supabase_anon_key
            )
            self.service_client = create_client(
                self.supabase_url,
                self.supabase_service_role_key
            )
            self.engine = create_engine(
                self.postgres_url,
                pool_size=20,
                max_overflow=0,
                pool_pre_ping=True,
                echo=False
            )
            self.async_engine = create_async_engine(
                self.postgres_url.replace('postgres://', 'postgresql+asyncpg://'),
                pool_size=20,
                max_overflow=0,
                pool_pre_ping=True,
                echo=False
            )
            self.async_session_maker = sessionmaker(
                self.async_engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            logger.info("Supabase clients and database connections initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase clients: {e}")
            raise
    def test_connection(self) -> bool:
        """Test database connection and basic operations"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                if result.fetchone()[0] == 1:
                    logger.info("Database connection test successful")
                    return True
            return False
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    def run_schema_migration(self, schema_file: str = "migration/supabase_schema.sql"):
        """Run the schema migration SQL file"""
        try:
            with open(schema_file, 'r') as f:
                schema_sql = f.read()
            with self.engine.connect() as conn:
                statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
                for statement in statements:
                    if statement:
                        conn.execute(text(statement))
                conn.commit()
            logger.info("Schema migration completed successfully")
            return True
        except Exception as e:
            logger.error(f"Schema migration failed: {e}")
            return False
    async def async_execute(self, query: str, params: Dict[str, Any] = None) -> Any:
        """Execute async query with parameters"""
        async with self.async_session_maker() as session:
            try:
                result = await session.execute(text(query), params or {})
                await session.commit()
                return result
            except Exception as e:
                await session.rollback()
                logger.error(f"Async query execution failed: {e}")
                raise
    def get_user_by_clerk_id(self, clerk_id: str) -> Optional[Dict[str, Any]]:
        """Get user by Clerk ID using Supabase client"""
        try:
            response = self.service_client.table('users').select('*').eq('clerk_user_id', clerk_id).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Failed to get user by Clerk ID: {e}")
            return None
    def create_user(self, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create new user in Supabase"""
        try:
            response = self.service_client.table('users').insert(user_data).execute()
            if response.data:
                logger.info(f"Created user: {user_data.get('email')}")
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            return None
    def get_characters_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all characters for a user"""
        try:
            response = self.service_client.table('characters').select('*').eq('user_id', user_id).execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Failed to get characters for user {user_id}: {e}")
            return []
    def create_companion(self, companion_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create new companion in Supabase"""
        try:
            response = self.service_client.table('characters').insert(companion_data).execute()
            if response.data:
                logger.info(f"Created companion: {companion_data.get('name')}")
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Failed to create companion: {e}")
            return None
    def setup_storage_buckets(self):
        """Create necessary storage buckets for files"""
        try:
            self.service_client.storage.create_bucket(
                'avatars',
                options={
                    'public': True,
                    'allowedMimeTypes': ['image/jpeg', 'image/png', 'image/webp', 'image/gif'],
                    'fileSizeLimit': 5242880
                }
            )
            logger.info("Created avatars storage bucket")
        except Exception as e:
            logger.warning(f"Storage bucket creation warning: {e}")
    def close_connections(self):
        """Close all database connections"""
        try:
            if self.engine:
                self.engine.dispose()
            if self.async_engine:
                asyncio.create_task(self.async_engine.dispose())
            logger.info("Database connections closed")
        except Exception as e:
            logger.error(f"Error closing connections: {e}")
supabase_config = SupabaseConfig()
def get_supabase_config() -> SupabaseConfig:
    """Get the global Supabase configuration instance"""
    return supabase_config
def initialize_supabase() -> bool:
    """Initialize Supabase with full setup"""
    try:
        config = get_supabase_config()
        config.initialize_clients()
        if not config.test_connection():
            return False
        if not config.run_schema_migration():
            return False
        config.setup_storage_buckets()
        logger.info("Supabase initialization completed successfully")
        return True
    except Exception as e:
        logger.error(f"Supabase initialization failed: {e}")
        return False
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    if initialize_supabase():
        print("✅ Supabase setup completed successfully")
        config = get_supabase_config()
        test_user = {
            'email': 'test@example.com',
            'clerk_user_id': 'test_clerk_id'
        }
        user = config.create_user(test_user)
        if user:
            print(f"✅ Test user created: {user['id']}")
        config.close_connections()
    else:
        print("❌ Supabase setup failed")
