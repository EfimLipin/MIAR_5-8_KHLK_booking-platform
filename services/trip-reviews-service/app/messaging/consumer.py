from __future__ import annotations
import asyncio
import json
import logging
from datetime import datetime, timezone
import aio_pika
from pymongo.errors import DuplicateKeyError
from app.core.config import settings
from app.repositories.trip_repository import TripRepository
from app.services.trip_service import TripService

logger = logging.getLogger(__name__)
INCOMING_EVENTS = ("booking.confirmed", "booking.cancelled", "documents.ready", "customer.profile.updated")


async def _on_message(message: aio_pika.IncomingMessage, service: TripService, repo: TripRepository):
    async with message.process(requeue=False):
        try:
            envelope = json.loads(message.body.decode("utf-8"))
            message_id = envelope["message_id"]
            event_type = envelope["event_type"]
            if event_type not in INCOMING_EVENTS or not isinstance(envelope.get("payload"), dict):
                raise ValueError("Некорректный конверт или неподдерживаемый тип события")
        except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError, ValueError):
            logger.exception("Invalid RabbitMQ message; rejected without requeue")
            raise

        if await repo.is_message_processed(message_id):
            logger.info("Duplicate event %s skipped", message_id)
            return
        await service.handle_event(event_type, envelope["payload"])
        await repo.mark_message_processed(message_id, event_type)
        logger.info("Processed event %s message_id=%s", event_type, message_id)


async def consume_forever(database, stop_event: asyncio.Event):
    repo = TripRepository(database)
    publisher = None
    service = TripService(repo, publisher)
    while not stop_event.is_set():
        connection = None
        try:
            connection = await aio_pika.connect_robust(settings.rabbitmq_url, timeout=5)
            channel = await connection.channel()
            await channel.set_qos(prefetch_count=10)
            exchange = await channel.declare_exchange(settings.rabbitmq_exchange, aio_pika.ExchangeType.DIRECT, durable=True)
            dead_exchange = await channel.declare_exchange("travel.events.dlx", aio_pika.ExchangeType.DIRECT, durable=True)
            dead_queue_name = f"{settings.rabbitmq_queue}.dead"
            dead_queue = await channel.declare_queue(dead_queue_name, durable=True)
            await dead_queue.bind(dead_exchange, routing_key=dead_queue_name)
            queue = await channel.declare_queue(settings.rabbitmq_queue, durable=True,
                arguments={"x-dead-letter-exchange": "travel.events.dlx", "x-dead-letter-routing-key": dead_queue_name})
            for event_type in INCOMING_EVENTS:
                await queue.bind(exchange, routing_key=event_type)
            await queue.consume(lambda msg: _on_message(msg, service, repo))
            logger.info("RabbitMQ consumer started queue=%s bindings=%s", settings.rabbitmq_queue, INCOMING_EVENTS)
            await stop_event.wait()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("RabbitMQ consumer connection failed; retrying in 5 seconds")
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=5)
            except asyncio.TimeoutError:
                pass
        finally:
            if connection and not connection.is_closed:
                await connection.close()
