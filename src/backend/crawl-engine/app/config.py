"""Crawl Engine configuration."""

from pydantic_settings import BaseSettings


class CrawlEngineSettings(BaseSettings):
    database_url: str = "postgresql+asyncpg://career:changeme@localhost:5432/career_agent"
    rabbitmq_url: str = "amqp://career:changeme@localhost:5672/"
    redis_url: str = "redis://localhost:6379/6"

    # Crawling config
    max_concurrent_crawlers: int = 10
    request_delay_seconds: float = 1.5
    request_timeout_seconds: int = 30
    max_retries: int = 3
    proxy_rotation_enabled: bool = False
    proxy_list: str = ""  # comma-separated proxy URLs

    # Playwright
    playwright_headless: bool = True
    playwright_timeout_ms: int = 30000

    # Worker identity
    worker_id: str = "crawl-worker-1"

    class Config:
        env_prefix = ""


settings = CrawlEngineSettings()
