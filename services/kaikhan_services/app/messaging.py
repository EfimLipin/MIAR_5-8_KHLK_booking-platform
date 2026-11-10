import json, logging, os, time
from datetime import datetime, timezone
from uuid import uuid4
import pika

log = logging.getLogger('events')
EXCHANGE='travel.events'
def connection():
    parameters=pika.URLParameters(os.environ['RABBITMQ_URL'])
    parameters.connection_attempts=10
    parameters.retry_delay=2
    parameters.socket_timeout=5
    parameters.blocked_connection_timeout=10
    return pika.BlockingConnection(parameters)
def setup(channel): channel.exchange_declare(exchange=EXCHANGE,exchange_type='direct',durable=True)
def publish(kind,payload):
    event={'message_id':str(uuid4()),'event_type':kind,'occurred_at':datetime.now(timezone.utc).isoformat(),'payload':payload}
    with connection() as conn:
        channel=conn.channel(); setup(channel); channel.confirm_delivery()
        channel.basic_publish(exchange=EXCHANGE,routing_key=kind,body=json.dumps(event),
                              properties=pika.BasicProperties(content_type='application/json',delivery_mode=2))
    log.warning('PUBLISHED %s resource=%s',kind,payload['id'])

def consume(session_factory, stop):
    from .repositories import Repository
    from .services import Service, DomainError
    while not stop.is_set():
        try:
            with connection() as conn:
                ch=conn.channel(); setup(ch)
                ch.queue_declare(queue='booking_payments',durable=True)
                ch.queue_declare(queue='booking_payments.dead',durable=True)
                for key in ['payment.succeeded','payment.refunded']:
                    ch.queue_bind(queue='booking_payments',exchange=EXCHANGE,routing_key=key)
                ch.basic_qos(prefetch_count=1)
                for method,properties,body in ch.consume('booking_payments',inactivity_timeout=1,auto_ack=False):
                    if stop.is_set(): break
                    if method is None: continue
                    try:
                        message=json.loads(body)
                        with session_factory() as session:
                            Service(Repository(session),publish,'booking').on_payment(message['event_type'],message['payload'])
                        ch.basic_ack(method.delivery_tag)
                        log.warning('ACK %s message=%s',message['event_type'],message['message_id'])
                    except (DomainError,KeyError,ValueError) as error:
                        ch.basic_publish(exchange='',routing_key='booking_payments.dead',body=body,
                                         properties=pika.BasicProperties(delivery_mode=2))
                        ch.basic_ack(method.delivery_tag)
                        log.exception('INVALID EVENT %s',error)
                    except Exception:
                        ch.basic_nack(method.delivery_tag,requeue=True)
                        time.sleep(1)
                ch.cancel()
        except Exception:
            log.exception('Consumer reconnecting')
            stop.wait(2)
