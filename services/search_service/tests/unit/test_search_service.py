import pytest
from app.models.search import TourSummary
from app.services.search_service import SearchService

class FakeSearchRepo:
    def __init__(self):
        self.searches = {}
        self.favorites = {}
    def save_search(self, q):
        self.searches[q.id] = q
        return q
    def get_search(self, qid):
        return self.searches.get(qid)
    def add_favorite(self, f):
        self.favorites[f.id] = f
        return f
    def get_favorites(self, user_id):
        return [f for f in self.favorites.values() if f.user_id == user_id]
    def remove_favorite(self, fid):
        return self.favorites.pop(fid, None) is not None

def test_search_returns_catalog_results(monkeypatch):
    service = SearchService(repo=FakeSearchRepo())
    monkeypatch.setattr(service, "_fetch_tours",
        lambda params: [TourSummary(tour_id="t1", name="Тур", destination="Париж", price=100.0)])
    q = service.search_tours(user_id="u1", destination="Париж",
                             date_from=None, date_to=None, max_price=None)
    assert q.results[0].tour_id == "t1"
    assert service.get_search(q.id) is q

def test_search_when_catalog_unavailable(monkeypatch):
    service = SearchService(repo=FakeSearchRepo())
    def boom(params):
        raise Exception("no catalog")
    monkeypatch.setattr(service, "_fetch_tours", boom)
    q = service.search_tours(user_id="u1", destination=None,
                             date_from=None, date_to=None, max_price=None)
    assert q.results == []