from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    amqp_url: str = "amqp://guest:guest@localhost:5672/"
    mongo_url: str = "mongodb://localhost:27017"
    catalog_service_url: str = "http://localhost:8001"

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()