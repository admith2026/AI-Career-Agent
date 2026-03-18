from shared.config import BaseServiceSettings


class AgentOrchestratorSettings(BaseServiceSettings):
    service_name: str = "agent-orchestrator"
    service_port: int = 5017

    # Downstream agent service URLs
    job_discovery_url: str = "http://localhost:5001"
    job_intelligence_url: str = "http://localhost:5002"
    resume_generator_url: str = "http://localhost:5003"
    application_automation_url: str = "http://localhost:5004"
    linkedin_automation_url: str = "http://localhost:5011"
    voice_ai_url: str = "http://localhost:5012"
    interview_ai_url: str = "http://localhost:5013"
    negotiation_ai_url: str = "http://localhost:5014"

    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"


settings = AgentOrchestratorSettings()
