"""Consume messages with body-driven delay and manual acknowledgement."""
from __future__ import annotations

import logging
import time

from src.config import Settings
from src.messages import decode_message, get_delay_seconds
from src.rabbit import declare_topology, open_connection

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("pr5.consumer")


def main() -> int:
    settings = Settings.from_env()
    connection = open_connection(settings)
    try:
        channel = connection.channel()
        declare_topology(channel, settings)
        channel.basic_qos(prefetch_count=1)

        def callback(ch, method, properties, body: bytes) -> None:
            try:
                message = decode_message(body)
                delay_seconds = get_delay_seconds(message)
                logger.info(
                    "Получено событие %s; message_id=%s; задержка=%d сек.",
                    message.get("event_type", "unknown"),
                    message.get("message_id", "unknown"),
                    delay_seconds,
                )
                time.sleep(delay_seconds)
                ch.basic_ack(delivery_tag=method.delivery_tag)
                logger.info("Обработка завершена; сообщение подтверждено (ACK).")
            except ValueError as exc:
                logger.error("Сообщение отклонено: %s", exc)
                # Без DLQ некорректное сообщение удаляется, чтобы не создавать бесконечный цикл.
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            except Exception:
                logger.exception("Ошибка обработки; сообщение возвращено в очередь.")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

        channel.basic_consume(
            queue=settings.queue,
            on_message_callback=callback,
            auto_ack=False,
        )
        logger.info(
            "Ожидание сообщений: queue=%s, exchange=%s, routing_key=%s. Для остановки нажмите Ctrl+C.",
            settings.queue,
            settings.exchange,
            settings.routing_key,
        )
        channel.start_consuming()
    except KeyboardInterrupt:
        logger.info("Получена команда остановки.")
    finally:
        if connection.is_open:
            connection.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
