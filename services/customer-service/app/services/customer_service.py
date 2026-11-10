from datetime import datetime, timezone
from uuid import uuid4
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from app.core.security import hash_password, verify_password, create_access_token
from app.models.customer import Customer
from app.repositories.customer_repository import CustomerRepository
from app.messaging.publisher import RabbitPublisher


class CustomerService:
    def __init__(self, repo: CustomerRepository, publisher: RabbitPublisher):
        self.repo = repo
        self.publisher = publisher

    async def register(self, data):
        email = str(data.email).lower()
        if self.repo.get_by_email(email):
            raise HTTPException(409, "Учётная запись с таким email уже существует.")
        customer = Customer(
            customer_id=str(uuid4()), email=email, password_hash=hash_password(data.password),
            first_name=data.first_name, last_name=data.last_name, phone=data.phone,
            account_status="active", registered_at=datetime.now(timezone.utc), profile_version=1,
        )
        try:
            customer = self.repo.create(customer)
        except IntegrityError as exc:
            self.repo.db.rollback()
            raise HTTPException(409, "Учётная запись с таким email уже существует.") from exc
        await self.publisher.publish(
            "customer.registered", customer.customer_id,
            {"customer_id": customer.customer_id, "registered_at": customer.registered_at.isoformat(),
             "account_status": customer.account_status},
        )
        return customer

    def authenticate(self, email: str, password: str):
        customer = self.repo.get_by_email(email.lower())
        if customer is None or not verify_password(password, customer.password_hash):
            raise HTTPException(401, "Неверная пара email/password.")
        if customer.account_status != "active":
            raise HTTPException(403, "Учётная запись заблокирована.")
        token, expires_in = create_access_token(customer.customer_id)
        return {"access_token": token, "token_type": "Bearer", "expires_in": expires_in,
                "customer_id": customer.customer_id}

    def get_profile(self, customer_id: str):
        customer = self.repo.get_by_id(customer_id)
        if customer is None:
            raise HTTPException(404, "Клиент не найден.")
        return customer

    async def patch_profile(self, customer_id: str, patch: dict):
        customer = self.get_profile(customer_id)
        changed = []
        for name, value in patch.items():
            if getattr(customer, name) != value:
                setattr(customer, name, value)
                changed.append(name)
        if not changed:
            raise HTTPException(400, "Не передано ни одного изменяемого значения.")
        customer.updated_at = datetime.now(timezone.utc)
        customer.profile_version += 1
        customer = self.repo.update(customer)
        await self.publisher.publish(
            "customer.profile.updated", customer.customer_id,
            {"customer_id": customer.customer_id, "profile_version": customer.profile_version,
             "changed_fields": changed, "updated_at": customer.updated_at.isoformat()},
        )
        # Keep event metadata separate from the persisted customer model.
        return customer, changed
