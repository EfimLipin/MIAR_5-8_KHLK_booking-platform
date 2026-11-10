from __future__ import annotations
from datetime import datetime, timezone
from uuid import uuid4
import json
import logging
import aio_pika
from app.core.config import settings

logger = logging.getLogger(__name__)


class RabbitPublisher:
    def __init__(self) -> None:
        self.connection = None
        self.channel = None
        self.exchange = None

    async def connect(self) -> None:
        self.connection = await aio_pika.connect_robust(settings.rabbitmq_url, timeout=5)
        self.channel = await self.connection.channel()
        self.exchange = await self.channel.declare_exchange(
            settings.rabbitmq_exchange, aio_pika.ExchangeType.DIRECT, durable=True
        )
        logger.info("RabbitMQ publisher connected; exchange=%s", settings.rabbitmq_exchange)

    async def publish(self, event_type: str, aggregate_id: str, payload: dict, correlation_id: str | None = None) -> None:
        if self.exchange is None or self.connection is None or self.connection.is_closed:
            await self.connect()
        message_id = str(uuid4())
        envelope = {
            "message_id": message_id,
            "event_type": event_type,
            "event_version": 1,
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            "aggregate_id": aggregate_id,
            "correlation_id": correlation_id or message_id,
            "payload": payload,
        }
        message = aio_pika.Message(
            body=json.dumps(envelope, ensure_ascii=False).encode("utf-8"),
            content_type="application/json", delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            message_id=message_id, correlation_id=envelope["correlation_id"],
        )
        await self.exchange.publish(message, routing_key=event_type, mandatory=False)
        logger.info("Published event %s message_id=%s", event_type, message_id)

    async def close(self) -> None:
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
