"""Check AMQP connectivity and print a clear diagnostic result."""
from __future__ import annotations

import socket
import sys

from src.config import Settings
from src.rabbit import open_connection


def main() -> int:
    try:
        settings = Settings.from_env()
    except ValueError as exc:
        print(f"Ошибка конфигурации: {exc}")
        return 2

    print(f"Проверка TCP {settings.host}:{settings.port} ...")
    try:
        with socket.create_connection((settings.host, settings.port), timeout=5):
            print("TCP-подключение доступно.")
    except OSError as exc:
        print(f"TCP-подключение недоступно: {exc}")
        print("Проверьте адрес, порт, VPN/сетевой доступ и состояние учебного брокера.")
        return 1

    print("Проверка AMQP-аутентификации ...")
    try:
        connection = open_connection(settings)
        connection.close()
    except Exception as exc:
        print(f"AMQP-подключение не выполнено: {type(exc).__name__}: {exc}")
        return 1

    print("AMQP-подключение успешно; соединение закрыто.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
