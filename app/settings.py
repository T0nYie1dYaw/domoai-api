import os
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=os.environ.get('ENV_FILE', '.env'), env_file_encoding='utf-8')
    discord_token: str
    discord_guild_id: int
    discord_channel_id: int

    domoai_application_id: int = 1153984868804468756

    redis_uri: Optional[str] = None

    event_callback_url: Optional[str] = None

    cache_prefix: str = 'domoai:'

    api_auth_token: Optional[str] = None


@lru_cache()
def get_settings() -> Settings:
    return Settings()
