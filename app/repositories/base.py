from typing import Dict, List, Optional, Type, TypeVar, Generic
from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo import ReturnDocument
from app.models.base import BaseDocument

T = TypeVar('T', bound=BaseDocument)


class BaseRepository(Generic[T]):
    """Base repository class with common CRUD operations."""
    
    def __init__(self, db: AsyncIOMotorDatabase, model_class: Type[T], collection_name: str):
        self.db = db
        self.collection: AsyncIOMotorCollection = db[collection_name]
        self.model_class = model_class
    
    async def create(self, data: Dict) -> T:
        """Create a new document."""
        now = datetime.utcnow()
        data.update({
            "created_at": now,
            "updated_at": now
        })
        
        result = await self.collection.insert_one(data)
        data["_id"] = result.inserted_id
        return self.model_class(**data)
    
    async def get_by_id(self, doc_id: str) -> Optional[T]:
        """Get document by ID."""
        if not ObjectId.is_valid(doc_id):
            return None
            
        doc = await self.collection.find_one({"_id": ObjectId(doc_id)})
        if doc:
            return self.model_class(**doc)
        return None
    
    async def update(self, doc_id: str, update_data: Dict) -> Optional[T]:
        """Update document by ID."""
        if not ObjectId.is_valid(doc_id):
            return None
        
        update_data["updated_at"] = datetime.utcnow()
        
        doc = await self.collection.find_one_and_update(
            {"_id": ObjectId(doc_id)},
            {"$set": update_data},
            return_document=ReturnDocument.AFTER
        )
        
        if doc:
            return self.model_class(**doc)
        return None
    
    async def delete(self, doc_id: str) -> bool:
        """Delete document by ID."""
        if not ObjectId.is_valid(doc_id):
            return False
            
        result = await self.collection.delete_one({"_id": ObjectId(doc_id)})
        return result.deleted_count > 0
    
    async def find(
        self, 
        filter_dict: Dict = None, 
        skip: int = 0, 
        limit: int = 20,
        sort_by: str = "created_at",
        sort_order: int = -1
    ) -> List[T]:
        """Find documents with filtering, pagination, and sorting."""
        if filter_dict is None:
            filter_dict = {}
        
        cursor = self.collection.find(filter_dict)
        cursor = cursor.sort(sort_by, sort_order)
        cursor = cursor.skip(skip).limit(limit)
        
        docs = await cursor.to_list(length=limit)
        return [self.model_class(**doc) for doc in docs]
    
    async def count(self, filter_dict: Dict = None) -> int:
        """Count documents matching filter."""
        if filter_dict is None:
            filter_dict = {}
        return await self.collection.count_documents(filter_dict)
    
    async def find_one(self, filter_dict: Dict) -> Optional[T]:
        """Find a single document by filter."""
        doc = await self.collection.find_one(filter_dict)
        if doc:
            return self.model_class(**doc)
        return None
    
    async def exists(self, filter_dict: Dict) -> bool:
        """Check if document exists."""
        doc = await self.collection.find_one(filter_dict, {"_id": 1})
        return doc is not None
    
    async def bulk_create(self, data_list: List[Dict]) -> List[T]:
        """Create multiple documents."""
        now = datetime.utcnow()
        for data in data_list:
            data.update({
                "created_at": now,
                "updated_at": now
            })
        
        result = await self.collection.insert_many(data_list)
        
        # Add inserted IDs back to the data
        for i, inserted_id in enumerate(result.inserted_ids):
            data_list[i]["_id"] = inserted_id
        
        return [self.model_class(**data) for data in data_list]
    
    async def delete_many(self, filter_dict: Dict) -> int:
        """Delete multiple documents."""
        result = await self.collection.delete_many(filter_dict)
        return result.deleted_count 