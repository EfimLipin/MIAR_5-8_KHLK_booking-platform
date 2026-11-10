from __future__ import annotations
from datetime import date, datetime, timezone
from uuid import UUID, uuid4, uuid5, NAMESPACE_URL
from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError
from app.repositories.trip_repository import TripRepository


class TripService:
    def __init__(self, repo: TripRepository, publisher):
        self.repo = repo
        self.publisher = publisher

    async def list_trips(self, customer_id: str, status: str | None, offset: int, count: int):
        rows, total = await self.repo.list_trips(customer_id, status, offset, count)
        return {"items": rows, "offset": offset, "count": count, "total": total}

    async def get_trip(self, trip_id: str, customer_id: str):
        trip = await self.repo.get_trip(trip_id)
        if trip is None:
            raise HTTPException(404, "Поездка не найдена.")
        if trip["customer_id"] != customer_id:
            raise HTTPException(403, "Поездка принадлежит другому клиенту.")
        return trip

    async def create_review(self, trip: dict, customer_id: str, rating: int, text: str, correlation_id: str):
        if trip["status"] != "completed":
            raise HTTPException(409, "Отзыв можно оставить только после завершения поездки.")
        review = {
            "review_id": str(uuid4()), "trip_id": trip["trip_id"], "booking_id": trip["booking_id"],
            "customer_id": customer_id, "tour_id": trip["tour_id"], "rating": rating,
            "text": text, "created_at": datetime.now(timezone.utc),
        }
        try:
            await self.repo.create_review(review)
        except DuplicateKeyError as exc:
            raise HTTPException(409, "Для данной поездки отзыв уже создан.") from exc
        await self.publisher.publish("review.created", review["review_id"], {
            "review_id": review["review_id"], "trip_id": review["trip_id"], "tour_id": review["tour_id"],
            "customer_id": review["customer_id"], "rating": review["rating"], "created_at": review["created_at"].isoformat(),
        }, correlation_id=correlation_id)
        aggregate = await self.repo.recalculate_rating(trip["tour_id"])
        await self.publisher.publish("tour.rating.updated", trip["tour_id"], {
            "tour_id": trip["tour_id"], "rating_average": aggregate["rating_average"],
            "reviews_count": aggregate["reviews_count"], "calculated_at": aggregate["calculated_at"].isoformat(),
        }, correlation_id=correlation_id)
        return review

    async def handle_event(self, event_type: str, payload: dict):
        if event_type == "booking.confirmed":
            required = ("booking_id", "customer_id", "tour_id", "start_date", "end_date", "travellers_count")
            if any(key not in payload for key in required):
                raise ValueError("booking.confirmed: отсутствует обязательное поле")
            booking_id = str(UUID(str(payload["booking_id"])))
            customer_id = str(UUID(str(payload["customer_id"])))
            tour_id = str(UUID(str(payload["tour_id"])))
            trip_id = str(uuid5(NAMESPACE_URL, f"booking:{booking_id}"))
            start = date.fromisoformat(payload["start_date"])
            end = date.fromisoformat(payload["end_date"])
            travellers_count = payload["travellers_count"]
            if isinstance(travellers_count, bool) or not isinstance(travellers_count, int) or travellers_count < 1:
                raise ValueError("booking.confirmed: travellers_count должен быть целым числом не меньше 1")
            if end < start:
                raise ValueError("booking.confirmed: end_date раньше start_date")
            today = date.today()
            status = "active" if start <= today else "planned"
            trip = {"trip_id": trip_id, "booking_id": booking_id, "customer_id": customer_id,
                    "tour_id": tour_id, "status": status, "start_date": start.isoformat(),
                    "end_date": end.isoformat(), "completed_at": None, "cancelled_at": None,
                    "reason_code": None, "document_set_id": None, "ready_at": None,
                    "travellers_count": travellers_count}
            await self.repo.upsert_confirmed_trip(trip)
        elif event_type == "booking.cancelled":
            booking_id = str(UUID(str(payload["booking_id"])))
            cancelled_at = payload.get("cancelled_at", datetime.now(timezone.utc).isoformat())
            await self.repo.update_trip_by_booking(booking_id, {
                "status": "cancelled", "cancelled_at": cancelled_at,
                "reason_code": payload.get("reason_code")})
        elif event_type == "documents.ready":
            booking_id = str(UUID(str(payload["booking_id"])))
            document_set_id = str(UUID(str(payload["document_set_id"])))
            ready_at = payload.get("ready_at")
            if not ready_at:
                raise ValueError("documents.ready: отсутствует ready_at")
            await self.repo.update_trip_by_booking(booking_id, {
                "document_set_id": document_set_id, "ready_at": ready_at})
        elif event_type == "customer.profile.updated":
            customer_id = str(UUID(str(payload["customer_id"])))
            profile_version = payload.get("profile_version")
            if isinstance(profile_version, bool) or not isinstance(profile_version, int) or profile_version < 1:
                raise ValueError("customer.profile.updated: некорректный profile_version")
            updated_at = payload.get("updated_at")
            if not updated_at:
                raise ValueError("customer.profile.updated: отсутствует updated_at")
            await self.repo.update_customer_projection(customer_id, profile_version,
                list(payload.get("changed_fields", [])), updated_at)
        else:
            raise ValueError(f"Неподдерживаемое событие: {event_type}")

    async def complete_due_trips(self, on_date: date | None = None):
        current_date = on_date or date.today()
        due = await self.repo.due_trips(current_date)
        completed = []
        for trip in due:
            completed_at = datetime.now(timezone.utc)
            updated = await self.repo.mark_completed(trip["trip_id"], completed_at)
            if updated is None:
                continue
            payload = {"trip_id": updated["trip_id"], "booking_id": updated["booking_id"],
                       "customer_id": updated["customer_id"], "tour_id": updated["tour_id"],
                       "completed_at": completed_at.isoformat()}
            await self.publisher.publish("trip.completed", updated["trip_id"], payload)
            completed.append(updated["trip_id"])
        return completed

    async def get_review(self, review_id: str, customer_id: str):
        review = await self.repo.get_review(review_id)
        if review is None:
            raise HTTPException(404, "Отзыв не найден.")
        if review["customer_id"] != customer_id:
            raise HTTPException(403, "Отзыв принадлежит другому клиенту.")
        return review

    async def get_rating(self, tour_id: str):
        rating = await self.repo.get_rating(tour_id)
        if rating is None:
            return {"tour_id": tour_id, "rating_average": 0.0, "reviews_count": 0,
                    "calculated_at": datetime.now(timezone.utc)}
        return rating
