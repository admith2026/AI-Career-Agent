from shared.config import BaseServiceSettings


class CrawlerSettings(BaseServiceSettings):
    service_name: str = "job-discovery"
    service_port: int = 5001

    interval_hours: int = 3
    max_concurrent_crawlers: int = 3
    request_delay_seconds: float = 2.0
    user_agent: str = "CareerAgent/1.0 (Job Discovery Bot)"

    search_keywords: list[str] = [
        ".NET Developer",
        "C# Developer",
        "ASP.NET Core",
        ".NET Full Stack Developer",
        "Blazor Developer",
        "Azure .NET Developer",
    ]
    filters: list[str] = ["Remote", "Contract", "Freelance"]


settings = CrawlerSettings()
