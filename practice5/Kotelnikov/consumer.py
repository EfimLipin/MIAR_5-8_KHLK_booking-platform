import pika
import time
import random

credentials = pika.PlainCredentials('admin', 'admin123')
parameters = pika.ConnectionParameters(
    host='localhost',
    port=5672,
    credentials=credentials
)

connection = pika.BlockingConnection(parameters)
channel = connection.channel()

queue_name = 'ikbo-64-23_kotelnikov'
exchange_name = 'kotelnikov_fanout_exchange'

channel.queue_declare(queue=queue_name, auto_delete=True)
channel.exchange_declare(exchange=exchange_name, exchange_type='fanout')
channel.queue_bind(exchange=exchange_name, queue=queue_name)

def callback(ch, method, properties, body):
    message = body.decode('utf-8')
    print(f" [x] Получено сообщение: {message}")

    delay = random.randint(1, 5)
    print(f" [x] Начинаю обработку, задержка {delay} сек...")
    time.sleep(delay)

    print(f" [x] Обработка завершена за {delay} сек.")
    ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_qos(prefetch_count=1)

channel.basic_consume(
    queue=queue_name,
    on_message_callback=callback
)

print(' [*] Ожидаю сообщения. Для выхода нажми Ctrl+C')
channel.start_consuming()