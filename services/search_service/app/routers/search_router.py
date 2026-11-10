from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.services.search_service import SearchService
from app.models.search import SearchQuery, Favorite, SearchRequest, FavoriteRequest

router = APIRouter(prefix="/api", tags=["search"])

def get_search_service() -> SearchService:
    return SearchService()

@router.post("/search", response_model=SearchQuery)
def create_search(req: SearchRequest, service: SearchService = Depends(get_search_service)):
    return service.search_tours(req.user_id, req.destination,
                                req.date_from, req.date_to, req.max_price)

@router.get("/search/{query_id}", response_model=SearchQuery)
def get_search(query_id: UUID, service: SearchService = Depends(get_search_service)):
    q = service.get_search(query_id)
    if not q:
        raise HTTPException(404, "Search query not found")
    return q

@router.post("/favorites", response_model=Favorite)
def add_favorite(req: FavoriteRequest, service: SearchService = Depends(get_search_service)):
    return service.add_favorite(req.user_id, req.tour_id)

@router.get("/favorites", response_model=list[Favorite])
def get_favorites(user_id: str, service: SearchService = Depends(get_search_service)):
    return service.get_favorites(user_id)

@router.delete("/favorites/{favorite_id}")
def delete_favorite(favorite_id: UUID, service: SearchService = Depends(get_search_service)):
    if not service.remove_favorite(favorite_id):
        raise HTTPException(404, "Favorite not found")
    return {"status": "deleted"}