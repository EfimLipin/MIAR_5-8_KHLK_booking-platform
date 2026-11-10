from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    text: str = Field(min_length=1, max_length=5000)

    @field_validator("text")
    @classmethod
    def trim_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Текст отзыва не может быть пустым")
        return value


class TripResponse(BaseModel):
    trip_id: str
    booking_id: str
    customer_id: str
    tour_id: str
    status: str
    start_date: date
    end_date: date
    completed_at: datetime | None = None
    cancelled_at: datetime | None = None
    reason_code: str | None = None
    document_set_id: str | None = None
    ready_at: datetime | None = None
    travellers_count: int


class TripListResponse(BaseModel):
    items: list[TripResponse]
    offset: int
    count: int
    total: int


class ReviewResponse(BaseModel):
    review_id: str
    trip_id: str
    booking_id: str
    customer_id: str
    tour_id: str
    rating: int
    text: str
    created_at: datetime


class RatingResponse(BaseModel):
    tour_id: str
    rating_average: float
    reviews_count: int
    calculated_at: datetime


class BookingEligibilityResponse(BaseModel):
    review_allowed: bool
    booking_id: str
    customer_id: str
    trip_id: str
    tour_id: str
    booking_status: str
    trip_status: str
    reason: str | None = None
