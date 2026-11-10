from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.settings import settings

engine = create_engine(settings.postgres_url)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()