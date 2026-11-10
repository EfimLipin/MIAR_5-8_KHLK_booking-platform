import asyncio
import logging
from contextlib import asynccontextmanager
from uuid import uuid4
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from app.api.routes import router
from app.core.config import settings
from app.core.mongo import MongoContext
from app.core.errors import http_error_handler, validation_error_handler, unhandled_error_handler
from app.core.request_context import request_id_var
from app.messaging.publisher import RabbitPublisher
from app.messaging.consumer import consume_forever
from app.repositories.trip_repository import TripRepository
from app.services.trip_service import TripService

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


async def completion_worker(database, publisher, stop_event: asyncio.Event):
    service = TripService(TripRepository(database), publisher)
    while not stop_event.is_set():
        try:
            completed_ids = await service.complete_due_trips()
            if completed_ids:
                logging.getLogger(__name__).info("Completed due trips: %s", completed_ids)
        except Exception:
            logging.getLogger(__name__).exception("Trip completion worker iteration failed")
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=settings.completion_poll_seconds)
        except asyncio.TimeoutError:
            pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    mongo = MongoContext()
    await mongo.connect()
    publisher = RabbitPublisher()
    try:
        await publisher.connect()
    except Exception:
        logging.getLogger(__name__).exception("RabbitMQ publisher unavailable at startup; reconnect on publish")
    stop_event = asyncio.Event()
    consumer_task = asyncio.create_task(consume_forever(mongo.database, stop_event))
    completion_task = asyncio.create_task(completion_worker(mongo.database, publisher, stop_event))
    app.state.mongo = mongo
    app.state.publisher = publisher
    yield
    stop_event.set()
    consumer_task.cancel()
    completion_task.cancel()
    await asyncio.gather(consumer_task, completion_task, return_exceptions=True)
    await publisher.close()
    await mongo.close()


app = FastAPI(title="Поездка и отзывы", version="1.0.0", lifespan=lifespan)
app.include_router(router)
app.add_exception_handler(HTTPException, http_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(Exception, unhandled_error_handler)


@app.middleware("http")
async def attach_request_id(request: Request, call_next):
    rid = request.headers.get("X-Request-ID") or str(uuid4())
    token = request_id_var.set(rid)
    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = rid
        return response
    finally:
        request_id_var.reset(token)
