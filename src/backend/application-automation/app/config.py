from shared.config import BaseServiceSettings


class AutomationSettings(BaseServiceSettings):
    service_name: str = "application-automation"
    service_port: int = 5004

    # Resume Generator service
    resume_generator_url: str = "http://localhost:5003"

    # SMTP settings for email applications
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_name: str = "Career Agent"

    # Auto-apply settings
    max_daily_applications: int = 10
    min_score_for_auto_apply: int = 70


settings = AutomationSettings()
