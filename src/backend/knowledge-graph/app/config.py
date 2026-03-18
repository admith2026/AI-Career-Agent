"""Knowledge Graph configuration."""

from pydantic_settings import BaseSettings


class KnowledgeGraphSettings(BaseSettings):
    database_url: str = "postgresql+asyncpg://career:changeme@localhost:5432/career_agent"
    rabbitmq_url: str = "amqp://career:changeme@localhost:5672/"
    redis_url: str = "redis://localhost:6379/8"

    # Neo4j
    neo4j_uri: str = "bolt://neo4j:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "changeme"

    class Config:
        env_prefix = ""


settings = KnowledgeGraphSettings()
