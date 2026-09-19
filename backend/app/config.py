from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Absent Request API"
    database_url: str = "sqlite:///./absent_requests.db"
    frontend_origin: str = "http://localhost:5173"
    gmail_sender: str = ""
    gmail_credentials_file: str = ""
    gmail_token_file: str = "gmail-token.json"
    google_cloud_project: str = ""
    pubsub_verification_token: str = ""
    pubsub_audience: str = ""
    public_api_url: str = "http://localhost:8000"


@lru_cache
def get_settings() -> Settings:
    return Settings()
