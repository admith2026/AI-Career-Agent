from shared.config import BaseServiceSettings


class GatewaySettings(BaseServiceSettings):
    service_name: str = "api-gateway"
    service_port: int = 5000

    # Downstream service URLs
    job_discovery_url: str = "http://localhost:5001"
    job_intelligence_url: str = "http://localhost:5002"
    resume_generator_url: str = "http://localhost:5003"
    application_automation_url: str = "http://localhost:5004"
    notifications_url: str = "http://localhost:5005"
    crawl_engine_url: str = "http://localhost:5006"
    data_pipeline_url: str = "http://localhost:5007"
    knowledge_graph_url: str = "http://localhost:5008"
    decision_engine_url: str = "http://localhost:5009"

    # Blackhole services
    predictive_ai_url: str = "http://localhost:5010"
    linkedin_automation_url: str = "http://localhost:5011"
    voice_ai_url: str = "http://localhost:5012"
    interview_ai_url: str = "http://localhost:5013"
    negotiation_ai_url: str = "http://localhost:5014"
    freelance_bidding_url: str = "http://localhost:5015"
    demand_generation_url: str = "http://localhost:5016"

    # SaaS services
    agent_orchestrator_url: str = "http://localhost:5017"
    subscription_url: str = "http://localhost:5018"
    marketplace_url: str = "http://localhost:5019"

    # CORS origins
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:19006"]

    # Webhook secret for n8n integration
    webhook_secret: str = ""


settings = GatewaySettings()
