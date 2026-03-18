from shared.config import BaseServiceSettings


class SubscriptionSettings(BaseServiceSettings):
    service_name: str = "subscription"
    service_port: int = 5018
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""


settings = SubscriptionSettings()
