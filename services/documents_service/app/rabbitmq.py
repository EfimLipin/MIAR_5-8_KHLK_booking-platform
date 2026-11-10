import json, traceback
from aio_pika import connect_robust, IncomingMessage
from app.settings import settings
from app.database import SessionLocal
from app.services.document_service import DocumentService

async def process_event(msg: IncomingMessage):
    try:
        data = json.loads(msg.body.decode())
        event = data.get("event")
        db = SessionLocal()
        service = DocumentService(db)
        if event == "payment.completed":
            service.create_set(booking_id=data["booking_id"],
                               user_id=data["user_id"],
                               tour_id=data["tour_id"])
        elif event == "booking.canceled":
            service.cancel_by_booking(data["booking_id"])
        await msg.ack()
    except Exception:
        traceback.print_exc()
        await msg.nack(requeue=True)

async def consume(loop) -> None:
    connection = await connect_robust(settings.amqp_url, loop=loop)
    channel = await connection.channel()
    exchange = await channel.declare_exchange("tour_events", type="topic", durable=True)
    queue = await channel.declare_queue("documents_events_queue", durable=True)
    await queue.bind(exchange, routing_key="payment.completed")
    await queue.bind(exchange, routing_key="booking.canceled")
    await queue.consume(process_event)
    print("Documents service: RabbitMQ consuming started")
    return connection