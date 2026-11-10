import asyncio
from fastapi import FastAPI
from app.routers.search_router import router as search_router
from app import rabbitmq

app = FastAPI(title="Search Service")

@app.on_event("startup")
async def startup():
    loop = asyncio.get_event_loop()
    asyncio.ensure_future(rabbitmq.consume(loop))

app.include_router(search_router)