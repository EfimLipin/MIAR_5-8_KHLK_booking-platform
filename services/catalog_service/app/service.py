from app.repository import TourRepository
from app.models import Tour, TourStatus
import uuid

class TourService:
    def __init__(self, repo: TourRepository):
        self.repo = repo

    def get_tours(self, offset, count, country):
        return self.repo.get_all(offset, count, country)

    def get_tour(self, tour_id: uuid.UUID):
        tour = self.repo.get_by_id(tour_id)
        if not tour:
            raise KeyError("Tour not found")
        return tour

    def create_tour(self, name: str, description: str, country: str, price: int):
        tour = Tour(
            name=name,
            description=description,
            country=country,
            price=price,
            status=TourStatus.DRAFT
        )
        return self.repo.create(tour)

    def update_tour(self, tour_id: uuid.UUID, data: dict):
        tour = self.repo.get_by_id(tour_id)
        if not tour:
            raise KeyError("Tour not found")
        for key, value in data.items():
            if hasattr(tour, key):
                setattr(tour, key, value)
        return self.repo.update(tour)

    def delete_tour(self, tour_id: uuid.UUID):
        tour = self.repo.get_by_id(tour_id)
        if not tour:
            raise KeyError("Tour not found")
        self.repo.delete(tour)

    def publish_tour(self, tour_id: uuid.UUID):
        tour = self.repo.get_by_id(tour_id)
        if not tour:
            raise KeyError("Tour not found")
        if tour.status == TourStatus.PUBLISHED:
            raise ValueError("Tour already published")
        if not tour.name or not tour.country or not tour.price:
            raise ValueError("Tour is not ready for publication")
        return self.repo.publish(tour)