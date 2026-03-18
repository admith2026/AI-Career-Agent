from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://career_agent:career_agent_pwd@localhost:5432/career_agent"

    # RabbitMQ
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # Qdrant Vector DB
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection: str = "job_embeddings"

    # Service
    service_name: str = "job-intelligence"
    service_port: int = 5002

    class Config:
        env_file = ".env"


settings = Settings()
