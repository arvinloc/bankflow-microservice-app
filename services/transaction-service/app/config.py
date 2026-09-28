from pathlib import Path

import pydantic_settings
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parent.parent / ".env"
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")


    database_url: str
    keycloak_issuer: str
    keycloak_jwks_url: str
    keycloak_audience: str = "bank-api"

    keycloak_token_url: str
    keycloak_client_id: str = "transaction-service"
    keycloak_client_secret: str
    accounts_service_url: str


settings = Settings()


