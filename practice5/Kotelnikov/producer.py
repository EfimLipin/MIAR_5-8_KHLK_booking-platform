import pika

credentials = pika.PlainCredentials('admin', 'admin123')
parameters = pika.ConnectionParameters(
    host='localhost',
    port=5672,
    credentials=credentials
)

connection = pika.BlockingConnection(parameters)
channel = connection.channel()

queue_name = 'ikbo-64-23_kotelnikov'
channel.queue_declare(queue=queue_name, auto_delete=True)

exchange_name = 'kotelnikov_fanout_exchange'
channel.exchange_declare(exchange=exchange_name, exchange_type='fanout')

channel.queue_bind(exchange=exchange_name, queue=queue_name)

message = 'Привет от Котельникова! Это тестовое сообщение для ПР5.'
channel.basic_publish(
    exchange=exchange_name,
    routing_key='',
    body=message
)
print(f" [x] Отправлено сообщение: {message}")

connection.close()