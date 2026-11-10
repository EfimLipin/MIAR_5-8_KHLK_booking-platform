import pytest
from pydantic import ValidationError
from app.models.document import DocumentSet, DocumentStatus
from app.services.document_service import DocumentService

class FakeRepo:
    def __init__(self):
        self.items = {}
    def create(self, doc):
        self.items[doc.id] = doc
        return doc
    def get_by_id(self, doc_id):
        return self.items.get(doc_id)
    def get_by_user(self, user_id):
        return [d for d in self.items.values() if d.user_id == user_id]
    def get_by_booking_id(self, booking_id):
        for d in self.items.values():
            if d.booking_id == booking_id:
                return d
        return None
    def update(self, doc):
        self.items[doc.id] = doc
        return doc

@pytest.fixture()
def service():
    return DocumentService(repo=FakeRepo())

def test_create_document_set(service):
    doc = service.create_set("b1", "u1", "t1")
    assert doc.status == DocumentStatus.CREATED
    assert doc.visa_issued is True
    assert doc.insurance_issued is True
    assert doc.voucher_generated is True
    assert doc.contract_signed is False

def test_sign_contract(service):
    doc = service.create_set("b1", "u1", "t1")
    updated = service.sign_contract(doc.id)
    assert updated.contract_signed is True
    assert updated.status == DocumentStatus.COMPLETED

def test_cancel_by_booking(service):
    doc = service.create_set("b1", "u1", "t1")
    canceled = service.cancel_by_booking("b1")
    assert canceled.status == DocumentStatus.CANCELED

def test_document_booking_id_required():
    with pytest.raises(ValidationError):
        DocumentSet(user_id="u1", tour_id="t1")   # booking_id отсутствует