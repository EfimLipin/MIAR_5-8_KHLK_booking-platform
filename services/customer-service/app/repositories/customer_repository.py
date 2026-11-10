from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.customer import Customer


class CustomerRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, customer_id: str) -> Customer | None:
        return self.db.get(Customer, customer_id)

    def get_by_email(self, email: str) -> Customer | None:
        return self.db.scalar(select(Customer).where(Customer.email == email.lower()))

    def create(self, customer: Customer) -> Customer:
        self.db.add(customer)
        self.db.commit()
        self.db.refresh(customer)
        return customer

    def update(self, customer: Customer) -> Customer:
        self.db.add(customer)
        self.db.commit()
        self.db.refresh(customer)
        return customer
