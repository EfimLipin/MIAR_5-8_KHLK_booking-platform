from sqlalchemy.orm import Session
from app.models import PartnerRequest, RequestStatus
import uuid

class PartnerRequestRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, request: PartnerRequest):
        self.db.add(request)
        self.db.commit()
        self.db.refresh(request)
        return request

    def get_by_id(self, request_id: uuid.UUID):
        return self.db.query(PartnerRequest).filter(PartnerRequest.id == request_id).first()

    def get_all(self, offset: int = 0, count: int = 20, status: str = None):
        query = self.db.query(PartnerRequest)
        if status:
            query = query.filter(PartnerRequest.status == status)
        total = query.count()
        items = query.offset(offset).limit(count).all()
        return items, total

    def confirm(self, request: PartnerRequest):
        request.status = RequestStatus.CONFIRMED
        self.db.commit()
        self.db.refresh(request)
        return request

    def cancel(self, request: PartnerRequest):
        request.status = RequestStatus.CANCELLED
        self.db.commit()
        self.db.refresh(request)
        return request