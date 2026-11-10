import httpx
import uuid
from app.repository import PartnerRequestRepository
from app.models import PartnerRequest, RequestStatus
from app.config import settings

class PartnerService:
    def __init__(self, repo: PartnerRequestRepository):
        self.repo = repo

    async def create_request(self, tour_id: uuid.UUID, booking_id: uuid.UUID, client_id: uuid.UUID, comment: str = None):
        # Синхронный вызов к Каталогу туров
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{settings.catalog_service_url}/tours/{tour_id}", timeout=5.0)
            except httpx.RequestError:
                raise ValueError("Catalog service unavailable")
            if response.status_code == 404:
                raise KeyError("Tour not found in catalog")
            if response.status_code != 200:
                raise ValueError("Catalog service error")
            tour_data = response.json()
            if tour_data["status"] != "published":
                raise ValueError("Tour is not published")

        request = PartnerRequest(
            tour_id=tour_id,
            booking_id=booking_id,
            client_id=client_id,
            comment=comment,
            status=RequestStatus.SENT
        )
        return self.repo.create(request)

    def get_request(self, request_id: uuid.UUID):
        req = self.repo.get_by_id(request_id)
        if not req:
            raise KeyError("Request not found")
        return req

    def get_requests(self, offset, count, status):
        return self.repo.get_all(offset, count, status)

    def confirm_request(self, request_id: uuid.UUID):
        req = self.repo.get_by_id(request_id)
        if not req:
            raise KeyError("Request not found")
        if req.status != RequestStatus.SENT:
            raise ValueError("Request already processed")
        return self.repo.confirm(req)

    def cancel_request(self, request_id: uuid.UUID):
        req = self.repo.get_by_id(request_id)
        if not req:
            raise KeyError("Request not found")
        if req.status != RequestStatus.SENT:
            raise ValueError("Request already processed")
        return self.repo.cancel(req)