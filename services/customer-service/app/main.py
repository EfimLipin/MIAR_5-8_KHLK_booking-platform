import logging
from contextlib import asynccontextmanager
from uuid import uuid4
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi import HTTPException
from app.api.routes import router
from app.core.database import init_db
from app.core.errors import http_error_handler, validation_error_handler, unhandled_error_handler
from app.core.request_context import request_id_var
from app.messaging.publisher import RabbitPublisher

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    publisher = RabbitPublisher()
    try:
        await publisher.connect()
    except Exception:
        logging.getLogger(__name__).exception("RabbitMQ недоступен при запуске; повторное соединение будет выполнено при публикации")
    app.state.publisher = publisher
    yield
    await publisher.close()


app = FastAPI(title="Управление клиентами", version="1.0.0", lifespan=lifespan)
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
