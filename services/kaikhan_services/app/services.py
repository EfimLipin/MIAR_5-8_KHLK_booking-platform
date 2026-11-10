from uuid import uuid4
from .models import Record, serialize

class DomainError(Exception):
    def __init__(self, status, detail): self.status, self.detail = status, detail

def validate_payment(booking, customer_id, amount):
    from decimal import Decimal
    if booking['customer_id'] != str(customer_id): raise DomainError(403, 'Booking belongs to another customer')
    if booking['status'] != 'pending': raise DomainError(409, 'Booking is not awaiting payment')
    if Decimal(booking['amount']) != amount: raise DomainError(409, 'Payment amount does not match booking')

def next_status(current, action):
    transitions = {('pending','cancel'): 'cancelled', ('pending','paid'): 'confirmed',
                   ('confirmed','refund'): 'cancelled', ('succeeded','refund'): 'refunded'}
    if (current, action) not in transitions: raise DomainError(409, 'Invalid state transition')
    return transitions[current,action]

class Service:
    def __init__(self, repo, publish, mode, booking_lookup=None):
        self.repo,self.publish,self.mode,self.booking_lookup = repo,publish,mode,booking_lookup
    def get(self, key):
        row = self.repo.get(str(key))
        if row is None: raise DomainError(404, 'Resource not found')
        return row
    def create(self, data, request_key):
        old = self.repo.by_request(request_key)
        reference = str(data.tour_id if self.mode == 'booking' else data.booking_id)
        if old:
            if (old.customer_id,old.reference_id,old.amount) != (str(data.customer_id),reference,data.amount):
                raise DomainError(409, 'Idempotency key used with different data')
            self.publish('booking.created' if self.mode == 'booking' else 'payment.succeeded', serialize(old))
            return old
        if self.mode == 'payment': validate_payment(self.booking_lookup(reference),data.customer_id,data.amount)
        row = Record(id=str(uuid4()), customer_id=str(data.customer_id), reference_id=reference,
                     amount=data.amount, status='pending' if self.mode == 'booking' else 'succeeded', request_key=request_key)
        self.repo.save(row)
        self.publish('booking.created' if self.mode == 'booking' else 'payment.succeeded', serialize(row))
        return row
    def change(self, key, action):
        row = self.get(key)
        target = 'cancelled' if self.mode == 'booking' else 'refunded'
        if row.status == target: return row
        row.status = next_status(row.status,action)
        self.repo.save(row)
        self.publish('booking.cancelled' if self.mode == 'booking' else 'payment.refunded', serialize(row))
        return row
    def on_payment(self, event_type, payload):
        row = self.get(payload['reference_id'])
        if str(row.amount) != payload['amount'] or row.customer_id != payload['customer_id']:
            raise DomainError(409,'Event does not match booking')
        target = 'confirmed' if event_type == 'payment.succeeded' else 'cancelled'
        if row.status == target: return row
        row.status = next_status(row.status,'paid' if event_type == 'payment.succeeded' else 'refund')
        self.repo.save(row)
        self.publish('booking.confirmed' if target == 'confirmed' else 'booking.cancelled', serialize(row))
        return row
