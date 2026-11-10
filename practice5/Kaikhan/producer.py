"""Publish one persistent PR5 message. Example: python producer.py --delay 7"""
import argparse
import json
from datetime import datetime, timezone
from uuid import uuid4
import pika
from config import connect, declare, EXCHANGE, QUEUE, ROUTING_KEY

def main():
    parser = argparse.ArgumentParser(description="PR5 RabbitMQ producer")
    parser.add_argument("--delay", type=int, default=7)
    args = parser.parse_args()
    if not 0 <= args.delay <= 3600:
        parser.error("--delay must be between 0 and 3600 seconds")
    message = {
        "message_id": str(uuid4()), "event_type": "pr5.demo",
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "delay_seconds": args.delay,
        "payload": {"student": "Кайхан Д.С.", "group": "ИКБО-64-23"},
    }
    with connect() as conn:
        channel = conn.channel()
        declare(channel)
        channel.confirm_delivery()
        channel.basic_publish(
            exchange=EXCHANGE, routing_key=ROUTING_KEY,
            body=json.dumps(message, ensure_ascii=False).encode("utf-8"),
            properties=pika.BasicProperties(content_type="application/json", delivery_mode=2),
            mandatory=True,
        )
    print(json.dumps({"result": "PUBLISHED", "queue": QUEUE, "message": message}, ensure_ascii=False), flush=True)

if __name__ == "__main__":
    main()
