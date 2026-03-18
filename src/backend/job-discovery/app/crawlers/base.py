"""Base crawler interface and shared utilities."""

import abc
import asyncio
import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import httpx

logger = logging.getLogger(__name__)


@dataclass
class CrawledJob:
    """Normalised job record coming out of any crawler."""

    external_id: str
    source: str
    job_title: str
    company_name: str | None = None
    vendor_name: str | None = None
    recruiter_name: str | None = None
    recruiter_email: str | None = None
    phone_number: str | None = None
    job_description: str | None = None
    job_link: str = ""
    salary_or_rate: str | None = None
    location: str | None = None
    is_remote: bool = True
    contract_type: str | None = None
    date_posted: datetime | None = None
    raw_data: dict[str, Any] = field(default_factory=dict)


class BaseCrawler(abc.ABC):
    """Abstract base class for all job-board crawlers."""

    source: str = "unknown"

    def __init__(self, delay_seconds: float = 2.0, user_agent: str = "CareerAgent/1.0"):
        self._delay = delay_seconds
        self._headers = {
            "User-Agent": user_agent,
            "Accept": "text/html,application/json",
        }
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                headers=self._headers, timeout=30.0, follow_redirects=True
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def _fetch(self, url: str) -> httpx.Response:
        client = await self._get_client()
        await asyncio.sleep(self._delay)
        response = await client.get(url)
        response.raise_for_status()
        return response

    @abc.abstractmethod
    async def crawl(self, keywords: list[str]) -> list[CrawledJob]:
        """Crawl the job board and return normalised job records."""
        ...

    @staticmethod
    def make_external_id(source: str, unique_input: str) -> str:
        return hashlib.sha256(f"{source}:{unique_input}".encode()).hexdigest()[:64]
