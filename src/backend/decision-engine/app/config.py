"""Decision Engine configuration."""

from pydantic_settings import BaseSettings


class DecisionEngineSettings(BaseSettings):
    database_url: str = "postgresql+asyncpg://career:changeme@localhost:5432/career_agent"
    rabbitmq_url: str = "amqp://career:changeme@localhost:5672/"
    redis_url: str = "redis://localhost:6379/9"

    # Scoring thresholds
    auto_apply_min_score: int = 80
    outreach_min_score: int = 60
    signal_boost_max: int = 15

    # External service URLs
    resume_generator_url: str = "http://resume-generator:5003"
    application_automation_url: str = "http://application-automation:5004"
    knowledge_graph_url: str = "http://knowledge-graph:5008"

    class Config:
        env_prefix = ""


settings = DecisionEngineSettings()
