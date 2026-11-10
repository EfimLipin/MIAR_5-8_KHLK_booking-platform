from sqlalchemy import Column, String, DateTime, Enum, Uuid
from datetime import datetime
import enum
import uuid
from app.database import Base

class RequestStatus(str, enum.Enum):
    SENT = "sent"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"

class PartnerRequest(Base):
    __tablename__ = "partner_requests"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tour_id = Column(Uuid(as_uuid=True), nullable=False)
    booking_id = Column(Uuid(as_uuid=True), nullable=False)
    client_id = Column(Uuid(as_uuid=True), nullable=False)
    comment = Column(String, nullable=True)
    status = Column(Enum(RequestStatus), nullable=False, default=RequestStatus.SENT)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)