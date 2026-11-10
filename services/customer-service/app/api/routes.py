from uuid import UUID
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import decode_access_token
from app.core.config import settings
from app.models.schemas import CustomerCreate, TokenRequest, TokenResponse, CustomerResponse, CustomerPatch, CustomerPatchResponse
from app.repositories.customer_repository import CustomerRepository
from app.services.customer_service import CustomerService
from app.messaging.publisher import RabbitPublisher

router = APIRouter(prefix="/api/v1", tags=["Customer Management"])


def get_service(request: Request, db: Session = Depends(get_db)) -> CustomerService:
    return CustomerService(CustomerRepository(db), request.app.state.publisher)


def current_customer_id(authorization: str | None = Header(default=None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Требуется заголовок Authorization: Bearer.")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        return str(UUID(str(decode_access_token(token)["sub"])))
    except Exception as exc:
        raise HTTPException(401, "Токен отсутствует, просрочен или недействителен.") from exc


def ensure_owner(path_customer_id: UUID, token_customer_id: str) -> None:
    if str(path_customer_id) != token_customer_id:
        raise HTTPException(403, "Доступ разрешён только к собственному профилю.")


@router.post("/customers", response_model=CustomerResponse, status_code=201)
async def register_customer(data: CustomerCreate, service: CustomerService = Depends(get_service)):
    return await service.register(data)


@router.post("/auth/tokens", response_model=TokenResponse)
def issue_token(data: TokenRequest, service: CustomerService = Depends(get_service)):
    return service.authenticate(str(data.email), data.password)


@router.get("/customers/{customer_id}", response_model=CustomerResponse)
def get_customer(customer_id: UUID, owner_id: str = Depends(current_customer_id), service: CustomerService = Depends(get_service)):
    ensure_owner(customer_id, owner_id)
    return service.get_profile(str(customer_id))


@router.patch("/customers/{customer_id}", response_model=CustomerPatchResponse)
async def patch_customer(customer_id: UUID, data: CustomerPatch, owner_id: str = Depends(current_customer_id), service: CustomerService = Depends(get_service)):
    ensure_owner(customer_id, owner_id)
    patch = data.model_dump(exclude_unset=True)
    if not patch:
        raise HTTPException(400, "Тело запроса не содержит изменяемых полей.")
    customer, changed = await service.patch_profile(str(customer_id), patch)
    result = CustomerResponse.model_validate(customer).model_dump()
    result["changed_fields"] = changed
    return result
