import asyncio
from fastapi import FastAPI
from app.routers.document_router import router as document_router
from app.schemas.base import Base
from app.database import engine
from app import rabbitmq

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Documents Service")

@app.on_event("startup")
async def startup():
    loop = asyncio.get_event_loop()
    asyncio.ensure_future(rabbitmq.consume(loop))

app.include_router(document_router)