"""Consume PR5 messages and ACK after their requested delay."""
import argparse
import json
import time
from config import connect, declare, QUEUE

def main():
    parser = argparse.ArgumentParser(description="PR5 RabbitMQ consumer")
    parser.add_argument("--once", action="store_true", help="Process one message, then exit")
    parser.add_argument("--timeout", type=float, default=30, help="Wait limit in --once mode")
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    with connect() as conn:
        channel = conn.channel()
        declare(channel)
        channel.basic_qos(prefetch_count=1)
        print("WAITING queue=" + QUEUE + " auto_ack=False prefetch_count=1", flush=True)
        wait_started = time.monotonic()
        for method, properties, body in channel.consume(QUEUE, auto_ack=False, inactivity_timeout=1):
            if method is None:
                if args.once and time.monotonic() - wait_started >= args.timeout:
                    raise TimeoutError("No message received before timeout")
                continue
            try:
                message = json.loads(body)
                delay = message["delay_seconds"]
                if type(delay) is not int or not 0 <= delay <= 3600:
                    raise ValueError("delay_seconds must be an integer from 0 to 3600")
            except (ValueError, KeyError, TypeError) as error:
                channel.basic_nack(method.delivery_tag, requeue=False)
                print("REJECTED " + str(error), flush=True)
                if args.once:
                    raise
                continue
            print("RECEIVED " + json.dumps(message, ensure_ascii=False), flush=True)
            started = time.monotonic()
            conn.sleep(delay)
            measured = time.monotonic() - started
            channel.basic_ack(method.delivery_tag)
            print(json.dumps({"result": "ACK", "message_id": message["message_id"],
                              "delay_seconds": delay, "measured_seconds": round(measured, 3),
                              "delivery_mode": properties.delivery_mode,
                              "manual_ack": True}), flush=True)
            if args.once:
                channel.cancel()
                return

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Consumer stopped")
