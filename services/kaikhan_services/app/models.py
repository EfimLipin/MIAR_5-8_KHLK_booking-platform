from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, Field
from sqlalchemy import String, Numeric, DateTime, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase): pass
class Record(Base):
    __tablename__ = "records"
    __table_args__ = (UniqueConstraint("request_key"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    customer_id: Mapped[str] = mapped_column(String(36))
    reference_id: Mapped[str] = mapped_column(String(36))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    status: Mapped[str] = mapped_column(String(24))
    request_key: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class BookingInput(BaseModel):
    customer_id: UUID
    tour_id: UUID
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)

class PaymentInput(BaseModel):
    booking_id: UUID
    customer_id: UUID
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)

def serialize(row):
    return {"id": row.id, "customer_id": row.customer_id,
            "reference_id": row.reference_id, "amount": str(row.amount),
            "currency": "RUB", "status": row.status,
            "created_at": row.created_at.isoformat()}
