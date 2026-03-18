"""Seed default crawler sources into the database."""

from sqlalchemy import select
from shared.models import CrawlerSource

DEFAULT_SOURCES = [
    {"name": "remoteok", "source_type": "http", "url_pattern": "https://remoteok.com/api", "crawl_frequency_minutes": 15, "priority": 9},
    {"name": "weworkremotely", "source_type": "http", "url_pattern": "https://weworkremotely.com/remote-jobs/search?term=.net", "crawl_frequency_minutes": 30, "priority": 8},
    {"name": "github_jobs", "source_type": "github", "url_pattern": "hiring .NET remote contract", "crawl_frequency_minutes": 60, "priority": 7},
    {"name": "reddit_hiring", "source_type": "reddit", "url_pattern": "https://www.reddit.com/r/forhire", "crawl_frequency_minutes": 30, "priority": 6},
    {"name": "techcrunch_signals", "source_type": "signal", "url_pattern": "https://techcrunch.com/category/startups/", "crawl_frequency_minutes": 60, "priority": 8},
    {"name": "hn_whoishiring", "source_type": "http", "url_pattern": "https://news.ycombinator.com/item?id=39562986", "crawl_frequency_minutes": 120, "priority": 7},
    {"name": "dice_dotnet", "source_type": "http", "url_pattern": "https://www.dice.com/jobs?q=.NET+Core&countryCode=US&radius=30&radiusUnit=mi&page=1&pageSize=20&filters.isRemote=true", "crawl_frequency_minutes": 30, "priority": 8},
    {"name": "indeed_remote", "source_type": "http", "url_pattern": "https://www.indeed.com/jobs?q=.net+core+remote+contract&sort=date", "crawl_frequency_minutes": 30, "priority": 8, "anti_bot_level": "medium"},
    {"name": "linkedin_signals", "source_type": "signal", "url_pattern": "https://www.linkedin.com/pulse/", "crawl_frequency_minutes": 120, "priority": 5, "requires_js": True, "anti_bot_level": "high"},
]


async def seed_default_sources(db):
    """Seed default sources if they don't exist."""
    for src in DEFAULT_SOURCES:
        existing = await db.execute(
            select(CrawlerSource).where(CrawlerSource.name == src["name"])
        )
        if existing.scalar_one_or_none():
            continue

        source = CrawlerSource(
            name=src["name"],
            source_type=src["source_type"],
            url_pattern=src["url_pattern"],
            crawl_frequency_minutes=src.get("crawl_frequency_minutes", 60),
            priority=src.get("priority", 5),
            requires_js=src.get("requires_js", False),
            anti_bot_level=src.get("anti_bot_level", "low"),
        )
        db.add(source)

    await db.commit()
