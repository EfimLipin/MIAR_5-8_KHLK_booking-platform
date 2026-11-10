import os,json
from decimal import Decimal
from uuid import uuid4
import pytest
from sqlalchemy import create_engine,inspect
from sqlalchemy.orm import sessionmaker
from app.models import Base,Record
from app.repositories import Repository
from app.messaging import connection,setup,EXCHANGE

@pytest.fixture
def session():
    engine=create_engine(os.environ['DATABASE_URL'])
    Base.metadata.create_all(engine)
    with sessionmaker(engine,expire_on_commit=False)() as session: yield session
    engine.dispose()

@pytest.mark.parametrize('status',['pending','succeeded'])
def test_real_postgres_create_read_update(session,status):
    repo=Repository(session); key=str(uuid4())
    row=Record(id=key,customer_id=str(uuid4()),reference_id=str(uuid4()),amount=Decimal('123.45'),status=status,request_key=key)
    repo.save(row); session.expunge_all()
    found=repo.get(key)
    assert found.amount==Decimal('123.45') and found.status==status
    found.status='cancelled' if status=='pending' else 'refunded'; repo.save(found)
    session.expunge_all(); assert repo.get(key).status==found.status
    assert repo.by_request(key).id==key

def test_real_rabbitmq_direct_route_and_manual_ack():
    with connection() as conn:
        ch=conn.channel(); setup(ch); q='test_'+uuid4().hex
        ch.queue_declare(queue=q,exclusive=True,auto_delete=True)
        ch.queue_bind(queue=q,exchange=EXCHANGE,routing_key='test.expected')
        ch.basic_publish(exchange=EXCHANGE,routing_key='test.unexpected',body='wrong')
        assert ch.basic_get(q,auto_ack=False)[0] is None
        ch.basic_publish(exchange=EXCHANGE,routing_key='test.expected',body='correct')
        method,_,body=ch.basic_get(q,auto_ack=False)
        assert body==b'correct'; ch.basic_nack(method.delivery_tag,requeue=True)
        method,_,body=ch.basic_get(q,auto_ack=False)
        assert method.redelivered and body==b'correct'
        ch.basic_ack(method.delivery_tag)
        assert ch.basic_get(q,auto_ack=False)[0] is None
