from shared.config import BaseServiceSettings


class NotificationSettings(BaseServiceSettings):
    service_name: str = "notifications"
    service_port: int = 5005

    # Telegram Bot API
    telegram_bot_token: str = ""

    # WhatsApp Cloud API (Meta)
    whatsapp_api_url: str = "https://graph.facebook.com/v18.0"
    whatsapp_phone_number_id: str = ""
    whatsapp_access_token: str = ""

    # SMTP for email notifications
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_name: str = "AI Career Agent"

    # Scheduled report times (UTC hours)
    morning_report_hour: int = 8
    evening_report_hour: int = 19


settings = NotificationSettings()
