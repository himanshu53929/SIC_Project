from typing import Optional

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )

    # Type hinted Settings
    secret_key: SecretStr
    usda_api_key: Optional[SecretStr] = None
    algorithm: str = "HS256" # Standard algo. for JSON Web Tokens
    access_token_expire_minutes: int = 30


settings = Settings()