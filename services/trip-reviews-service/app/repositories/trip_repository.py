from datetime import date, datetime, timezone
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError


class TripRepository:
    def __init__(self, database):
        self.db = database
        self.trips = database.trips
        self.reviews = database.reviews
        self.ratings = database.ratings
        self.customers = database.customer_profiles
        self.processed = database.processed_messages
        self.outbox = database.outbox

    async def list_trips(self, customer_id: str, status: str | None, offset: int, count: int):
        query = {"customer_id": customer_id}
        if status:
            query["status"] = status
        total = await self.trips.count_documents(query)
        rows = await self.trips.find(query, {"_id": 0}).sort("start_date", -1).skip(offset).limit(count).to_list(length=count)
        return rows, total

    async def get_trip(self, trip_id: str):
        return await self.trips.find_one({"trip_id": trip_id}, {"_id": 0})

    async def get_trip_by_booking(self, booking_id: str):
        return await self.trips.find_one({"booking_id": booking_id}, {"_id": 0})

    async def upsert_confirmed_trip(self, trip: dict):
        return await self.trips.find_one_and_update(
            {"booking_id": trip["booking_id"]}, {"$setOnInsert": trip},
            upsert=True, return_document=ReturnDocument.AFTER, projection={"_id": 0}
        )

    async def update_trip_by_booking(self, booking_id: str, updates: dict):
        return await self.trips.find_one_and_update(
            {"booking_id": booking_id}, {"$set": updates},
            return_document=ReturnDocument.AFTER, projection={"_id": 0}
        )

    async def create_review(self, review: dict):
        await self.reviews.insert_one(review)
        return review

    async def get_review(self, review_id: str):
        return await self.reviews.find_one({"review_id": review_id}, {"_id": 0})

    async def get_rating(self, tour_id: str):
        return await self.ratings.find_one({"tour_id": tour_id}, {"_id": 0})

    async def recalculate_rating(self, tour_id: str):
        pipeline = [{"$match": {"tour_id": tour_id}},
                    {"$group": {"_id": "$tour_id", "rating_average": {"$avg": "$rating"}, "reviews_count": {"$sum": 1}}}]
        rows = await self.reviews.aggregate(pipeline).to_list(length=1)
        if not rows:
            return None
        rating = {"tour_id": tour_id, "rating_average": round(float(rows[0]["rating_average"]), 2),
                  "reviews_count": int(rows[0]["reviews_count"]), "calculated_at": datetime.now(timezone.utc)}
        await self.ratings.update_one({"tour_id": tour_id}, {"$set": rating}, upsert=True)
        return rating

    async def is_message_processed(self, message_id: str) -> bool:
        return await self.processed.find_one({"_id": message_id}, {"_id": 1}) is not None

    async def mark_message_processed(self, message_id: str, event_type: str):
        await self.processed.insert_one({"_id": message_id, "event_type": event_type, "processed_at": datetime.now(timezone.utc)})

    async def update_customer_projection(self, customer_id: str, profile_version: int, changed_fields: list[str], updated_at: str):
        await self.customers.update_one({"customer_id": customer_id},
            {"$set": {"customer_id": customer_id, "profile_version": profile_version,
                       "changed_fields": changed_fields, "updated_at": updated_at}}, upsert=True)

    async def due_trips(self, on_date: date):
        cursor = self.trips.find({"status": {"$in": ["planned", "active"]}, "end_date": {"$lt": on_date.isoformat()}}, {"_id": 0})
        return await cursor.to_list(length=500)

    async def mark_completed(self, trip_id: str, completed_at: datetime):
        return await self.trips.find_one_and_update(
            {"trip_id": trip_id, "status": {"$in": ["planned", "active"]}},
            {"$set": {"status": "completed", "completed_at": completed_at}},
            return_document=ReturnDocument.AFTER, projection={"_id": 0}
        )
