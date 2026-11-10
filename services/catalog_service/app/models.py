from sqlalchemy import Column, String, Integer, DateTime, Enum, Uuid
from datetime import datetime
import enum
import uuid
from app.database import Base

class TourStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"

class Tour(Base):
    __tablename__ = "tours"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    country = Column(String, nullable=False)
    price = Column(Integer, nullable=False)
    status = Column(Enum(TourStatus), nullable=False, default=TourStatus.DRAFT)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)