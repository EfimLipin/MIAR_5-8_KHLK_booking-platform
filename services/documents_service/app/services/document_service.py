from uuid import UUID
from sqlalchemy.orm import Session
from app.models.document import DocumentSet, DocumentStatus
from app.repos.db_document_repo import DocumentRepo

class DocumentService:
    def __init__(self, db: Session = None, repo: DocumentRepo = None):
        self.repo = repo or DocumentRepo(db)

    def create_set(self, booking_id: str, user_id: str, tour_id: str) -> DocumentSet:
        # виза, страховка и ваучер формируются автоматически; договор требует подписи
        doc = DocumentSet(booking_id=booking_id, user_id=user_id, tour_id=tour_id,
                          visa_issued=True, insurance_issued=True,
                          voucher_generated=True)
        return self.repo.create(doc)

    def get_set(self, doc_id: UUID) -> DocumentSet | None:
        return self.repo.get_by_id(doc_id)

    def list_sets(self, user_id: str) -> list[DocumentSet]:
        return self.repo.get_by_user(user_id)

    def sign_contract(self, doc_id: UUID) -> DocumentSet:
        doc = self.repo.get_by_id(doc_id)
        if doc is None:
            raise KeyError(doc_id)
        if doc.status == DocumentStatus.CANCELED:
            raise ValueError("Canceled document cannot be signed")
        doc.contract_signed = True
        doc.status = DocumentStatus.COMPLETED
        return self.repo.update(doc)

    def cancel_set(self, doc_id: UUID) -> DocumentSet:
        doc = self.repo.get_by_id(doc_id)
        if doc is None:
            raise KeyError(doc_id)
        doc.status = DocumentStatus.CANCELED
        return self.repo.update(doc)

    def cancel_by_booking(self, booking_id: str) -> DocumentSet | None:
        doc = self.repo.get_by_booking_id(booking_id)
        if doc is None:
            return None
        doc.status = DocumentStatus.CANCELED
        return self.repo.update(doc)