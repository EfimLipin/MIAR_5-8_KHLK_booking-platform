from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db, engine, Base
from app.repository import PartnerRequestRepository
from app.service import PartnerService
from app.rabbitmq import publish_event, start_consumer
import uuid
import asyncio

app = FastAPI(title="Partner Service")
Base.metadata.create_all(bind=engine)

def get_service(db: Session = Depends(get_db)):
    return PartnerService(PartnerRequestRepository(db))

@app.post("/partner-requests", status_code=201)
async def create_request(
    tour_id: uuid.UUID,
    booking_id: uuid.UUID,
    client_id: uuid.UUID,
    comment: str = None,
    service: PartnerService = Depends(get_service)
):
    try:
        req = await service.create_request(tour_id, booking_id, client_id, comment)
        await publish_event("partner.request.sent", {"request_id": str(req.id), "tour_id": str(req.tour_id)})
        return {
            "id": str(req.id),
            "tour_id": str(req.tour_id),
            "booking_id": str(req.booking_id),
            "client_id": str(req.client_id),
            "status": req.status.value,
            "comment": req.comment,
            "created_at": req.created_at.isoformat()
        }
    except KeyError as e:
        raise HTTPException(404, str(e))
    except ValueError as e:
        raise HTTPException(409, str(e))

@app.get("/partner-requests")
def get_requests(
    offset: int = Query(0, ge=0),
    count: int = Query(20, ge=1, le=100),
    status: str = Query(None),
    service: PartnerService = Depends(get_service)
):
    items, total = service.get_requests(offset, count, status)
    return {
        "items": [
            {
                "id": str(r.id),
                "tour_id": str(r.tour_id),
                "booking_id": str(r.booking_id),
                "client_id": str(r.client_id),
                "status": r.status.value,
                "created_at": r.created_at.isoformat()
            }
            for r in items
        ],
        "total": total,
        "offset": offset,
        "count": count
    }

@app.get("/partner-requests/{request_id}")
def get_request(request_id: uuid.UUID, service: PartnerService = Depends(get_service)):
    try:
        req = service.get_request(request_id)
        return {
            "id": str(req.id),
            "tour_id": str(req.tour_id),
            "booking_id": str(req.booking_id),
            "client_id": str(req.client_id),
            "status": req.status.value,
            "comment": req.comment,
            "created_at": req.created_at.isoformat()
        }
    except KeyError:
        raise HTTPException(404, "Request not found")

@app.post("/partner-requests/{request_id}:confirm")
async def confirm_request(request_id: uuid.UUID, service: PartnerService = Depends(get_service)):
    try:
        req = service.confirm_request(request_id)
        await publish_event("partner.request.confirmed", {"request_id": str(req.id), "booking_id": str(req.booking_id)})
        return {"id": str(req.id), "status": req.status.value}
    except KeyError:
        raise HTTPException(404, "Request not found")
    except ValueError as e:
        raise HTTPException(409, str(e))

@app.post("/partner-requests/{request_id}:cancel")
async def cancel_request(request_id: uuid.UUID, service: PartnerService = Depends(get_service)):
    try:
        req = service.cancel_request(request_id)
        await publish_event("partner.request.cancelled", {"request_id": str(req.id), "booking_id": str(req.booking_id)})
        return {"id": str(req.id), "status": req.status.value}
    except KeyError:
        raise HTTPException(404, "Request not found")
    except ValueError as e:
        raise HTTPException(409, str(e))

@app.on_event("startup")
async def startup():
    asyncio.create_task(start_consumer())