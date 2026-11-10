from uuid import UUID
from pymongo import MongoClient
from app.models.search import SearchQuery, Favorite

class SearchRepo:
    def __init__(self, mongo_url: str, db_name: str = "search_service"):
        self.client = MongoClient(mongo_url)
        self.db = self.client[db_name]
        self.search_collection = self.db["search_queries"]
        self.favorites_collection = self.db["favorites"]

    def save_search(self, query: SearchQuery) -> SearchQuery:
        self.search_collection.replace_one(
            {"id": str(query.id)}, query.model_dump(mode="json"), upsert=True)
        return query

    def get_search(self, query_id: UUID) -> SearchQuery | None:
        doc = self.search_collection.find_one({"id": str(query_id)})
        return SearchQuery.model_validate(doc) if doc else None

    def add_favorite(self, fav: Favorite) -> Favorite:
        self.favorites_collection.replace_one(
            {"id": str(fav.id)}, fav.model_dump(mode="json"), upsert=True)
        return fav

    def get_favorites(self, user_id: str) -> list[Favorite]:
        return [Favorite.model_validate(d)
                for d in self.favorites_collection.find({"user_id": user_id})]

    def remove_favorite(self, fav_id: UUID) -> bool:
        return self.favorites_collection.delete_one({"id": str(fav_id)}).deleted_count > 0