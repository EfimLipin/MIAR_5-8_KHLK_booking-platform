from sqlalchemy import Column, String, Boolean, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from app.schemas.base import Base
from app.models.document import DocumentStatus

class DocumentSetDB(Base):
    __tablename__ = "document_sets"
    id = Column(UUID(as_uuid=True), primary_key=True)
    booking_id = Column(String, nullable=False)
    user_id = Column(String, nullable=False)
    tour_id = Column(String, nullable=False)
    status = Column(Enum(DocumentStatus), nullable=False)
    contract_signed = Column(Boolean, default=False)
    visa_issued = Column(Boolean, default=False)
    insurance_issued = Column(Boolean, default=False)
    voucher_generated = Column(Boolean, default=False)
    created_at = Column(DateTime, nullable=False)