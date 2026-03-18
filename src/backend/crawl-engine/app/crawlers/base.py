"""Base crawler interface and data classes."""

import abc
import hashlib
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class CrawledItem:
    """A single item extracted from a web page."""
    source: str
    item_type: str  # job, signal, company, recruiter
    url: str
    title: str
    raw_html: str = ""
    extracted_data: dict = field(default_factory=dict)
    external_id: str = ""
    discovered_at: datetime = field(default_factory=datetime.utcnow)
    date_posted: datetime | None = None

    @property
    def content_hash(self) -> str:
        return hashlib.sha256(f"{self.source}:{self.url}:{self.title}".encode()).hexdigest()


class BaseCrawler(abc.ABC):
    """Abstract base for all crawlers."""

    name: str = "base"
    source_type: str = "unknown"
    requires_js: bool = False

    @abc.abstractmethod
    async def crawl(self, url: str, **kwargs) -> list[CrawledItem]:
        """Crawl a URL and return extracted items."""
        ...

    @abc.abstractmethod
    async def parse(self, html: str, url: str) -> list[CrawledItem]:
        """Parse HTML content into structured items."""
        ...
