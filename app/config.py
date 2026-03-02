from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="Trust Index API", alias="APP_NAME")
    api_prefix: str = Field(default="/api/v1", alias="API_PREFIX")

    database_url: str = Field(
        validation_alias=AliasChoices("DATABASE_URL", "SUPABASE_DB_URL", "MYSQL_URL"),
    )
    db_auto_create: bool = Field(default=False, alias="DB_AUTO_CREATE")

    ollama_base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="llama3.2", alias="OLLAMA_MODEL")
    ollama_timeout_seconds: int = Field(default=45, alias="OLLAMA_TIMEOUT_SECONDS")
    ai_max_retries: int = Field(default=2, alias="AI_MAX_RETRIES")

    impulse_income_pct: float = Field(default=0.12, alias="IMPULSE_INCOME_PCT")
    discretionary_deviation_multiplier: float = Field(default=1.8, alias="DISCRETIONARY_DEVIATION_MULTIPLIER")

    commitment_on_time_grace_days: int = Field(default=4, alias="COMMITMENT_ON_TIME_GRACE_DAYS")

    emergency_shock_income_pct: float = Field(default=0.15, alias="EMERGENCY_SHOCK_INCOME_PCT")
    recovery_cap_months: int = Field(default=6, alias="RECOVERY_CAP_MONTHS")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
