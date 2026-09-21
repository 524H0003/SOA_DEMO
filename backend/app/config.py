from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Absent Request API"
    database_url: str = "sqlite:///./absent_requests.db"
    frontend_origin: str = "http://localhost:5173"
    gmail_sender: str = ""
    manager_email: str = ""
    gmail_credentials_file: str = ""
    gmail_credentials_json: str = ""
    gmail_credentials_json_base64: str = ""
    gmail_token_file: str = "gmail-token.json"
    gmail_token_json_base64: str = ""
    email_template_file: str = "templates/absent_request.html"
    pubsub_audience: str = ""
    pubsub_oidc_audience: str = ""
    pubsub_oidc_topic: str = ""
    pubsub_service_account_email: str = ""
    public_api_url: str = "http://localhost:8000"


@lru_cache
def get_settings() -> Settings:
    return Settings()
