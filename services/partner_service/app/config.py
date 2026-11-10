from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    rabbitmq_url: str
    catalog_service_url: str  # <-- ДОБАВИТЬ ЭТУ СТРОКУ

    class Config:
        env_file = ".env"

settings = Settings()