from typing import Optional
import structlog
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import settings

logger = structlog.get_logger(__name__)


class MongoDatabase:
    """Simple MongoDB connection manager."""
    
    def __init__(self, uri: str, db_name: str):
        self.uri = uri
        self.db_name = db_name
        self.client: Optional[AsyncIOMotorClient] = None
        self.database: Optional[AsyncIOMotorDatabase] = None
    
    async def connect(self) -> None:
        """Establish MongoDB connection."""
        try:
            self.client = AsyncIOMotorClient(self.uri)
            self.database = self.client[self.db_name]
            logger.info("MongoDB client created", db_name=self.db_name)
        except Exception as e:
            logger.error("Failed to create MongoDB client", error=str(e))
            raise
    
    async def disconnect(self) -> None:
        """Close MongoDB connection."""
        if self.client is not None:
            self.client.close()
            logger.info("MongoDB connection closed")
    
    async def ping(self) -> bool:
        """Test MongoDB connection."""
        try:
            if self.client is None:
                return False
            await self.client.admin.command('ping')
            logger.info("MongoDB ping successful", db_name=self.db_name)
            return True
        except Exception as e:
            logger.error("MongoDB ping failed", error=str(e))
            return False
    
    def get_database(self) -> AsyncIOMotorDatabase:
        """Get MongoDB database instance."""
        if self.database is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self.database
    
    def get_client(self) -> AsyncIOMotorClient:
        """Get MongoDB client instance."""
        if self.client is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self.client
    
    async def create_indexes(self) -> None:
        """Create MongoDB indexes for all collections."""
        if self.database is None:
            logger.warning("Database not available for index creation")
            return
        
        try:
            # Import repositories here to avoid circular imports
            from app.repositories.user import UserRepository
            from app.repositories.conversation import ConversationRepository
            from app.repositories.task import TaskRepository
            
            # Create repository instances and indexes
            user_repo = UserRepository(self.database)
            conversation_repo = ConversationRepository(self.database)
            task_repo = TaskRepository(self.database)
            
            await user_repo.create_indexes()
            await conversation_repo.create_indexes()
            await task_repo.create_indexes()
            
            logger.info("Database indexes created successfully")
        except Exception as e:
            logger.warning("Failed to create some database indexes", error=str(e))


async def create_mongodb_connection(uri: str = None, db_name: str = None) -> MongoDatabase:
    """Create and initialize a MongoDB connection."""
    uri = uri or str(settings.mongo_uri)
    db_name = db_name or settings.mongo_db_name
    
    mongo_db = MongoDatabase(uri, db_name)
    await mongo_db.connect()
    
    # Test connection
    if not await mongo_db.ping():
        raise RuntimeError("Failed to establish MongoDB connection")
    
    # Create indexes
    await mongo_db.create_indexes()
    
    return mongo_db

