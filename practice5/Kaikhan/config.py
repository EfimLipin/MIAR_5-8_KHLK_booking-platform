"""Common settings for the standalone PR5 publisher and consumer."""
import os
from pathlib import Path
from urllib.parse import quote
import pika

EXCHANGE = "travel.events"
QUEUE = "ikbo-64-23_kaikhan"
ROUTING_KEY = "pr5.demo"

def connect():
    url = os.environ.get("RABBITMQ_URL")
    if not url:
        env_file = Path(__file__).resolve().parents[1] / ".env"
        settings = {}
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8-sig").splitlines():
                if "=" in line and not line.lstrip().startswith("#"):
                    key, value = line.split("=", 1)
                    settings[key.strip()] = value.strip()
        password = os.environ.get("RABBITMQ_PASSWORD", settings.get("RABBITMQ_PASSWORD"))
        if not password:
            raise RuntimeError("Set RABBITMQ_URL or RABBITMQ_PASSWORD, or create project/.env")
        url = "amqp://labs:" + quote(password, safe="") + "@localhost:5672/"
    params = pika.URLParameters(url)
    params.connection_attempts = 10
    params.retry_delay = 2
    params.blocked_connection_timeout = 10
    return pika.BlockingConnection(params)

def declare(channel):
    channel.exchange_declare(exchange=EXCHANGE, exchange_type="direct", durable=True)
    channel.queue_declare(queue=QUEUE, durable=True)
    channel.queue_bind(queue=QUEUE, exchange=EXCHANGE, routing_key=ROUTING_KEY)
