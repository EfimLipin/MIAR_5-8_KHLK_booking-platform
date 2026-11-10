import enum
from datetime import datetime
from uuid import UUID, uuid4
from pydantic import BaseModel, Field

class DocumentStatus(enum.Enum):
    CREATED = "created"
    COMPLETED = "completed"
    CANCELED = "canceled"

class DocumentSet(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    booking_id: str
    user_id: str
    tour_id: str
    status: DocumentStatus = DocumentStatus.CREATED
    contract_signed: bool = False
    visa_issued: bool = False
    insurance_issued: bool = False
    voucher_generated: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CreateDocumentRequest(BaseModel):
    booking_id: str
    user_id: str
    tour_id: str