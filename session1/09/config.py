
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="AGENT_",
        extra="ignore",
    )

    model: str = "qwen3:4b"
    max_steps: int = Field(default=5, ge=1, le=30)
    tool_timeout: float = Field(default=5, gt=0)
    log_level: str = "INFO"


settings = Settings()
