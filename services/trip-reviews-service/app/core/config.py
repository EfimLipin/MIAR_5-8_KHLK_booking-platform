from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "trip-reviews"
    mongodb_url: str = Field(alias="MONGODB_URL")
    mongodb_database: str = "travel_platform"
    rabbitmq_url: str = Field(alias="RABBITMQ_URL")
    rabbitmq_exchange: str = "travel.events"
    rabbitmq_queue: str = "trip_reviews_service"
    jwt_secret_key: str = Field(alias="JWT_SECRET_KEY")
    jwt_algorithm: str = "HS256"
    booking_service_url: str = "http://host.docker.internal:8100"
    booking_timeout_seconds: float = 4.0
    completion_poll_seconds: int = 60
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", populate_by_name=True)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
