from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
import jwt
from app.core.security import decode_access_token
from app.models.schemas import TripListResponse, TripResponse, ReviewCreate, ReviewResponse, RatingResponse, BookingEligibilityResponse
from app.repositories.trip_repository import TripRepository
from app.services.trip_service import TripService
from app.services.booking_client import BookingClient

router = APIRouter(prefix="/api/v1", tags=["Trip and Reviews"])


def current_identity(authorization: str | None = Header(default=None)) -> tuple[str, str]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Требуется заголовок Authorization: Bearer.")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        return decode_access_token(token), authorization
    except (jwt.PyJWTError, ValueError, TypeError) as exc:
        raise HTTPException(401, "Токен отсутствует, просрочен или недействителен.") from exc


def get_service(request: Request) -> TripService:
    return TripService(TripRepository(request.app.state.mongo.database), request.app.state.publisher)


@router.get("/trips", response_model=TripListResponse)
async def list_trips(status: str | None = None, offset: int = Query(0, ge=0), count: int = Query(20, ge=1, le=100),
                     identity: tuple[str, str] = Depends(current_identity), service: TripService = Depends(get_service)):
    if status is not None and status not in {"planned", "active", "completed", "cancelled"}:
        raise HTTPException(400, "Недопустимое значение status.")
    return await service.list_trips(identity[0], status, offset, count)


@router.get("/trips/{trip_id}", response_model=TripResponse)
async def get_trip(trip_id: UUID, identity: tuple[str, str] = Depends(current_identity), service: TripService = Depends(get_service)):
    return await service.get_trip(str(trip_id), identity[0])


@router.post("/trips/{trip_id}/reviews", response_model=ReviewResponse, status_code=201)
async def create_review(trip_id: UUID, data: ReviewCreate, request: Request,
                        identity: tuple[str, str] = Depends(current_identity), service: TripService = Depends(get_service)):
    customer_id, authorization = identity
    trip = await service.get_trip(str(trip_id), customer_id)
    if trip["status"] != "completed":
        raise HTTPException(409, "Отзыв можно оставить только после завершения поездки.")
    booking = await BookingClient().check_review_eligibility(trip["booking_id"], authorization)
    if booking.get("review_allowed") is not True:
        raise HTTPException(409, f"Сервис «Бронирование» запретил публикацию отзыва: {booking.get('reason') or 'review_not_allowed'}.")
    if (booking["booking_id"] != trip["booking_id"] or booking["customer_id"] != customer_id
            or booking["trip_id"] != trip["trip_id"] or booking["tour_id"] != trip["tour_id"]):
        raise HTTPException(409, "Данные проверки бронирования не совпадают с поездкой.")
    return await service.create_review(trip, customer_id, data.rating, data.text, request.headers.get("X-Request-ID"))


@router.get("/reviews/{review_id}", response_model=ReviewResponse)
async def get_review(review_id: UUID, identity: tuple[str, str] = Depends(current_identity), service: TripService = Depends(get_service)):
    return await service.get_review(str(review_id), identity[0])


@router.get("/tours/{tour_id}/rating", response_model=RatingResponse)
async def get_tour_rating(tour_id: UUID, service: TripService = Depends(get_service)):
    return await service.get_rating(str(tour_id))
