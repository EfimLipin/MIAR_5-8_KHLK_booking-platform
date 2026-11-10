import pytest
from unittest.mock import Mock
from uuid import uuid4
from app.models import PartnerRequest, RequestStatus
from app.service import PartnerService
from app.database import Base
from app.repository import PartnerRequestRepository
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# --- Unit-тесты ---
def test_confirm_wrong_status():
    repo = Mock()
    req = PartnerRequest(id=uuid4(), tour_id=uuid4(), booking_id=uuid4(), client_id=uuid4(), status=RequestStatus.CONFIRMED)
    repo.get_by_id.return_value = req
    service = PartnerService(repo)
    with pytest.raises(ValueError, match="Request already processed"):
        service.confirm_request(req.id)

# --- Интеграционные тесты (с БД в памяти) ---
@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_create_request_db(db_session):
    repo = PartnerRequestRepository(db_session)
    req = PartnerRequest(tour_id=uuid4(), booking_id=uuid4(), client_id=uuid4(), status=RequestStatus.SENT)
    created = repo.create(req)
    assert created.id is not None
    assert created.status == RequestStatus.SENT