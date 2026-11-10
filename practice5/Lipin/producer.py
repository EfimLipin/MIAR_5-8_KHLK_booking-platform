import pika

RABBITMQ_HOST = 'localhost'
RABBITMQ_PORT = 5672
RABBITMQ_USER = 'guest'
RABBITMQ_PASSWORD = 'guest'

EXCHANGE_NAME = 'ikbo-64-23_lipin_topic'
QUEUE_NAME = 'ikbo-64-23_lipin'
ROUTING_KEY = 'tour.search.requested'

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
                   routing_key='tour.search.*')

body = 'Найден тур: Москва...Париж...'
channel.basic_publish(
    exchange=EXCHANGE_NAME,
    routing_key=ROUTING_KEY,
    body=body
)
print(f'SENT: {body}')

channel.close()
connect.close()