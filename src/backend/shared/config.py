from pydantic_settings import BaseSettings


class BaseServiceSettings(BaseSettings):
    """Base settings shared by all services."""

    # Database
    database_url: str = "postgresql+asyncpg://career_agent:career_agent_pwd@localhost:5432/career_agent"
    database_url_sync: str = "postgresql://career_agent:career_agent_pwd@localhost:5432/career_agent"

    # RabbitMQ
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # JWT
    jwt_secret: str = "YourSuperSecretKeyThatIsLongEnoughForHS256Algorithm!"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 1440

    # API Keys
    openai_api_key: str = ""
    jsearch_api_key: str = ""

    # Telegram
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    # Email
    email_user: str = ""
    email_pass: str = ""

    # Twilio
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    whatsapp_to_number: str = ""

    class Config:
        env_file = ".env"
        extra = "allow"
