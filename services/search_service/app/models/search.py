from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field

class TourSummary(BaseModel):
    tour_id: str
    name: str
    destination: str
    price: float

class SearchQuery(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    user_id: str
    destination: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    max_price: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    results: list[TourSummary] = Field(default_factory=list)

class Favorite(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    user_id: str
    tour_id: str
    added_at: datetime = Field(default_factory=datetime.utcnow)

class SearchRequest(BaseModel):
    user_id: str
    destination: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    max_price: Optional[float] = None

class FavoriteRequest(BaseModel):
    user_id: str
    tour_id: str