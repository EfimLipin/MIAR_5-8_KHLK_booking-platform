from sqlalchemy.orm import Session
from app.models import Tour, TourStatus
import uuid

class TourRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, offset: int = 0, count: int = 20, country: str = None):
        query = self.db.query(Tour)
        if country:
            query = query.filter(Tour.country == country)
        total = query.count()
        items = query.offset(offset).limit(count).all()
        return items, total

    def get_by_id(self, tour_id: uuid.UUID):
        return self.db.query(Tour).filter(Tour.id == tour_id).first()

    def create(self, tour: Tour):
        self.db.add(tour)
        self.db.commit()
        self.db.refresh(tour)
        return tour

    def update(self, tour: Tour):
        self.db.commit()
        self.db.refresh(tour)
        return tour

    def delete(self, tour: Tour):
        self.db.delete(tour)
        self.db.commit()

    def publish(self, tour: Tour):
        tour.status = TourStatus.PUBLISHED
        self.db.commit()
        self.db.refresh(tour)
        return tour