import pytest
from unittest.mock import Mock
from uuid import uuid4
from app.models import Tour, TourStatus
from app.service import TourService
from app.database import Base
from app.repository import TourRepository
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# --- Unit-тесты ---
def test_publish_tour_already_published():
    repo = Mock()
    tour = Tour(id=uuid4(), name="Test", country="Russia", price=1000, status=TourStatus.PUBLISHED)
    repo.get_by_id.return_value = tour
    service = TourService(repo)
    with pytest.raises(ValueError, match="Tour already published"):
        service.publish_tour(tour.id)

def test_create_tour_calls_repo():
    repo = Mock()
    service = TourService(repo)
    service.create_tour("Name", "Desc", "Country", 100)
    repo.create.assert_called_once()

# --- Интеграционные тесты (с БД в памяти) ---
@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_create_and_get_tour_db(db_session):
    repo = TourRepository(db_session)
    tour = Tour(name="Test", country="Russia", price=1000)
    created = repo.create(tour)
    found = repo.get_by_id(created.id)
    assert found.name == "Test"
    assert found.country == "Russia"