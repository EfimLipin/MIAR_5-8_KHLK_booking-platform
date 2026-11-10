import os, threading
from contextlib import asynccontextmanager
from uuid import UUID
import httpx
from fastapi import FastAPI, Header, Query
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base,BookingInput,PaymentInput,serialize
from .repositories import Repository
from .services import Service,DomainError
from .messaging import publish,consume

MODE=os.environ.get('SERVICE_MODE','booking')
engine=create_engine(os.environ['DATABASE_URL'],pool_pre_ping=True)
Session=sessionmaker(engine,expire_on_commit=False)
stop=threading.Event()
@asynccontextmanager
async def lifespan(app):
    Base.metadata.create_all(engine)
    worker=None
    if MODE=='booking':
        worker=threading.Thread(target=consume,args=(Session,stop),daemon=True); worker.start()
    yield
    stop.set()
    if worker: worker.join(timeout=3)
    engine.dispose()

app=FastAPI(title='Booking Service' if MODE=='booking' else 'Payment Service',version='1.0.0',lifespan=lifespan,
            description='Учебный локальный сервис. Платежи моделируются без банковского провайдера и без списания денег.')
@app.exception_handler(DomainError)
async def domain_error(request,error): return JSONResponse(status_code=error.status,content={'detail':error.detail})
def booking_lookup(key):
    try:
        response=httpx.get(os.environ['BOOKING_SERVICE_URL']+'/bookings/'+key,timeout=4)
    except httpx.TimeoutException: raise DomainError(504,'Booking service timed out')
    except httpx.RequestError: raise DomainError(503,'Booking service unavailable')
    if response.status_code==404: raise DomainError(404,'Booking not found')
    if response.status_code!=200: raise DomainError(502,'Booking service error')
    return response.json()
def service(session): return Service(Repository(session),publish,MODE,booking_lookup)

prefix='/bookings' if MODE=='booking' else '/payments'
Input=BookingInput if MODE=='booking' else PaymentInput
def create_record(data: Input, idempotency_key: str=Header(min_length=1,max_length=100)):
    with Session() as session: return serialize(service(session).create(data,idempotency_key))
def get_record(record_id: UUID):
    with Session() as session: return serialize(service(session).get(record_id))
def list_records(offset:int=Query(0,ge=0),count:int=Query(20,ge=1,le=100)):
    with Session() as session:
        return {'items':[serialize(row) for row in Repository(session).list(offset,count)],'offset':offset,'count':count}
def change_record(record_id: UUID):
    with Session() as session: return serialize(service(session).change(record_id,'cancel' if MODE=='booking' else 'refund'))
app.add_api_route(prefix,create_record,methods=['POST'],status_code=201)
app.add_api_route(prefix,list_records,methods=['GET'])
app.add_api_route(prefix+'/{record_id}',get_record,methods=['GET'])
app.add_api_route(prefix+'/{record_id}/'+('cancel' if MODE=='booking' else 'refund'),change_record,methods=['POST'])
