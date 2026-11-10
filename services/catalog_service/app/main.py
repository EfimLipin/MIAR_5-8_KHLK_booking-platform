from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db, engine, Base
from app.repository import TourRepository
from app.service import TourService
from app.models import Tour
from app.rabbitmq import publish_event, start_consumer
import uuid
import asyncio

app = FastAPI(title="Catalog Service")

# Создаём таблицы при старте (для простоты)
Base.metadata.create_all(bind=engine)

def get_service(db: Session = Depends(get_db)):
    return TourService(TourRepository(db))

@app.get("/tours")
def get_tours(
    offset: int = Query(0, ge=0),
    count: int = Query(20, ge=1, le=100),
    country: str = Query(None),
    service: TourService = Depends(get_service)
):
    items, total = service.get_tours(offset, count, country)
    return {
        "items": [
            {
                "id": str(t.id),
                "name": t.name,
                "country": t.country,
                "price": t.price,
                "status": t.status.value,
                "created_at": t.created_at.isoformat()
            }
            for t in items
        ],
        "total": total,
        "offset": offset,
        "count": count
    }

@app.get("/tours/{tour_id}")
def get_tour(tour_id: uuid.UUID, service: TourService = Depends(get_service)):
    try:
        tour = service.get_tour(tour_id)
        return {
            "id": str(tour.id),
            "name": tour.name,
            "description": tour.description,
            "country": tour.country,
            "price": tour.price,
            "status": tour.status.value,
            "created_at": tour.created_at.isoformat(),
            "updated_at": tour.updated_at.isoformat()
        }
    except KeyError:
        raise HTTPException(404, "Tour not found")

@app.post("/tours", status_code=201)
async def create_tour(
    name: str,
    description: str = None,
    country: str = None,
    price: int = None,
    service: TourService = Depends(get_service)
):
    if not name or not country or not price:
        raise HTTPException(400, "name, country and price are required")
    tour = service.create_tour(name, description, country, price)
    await publish_event("tour.created", {"tour_id": str(tour.id), "name": tour.name})
    return {
        "id": str(tour.id),
        "name": tour.name,
        "description": tour.description,
        "country": tour.country,
        "price": tour.price,
        "status": tour.status.value,
        "created_at": tour.created_at.isoformat()
    }

@app.put("/tours/{tour_id}")
def update_tour(
    tour_id: uuid.UUID,
    name: str = None,
    description: str = None,
    country: str = None,
    price: int = None,
    service: TourService = Depends(get_service)
):
    data = {k: v for k, v in {"name": name, "description": description, "country": country, "price": price}.items() if v is not None}
    try:
        tour = service.update_tour(tour_id, data)
        return {
            "id": str(tour.id),
            "name": tour.name,
            "description": tour.description,
            "country": tour.country,
            "price": tour.price,
            "status": tour.status.value,
            "updated_at": tour.updated_at.isoformat()
        }
    except KeyError:
        raise HTTPException(404, "Tour not found")

@app.delete("/tours/{tour_id}", status_code=204)
def delete_tour(tour_id: uuid.UUID, service: TourService = Depends(get_service)):
    try:
        service.delete_tour(tour_id)
    except KeyError:
        raise HTTPException(404, "Tour not found")

@app.post("/tours/{tour_id}:publish")
async def publish_tour(tour_id: uuid.UUID, service: TourService = Depends(get_service)):
    try:
        tour = service.publish_tour(tour_id)
        await publish_event("tour.published", {"tour_id": str(tour.id), "name": tour.name})
        return {
            "id": str(tour.id),
            "name": tour.name,
            "status": tour.status.value
        }
    except KeyError:
        raise HTTPException(404, "Tour not found")
    except ValueError as e:
        raise HTTPException(409, str(e))

@app.on_event("startup")
async def startup():
    asyncio.create_task(start_consumer())