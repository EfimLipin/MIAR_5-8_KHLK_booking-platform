from uuid import UUID
from sqlalchemy.orm import Session
from app.schemas.document import DocumentSetDB
from app.models.document import DocumentSet

class DocumentRepo:
    def __init__(self, db: Session):
        self.db = db

    def create(self, doc: DocumentSet) -> DocumentSet:
        row = DocumentSetDB(
            id=doc.id, booking_id=doc.booking_id, user_id=doc.user_id,
            tour_id=doc.tour_id, status=doc.status,
            contract_signed=doc.contract_signed, visa_issued=doc.visa_issued,
            insurance_issued=doc.insurance_issued,
            voucher_generated=doc.voucher_generated, created_at=doc.created_at)
        self.db.add(row)
        self.db.commit()
        return doc

    def get_by_id(self, doc_id: UUID) -> DocumentSet | None:
        row = self.db.query(DocumentSetDB).filter(DocumentSetDB.id == doc_id).first()
        return self._to_model(row) if row else None

    def get_by_user(self, user_id: str) -> list[DocumentSet]:
        rows = self.db.query(DocumentSetDB).filter(DocumentSetDB.user_id == user_id).all()
        return [self._to_model(r) for r in rows]

    def get_by_booking_id(self, booking_id: str) -> DocumentSet | None:
        row = self.db.query(DocumentSetDB).filter(DocumentSetDB.booking_id == booking_id).first()
        return self._to_model(row) if row else None

    def update(self, doc: DocumentSet) -> DocumentSet:
        row = self.db.query(DocumentSetDB).filter(DocumentSetDB.id == doc.id).first()
        if row is None:
            raise KeyError(doc.id)
        row.status = doc.status
        row.contract_signed = doc.contract_signed
        row.visa_issued = doc.visa_issued
        row.insurance_issued = doc.insurance_issued
        row.voucher_generated = doc.voucher_generated
        self.db.commit()
        return doc

    def _to_model(self, row: DocumentSetDB) -> DocumentSet:
        return DocumentSet(
            id=row.id, booking_id=row.booking_id, user_id=row.user_id,
            tour_id=row.tour_id, status=row.status,
            contract_signed=row.contract_signed, visa_issued=row.visa_issued,
            insurance_issued=row.insurance_issued,
            voucher_generated=row.voucher_generated, created_at=row.created_at)