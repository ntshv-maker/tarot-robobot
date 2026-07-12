from __future__ import annotations

from functools import lru_cache
from zoneinfo import ZoneInfo

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    bot_token: str = Field(alias="BOT_TOKEN")
    local_dev: bool = Field(default=False, alias="LOCAL_DEV")
    database_url: str = Field(
        default="postgresql+asyncpg://astorobot:astorobot@localhost:5432/astorobot",
        alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

    kie_api_key: str = Field(default="", alias="KIE_API_KEY")
    kie_api_url: str = Field(
        default="https://api.kie.ai/gemini-2.5-pro/v1/chat/completions",
        alias="KIE_API_URL",
    )
    kie_model: str = Field(default="gemini-2.5-pro", alias="KIE_MODEL")
    kie_reasoning_effort: str = Field(default="high", alias="KIE_REASONING_EFFORT")

    usd_to_rub_rate: float = Field(default=95.0, alias="USD_TO_RUB_RATE")
    llm_input_usd_per_1m: float = Field(default=1.25, alias="LLM_INPUT_USD_PER_1M")
    llm_output_usd_per_1m: float = Field(default=10.0, alias="LLM_OUTPUT_USD_PER_1M")
    llm_input_usd_per_1m_long: float = Field(default=2.5, alias="LLM_INPUT_USD_PER_1M_LONG")
    llm_output_usd_per_1m_long: float = Field(default=15.0, alias="LLM_OUTPUT_USD_PER_1M_LONG")
    llm_long_context_threshold: int = Field(default=200_000, alias="LLM_LONG_CONTEXT_THRESHOLD")

    admin_ids: str = Field(default="", alias="ADMIN_IDS")
    referral_bot_username: str = Field(default="", alias="REFERRAL_BOT_USERNAME")

    dashboard_password: str = Field(default="", alias="DASHBOARD_PASSWORD")
    dashboard_secret: str = Field(default="change-me-astorobot-dashboard", alias="DASHBOARD_SECRET")
    dashboard_host: str = Field(default="127.0.0.1", alias="DASHBOARD_HOST")
    dashboard_port: int = Field(default=8080, alias="DASHBOARD_PORT")

    privacy_policy_url: str = Field(default="https://example.com/privacy", alias="PRIVACY_POLICY_URL")
    consent_url: str = Field(default="https://example.com/consent", alias="CONSENT_URL")
    offer_url: str = Field(default="https://example.com/offer", alias="OFFER_URL")

    typing_sticker_id: str = Field(default="", alias="TYPING_STICKER_ID")
    timezone: str = Field(default="Europe/Moscow", alias="TIMEZONE")

    morning_digest_hour: int = Field(default=8, alias="MORNING_DIGEST_HOUR")
    evening_digest_hour: int = Field(default=20, alias="EVENING_DIGEST_HOUR")
    weekly_horoscope_hour: int = Field(default=9, alias="WEEKLY_HOROSCOPE_HOUR")

    @property
    def use_memory_backend(self) -> bool:
        return self.local_dev or self.redis_url.startswith("memory://")

    @property
    def tz(self) -> ZoneInfo:
        return ZoneInfo(self.timezone)

    @property
    def admin_id_list(self) -> list[int]:
        if not self.admin_ids.strip():
            return []
        return [int(x.strip()) for x in self.admin_ids.split(",") if x.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
