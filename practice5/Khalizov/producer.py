"""Publish a persistent trip.completed demonstration event to RabbitMQ."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone

from src.config import Settings
from src.messages import create_demo_message, encode_message
from src.rabbit import declare_topology, open_connection


def main() -> int:
    parser = argparse.ArgumentParser(description="Отправка тестового сообщения в RabbitMQ (PR5, вариант 4).")
    parser.add_argument("--delay", type=int, default=3, help="Неотрицательная задержка обработки в секундах.")
    args = parser.parse_args()

    settings = Settings.from_env()
    message = create_demo_message(args.delay)

    connection = open_connection(settings)
    try:
        channel = connection.channel()
        declare_topology(channel, settings)
        channel.confirm_delivery()
        import pika

        properties = pika.BasicProperties(
            content_type="application/json",
            content_encoding="utf-8",
            delivery_mode=2,  # persistent delivery mode
            message_id=message["message_id"],
            timestamp=int(datetime.now(timezone.utc).timestamp()),
            type=message["event_type"],
        )
        published = channel.basic_publish(
            exchange=settings.exchange,
            routing_key=settings.routing_key,
            body=encode_message(message),
            properties=properties,
            mandatory=True,
        )
        if published is False:
            raise RuntimeError("Брокер не подтвердил публикацию сообщения.")

        print("Сообщение опубликовано и подтверждено брокером.")
        print(f"Exchange: {settings.exchange} (direct, durable)")
        print(f"Routing key: {settings.routing_key}")
        print(f"Queue: {settings.queue} (durable)")
        print(f"Message ID: {message['message_id']}")
        print(f"Delay from body: {message['delay_seconds']} sec")
        return 0
    finally:
        if connection.is_open:
            connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
