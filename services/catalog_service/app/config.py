from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    rabbitmq_url: str

    class Config:
        env_file = ".env"

settings = Settings()