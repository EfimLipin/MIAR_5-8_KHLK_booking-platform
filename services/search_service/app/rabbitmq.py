import json, traceback
from aio_pika import connect_robust, IncomingMessage
from pymongo import MongoClient
from app.settings import settings

async def process_event(msg: IncomingMessage):
    try:
        data = json.loads(msg.body.decode())
        event = data.get("event")
        col = MongoClient(settings.mongo_url)["search_service"]["tours_index"]
        if event == "tour.published":
            col.replace_one({"tour_id": data["tour_id"]}, data, upsert=True)
        elif event == "tour.unpublished":
            col.delete_one({"tour_id": data["tour_id"]})
        await msg.ack()
    except Exception:
        traceback.print_exc()
        await msg.nack(requeue=True)

async def consume(loop) -> None:
    connection = await connect_robust(settings.amqp_url, loop=loop)
    channel = await connection.channel()
    exchange = await channel.declare_exchange("tour_events", type="topic", durable=True)
    queue = await channel.declare_queue("search_events_queue", durable=True)
    await queue.bind(exchange, routing_key="tour.published")
    await queue.bind(exchange, routing_key="tour.unpublished")
    await queue.consume(process_event)
    print("Search service: RabbitMQ consuming started")
    return connection