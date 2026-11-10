import httpx
from fastapi import HTTPException
from app.core.config import settings


class BookingClient:
    async def check_review_eligibility(self, booking_id: str, authorization: str) -> dict:
        url = f"{settings.booking_service_url.rstrip('/')}/api/v1/bookings/{booking_id}/review-eligibility"
        timeout = httpx.Timeout(settings.booking_timeout_seconds)
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url, headers={"Authorization": authorization, "Accept": "application/json"})
        except httpx.TimeoutException as exc:
            raise HTTPException(504, "Истекло время ожидания ответа сервиса «Бронирование».") from exc
        except httpx.RequestError as exc:
            raise HTTPException(503, "Сервис «Бронирование» временно недоступен.") from exc
        if response.status_code == 401:
            raise HTTPException(401, "Сервис «Бронирование» отклонил токен доступа.")
        if response.status_code == 403:
            raise HTTPException(403, "Сервис «Бронирование» запретил доступ к бронированию.")
        if response.status_code == 404:
            raise HTTPException(404, "Бронирование не найдено.")
        if response.status_code >= 500:
            raise HTTPException(503, "Сервис «Бронирование» вернул временную серверную ошибку.")
        if response.status_code != 200:
            raise HTTPException(502, f"Некорректный HTTP-ответ сервиса «Бронирование»: {response.status_code}.")
        try:
            data = response.json()
        except ValueError as exc:
            raise HTTPException(502, "Сервис «Бронирование» вернул некорректный JSON.") from exc
        required = {"review_allowed", "booking_id", "customer_id", "trip_id", "tour_id", "booking_status", "trip_status"}
        if not isinstance(data, dict) or not required.issubset(data):
            raise HTTPException(502, "Ответ сервиса «Бронирование» не соответствует контракту PR6.")
        return data
