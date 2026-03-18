from shared.config import BaseServiceSettings


class MarketplaceSettings(BaseServiceSettings):
    service_name: str = "marketplace"
    service_port: int = 5019


settings = MarketplaceSettings()
