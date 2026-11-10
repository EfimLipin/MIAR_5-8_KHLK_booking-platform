from time import sleep
import pika

RABBITMQ_HOST = 'localhost'
RABBITMQ_PORT = 5672
RABBITMQ_USER = 'guest'
RABBITMQ_PASSWORD = 'guest'

EXCHANGE_NAME = 'ikbo-64-23_lipin_topic'
QUEUE_NAME = 'ikbo-64-23_lipin'
BINDING_KEY = 'tour.search.*'

def delayed_callback(ch, method, properties, body):
    print(f" [x] Received {body.decode()}")
    delay = body.count(b'.')
    print(f" [x] Simulating load: sleeping {delay} seconds")
    sleep(delay)
    ch.basic_ack(delivery_tag=method.delivery_tag)
    print(" [x] Done")

connect = pika.BlockingConnection(
    pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        credentials=pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
    )
)
channel = connect.channel()

channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='topic')
channel.queue_declare(queue=QUEUE_NAME, auto_delete=True)
channel.queue_bind(exchange=EXCHANGE_NAME, queue=QUEUE_NAME,
                   routing_key=BINDING_KEY)

channel.basic_qos(prefetch_count=1)

channel.basic_consume(queue=QUEUE_NAME,
                      on_message_callback=delayed_callback,
                      auto_ack=False)

print('Waiting for messages. To exit press CTRL+C')
channel.start_consuming()