from pymongo import AsyncMongoClient, ASCENDING
from app.core.config import settings


class MongoContext:
    def __init__(self) -> None:
        self.client = AsyncMongoClient(settings.mongodb_url, serverSelectionTimeoutMS=5000, tz_aware=True)
        self.database = self.client[settings.mongodb_database]

    async def connect(self) -> None:
        await self.client.admin.command("ping")
        await self.database.trips.create_index([("booking_id", ASCENDING)], unique=True)
        await self.database.reviews.create_index([("trip_id", ASCENDING)], unique=True)
        await self.database.reviews.create_index([("tour_id", ASCENDING)])
        await self.database.outbox.create_index([("published", ASCENDING), ("created_at", ASCENDING)])

    async def close(self) -> None:
        await self.client.close()
