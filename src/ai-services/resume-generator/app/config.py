from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://career_agent:career_agent_pwd@localhost:5432/career_agent"
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    service_name: str = "resume-generator"
    service_port: int = 5003

    class Config:
        env_file = ".env"


settings = Settings()
