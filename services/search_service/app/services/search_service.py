from uuid import UUID
import httpx
from app.models.search import SearchQuery, Favorite, TourSummary
from app.repos.mongo_search_repo import SearchRepo
from app.settings import settings

class SearchService:
    def __init__(self, repo: SearchRepo = None):
        self.repo = repo or SearchRepo(settings.mongo_url)

    def _fetch_tours(self, params: dict) -> list[TourSummary]:
        # Синхронный вызов сервиса «Каталог туров» (студент Котельников)
        with httpx.Client(timeout=5) as client:
            resp = client.get(
                f"{settings.catalog_service_url}/api/catalog/tours", params=params)
            resp.raise_for_status()
            return [TourSummary(**t) for t in resp.json()]

    def search_tours(self, user_id: str, destination: str | None,
                     date_from, date_to, max_price) -> SearchQuery:
        query = SearchQuery(user_id=user_id, destination=destination,
                            date_from=date_from, date_to=date_to,
                            max_price=max_price)
        params = {}
        if destination:
            params["destination"] = destination
        if max_price is not None:
            params["max_price"] = max_price
        try:
            query.results = self._fetch_tours(params)
        except Exception:
            query.results = []   # каталог временно недоступен
        return self.repo.save_search(query)

    def get_search(self, query_id: UUID) -> SearchQuery | None:
        return self.repo.get_search(query_id)

    def add_favorite(self, user_id: str, tour_id: str) -> Favorite:
        return self.repo.add_favorite(Favorite(user_id=user_id, tour_id=tour_id))

    def get_favorites(self, user_id: str) -> list[Favorite]:
        return self.repo.get_favorites(user_id)

    def remove_favorite(self, fav_id: UUID) -> bool:
        return self.repo.remove_favorite(fav_id)