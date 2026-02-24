from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING, TEXT
from typing import Any, Optional
from models import LogDocument
from os import getenv
import asyncio

class Database:
    client: AsyncIOMotorClient
    db: Any

    def __init__(self, uri: str = getenv("MONGODB_URL")):
        self.client = AsyncIOMotorClient(uri)
        self.db = self.client.log_platform

    async def create_indexes(self):
        """Create optimized indexes for common queries"""
        # Compound index for time-series filtering
        await self.db.logs.create_index(
            [
                ("service", ASCENDING),
                ("timestamp", DESCENDING),
                ("level", ASCENDING)
            ],
            name="service_timestamp_level_idx"
        )
        
        # TTL index for automatic log expiration
        await self.db.logs.create_index(
            [
                ("timestamp", ASCENDING)
            ],
            expireAfterSeconds=60*60*24*30,  # 30 days
            name="ttl_timestamp_idx"
        )
        
        # Text index for full-text search
        await self.db.logs.create_index(
            [
                ("message", TEXT)
            ],
            name="text_message_idx"
        )

    async def get_db(self):
        """Get the database connection"""
        return self.db

    async def get_jobs_collection(self):
        """Get the jobs collection"""
        return self.db.jobs

# Initialize database connection
db = Database()
asyncio.run(db.create_indexes())