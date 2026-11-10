from sqlalchemy import select
from .models import Record

class Repository:
    def __init__(self, session): self.session = session
    def get(self, key): return self.session.get(Record, key)
    def by_request(self, key):
        return self.session.scalar(select(Record).where(Record.request_key == key))
    def list(self, offset=0, count=20):
        return list(self.session.scalars(select(Record).order_by(Record.created_at).offset(offset).limit(count)))
    def save(self, row):
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return row
