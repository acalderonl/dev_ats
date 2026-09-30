from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://ats_user:ats_password@db:5432/ats_db"
    secret_key: str = "supersecretkey_ats_2026"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 12

    linkedin_client_id: str = "mock_client_id"
    linkedin_client_secret: str = "mock_client_secret"

    frontend_origin: str = "http://localhost:3000"

    default_admin_email: str = "admin@atsdemo.com"
    default_admin_password: str = "Admin123!"


@lru_cache
def get_settings() -> Settings:
    return Settings()
