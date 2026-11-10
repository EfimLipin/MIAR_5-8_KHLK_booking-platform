from decimal import Decimal
from uuid import uuid4
from types import SimpleNamespace
import pytest
from app.models import BookingInput, PaymentInput
from app.services import Service, DomainError, validate_payment, next_status

class MemoryRepo:
    def __init__(self): self.rows={}
    def get(self,key): return self.rows.get(key)
    def by_request(self,key): return next((r for r in self.rows.values() if r.request_key==key),None)
    def save(self,row):
        from datetime import datetime,timezone
        if row.created_at is None: row.created_at=datetime.now(timezone.utc)
        self.rows[row.id]=row
        return row

@pytest.fixture
def booking():
    events=[]
    return Service(MemoryRepo(),lambda kind,payload:events.append((kind,payload)),'booking'),events

def data(): return BookingInput(customer_id=uuid4(),tour_id=uuid4(),amount='45000.00')

def test_booking_creates_pending_and_event(booking):
    svc,events=booking; row=svc.create(data(),'create-1')
    assert row.status=='pending' and events[0][0]=='booking.created'

def test_booking_repeated_request_is_idempotent(booking):
    svc,_=booking; body=data(); one=svc.create(body,'same'); two=svc.create(body,'same')
    assert one.id==two.id and len(svc.repo.rows)==1

def test_idempotency_key_cannot_change_payload(booking):
    svc,_=booking; svc.create(data(),'same')
    with pytest.raises(DomainError) as e: svc.create(data(),'same')
    assert e.value.status==409

def test_booking_cancel_is_idempotent(booking):
    svc,_=booking; row=svc.create(data(),'cancel')
    assert svc.change(row.id,'cancel').status=='cancelled'
    assert svc.change(row.id,'cancel').status=='cancelled'

def test_unknown_booking(booking):
    with pytest.raises(DomainError) as e: booking[0].get(uuid4())
    assert e.value.status==404

@pytest.mark.parametrize('status,action,expected',[
    ('pending','paid','confirmed'),('confirmed','refund','cancelled'),('succeeded','refund','refunded')])
def test_transitions(status,action,expected): assert next_status(status,action)==expected

def test_invalid_transition():
    with pytest.raises(DomainError): next_status('cancelled','paid')

@pytest.mark.parametrize('field,value,code',[('customer_id','other',403),('status','cancelled',409),('amount','1.00',409)])
def test_payment_rejects_invalid_booking(field,value,code):
    booking={'customer_id':'customer','status':'pending','amount':'45000.00'}; booking[field]=value
    with pytest.raises(DomainError) as e: validate_payment(booking,'customer',Decimal('45000.00'))
    assert e.value.status==code

def test_payment_creation_calls_booking_and_emits_event():
    customer=uuid4(); reference=uuid4(); calls=[]; events=[]
    def lookup(key):
        calls.append(key); return {'customer_id':str(customer),'status':'pending','amount':'100.00'}
    svc=Service(MemoryRepo(),lambda k,p:events.append(k),'payment',lookup)
    result=svc.create(PaymentInput(customer_id=customer,booking_id=reference,amount='100.00'),'payment-1')
    assert calls==[str(reference)] and result.status=='succeeded' and events==['payment.succeeded']
    assert svc.change(result.id,'refund').status=='refunded'

def test_duplicate_payment_event_is_safe(booking):
    svc,events=booking; row=svc.create(data(),'event'); payload={'reference_id':row.id,'customer_id':row.customer_id,'amount':str(row.amount)}
    svc.on_payment('payment.succeeded',payload); svc.on_payment('payment.succeeded',payload)
    assert row.status=='confirmed' and len([e for e in events if e[0]=='booking.confirmed'])==1

@pytest.mark.parametrize('amount',['0','-1','1.234'])
def test_invalid_amount_is_rejected(amount):
    with pytest.raises(ValueError): BookingInput(customer_id=uuid4(),tour_id=uuid4(),amount=amount)
