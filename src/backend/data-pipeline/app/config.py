"""Data Pipeline configuration."""

from pydantic_settings import BaseSettings


class PipelineSettings(BaseSettings):
    database_url: str = "postgresql+asyncpg://career:changeme@localhost:5432/career_agent"
    rabbitmq_url: str = "amqp://career:changeme@localhost:5672/"
    redis_url: str = "redis://localhost:6379/7"

    # Pipeline config
    dedup_ttl_hours: int = 72
    batch_size: int = 50
    processing_interval_seconds: int = 5

    # Downstream service URLs
    job_intelligence_url: str = "http://job-intelligence:5002"

    class Config:
        env_prefix = ""


settings = PipelineSettings()
