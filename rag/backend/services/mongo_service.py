from motor.motor_asyncio import AsyncIOMotorClient
from backend.config import settings

class MongoService:
    def __init__(self):
        self.client = AsyncIOMotorClient(settings.MONGODB_URL)
        self.db = self.client[settings.DATABASE_NAME]
        
        # Collections
        self.cases = self.db.cases
        self.crime_records = self.db.crime_records
        self.persons = self.db.persons
        
    async def insert_many(self, collection_name: str, documents: list[dict]):
        collection = self.db[collection_name]
        if documents:
            await collection.insert_many(documents)
            
    async def search_cases(self, query: dict, limit: int = 10):
        """Perform a structured search on cases."""
        cursor = self.cases.find(query).limit(limit)
        return await cursor.to_list(length=limit)

# Singleton instance
mongo_service = MongoService()
