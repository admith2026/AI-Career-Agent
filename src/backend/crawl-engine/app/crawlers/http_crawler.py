"""HTTP-based crawler using httpx + BeautifulSoup for static pages."""

import logging
import re
from datetime import datetime, timedelta, timezone
from bs4 import BeautifulSoup
import httpx
from fake_useragent import UserAgent

from .base import BaseCrawler, CrawledItem
from app.config import settings

logger = logging.getLogger(__name__)
ua = UserAgent()


class HttpCrawler(BaseCrawler):
    """Crawler for static HTML pages — job boards, career pages, news."""

    name = "http_crawler"
    source_type = "http"
    requires_js = False

    def __init__(self):
        self._proxies = self._load_proxies()
        self._proxy_index = 0

    def _load_proxies(self) -> list[str]:
        if settings.proxy_list:
            return [p.strip() for p in settings.proxy_list.split(",") if p.strip()]
        return []

    def _get_proxy(self) -> str | None:
        if not self._proxies or not settings.proxy_rotation_enabled:
            return None
        proxy = self._proxies[self._proxy_index % len(self._proxies)]
        self._proxy_index += 1
        return proxy

    async def crawl(self, url: str, **kwargs) -> list[CrawledItem]:
        source_name = kwargs.get("source_name", "unknown")
        headers = {"User-Agent": ua.random, "Accept-Language": "en-US,en;q=0.9"}
        proxy = self._get_proxy()

        try:
            async with httpx.AsyncClient(
                timeout=settings.request_timeout_seconds,
                proxy=proxy,
                follow_redirects=True,
            ) as client:
                resp = await client.get(url, headers=headers)
                resp.raise_for_status()
                return await self.parse(resp.text, url, source_name=source_name)
        except Exception as e:
            logger.error(f"HTTP crawl failed for {url}: {e}")
            return []

    async def parse(self, html: str, url: str, **kwargs) -> list[CrawledItem]:
        source_name = kwargs.get("source_name", "unknown")
        soup = BeautifulSoup(html, "lxml")
        items: list[CrawledItem] = []

        # Generic job listing extraction heuristic
        for article in soup.find_all(["article", "div", "li"], class_=lambda c: c and any(
            k in str(c).lower() for k in ["job", "listing", "posting", "position", "vacancy"]
        )):
            title_el = article.find(["h2", "h3", "h4", "a"])
            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            link = title_el.get("href", "") if title_el.name == "a" else ""
            if not link:
                link_el = article.find("a")
                link = link_el.get("href", "") if link_el else ""

            if not title or len(title) < 5:
                continue

            # Resolve relative URLs
            if link and not link.startswith("http"):
                from urllib.parse import urljoin
                link = urljoin(url, link)

            company_el = article.find(class_=lambda c: c and "company" in str(c).lower())
            company = company_el.get_text(strip=True) if company_el else ""

            location_el = article.find(class_=lambda c: c and "location" in str(c).lower())
            location = location_el.get_text(strip=True) if location_el else ""

            items.append(CrawledItem(
                source=source_name,
                item_type="job",
                url=link or url,
                title=title,
                raw_html=str(article)[:5000],
                extracted_data={
                    "company_name": company,
                    "location": location,
                    "job_description": article.get_text(separator="\n", strip=True)[:3000],
                },
                date_posted=self._extract_date(article),
            ))

        logger.info(f"HTTP crawler extracted {len(items)} items from {url}")
        return items

    @staticmethod
    def _extract_date(element) -> datetime | None:
        """Try to extract a posting date from an HTML element."""
        # Check <time> tags
        time_el = element.find("time")
        if time_el:
            for attr in ("datetime", "content"):
                val = time_el.get(attr, "")
                if val:
                    try:
                        return datetime.fromisoformat(val.replace("Z", "+00:00"))
                    except ValueError:
                        pass
            text = time_el.get_text(strip=True)
            parsed = HttpCrawler._parse_relative_date(text)
            if parsed:
                return parsed

        # Check elements with date-like classes
        date_el = element.find(class_=lambda c: c and any(
            k in str(c).lower() for k in ["date", "time", "posted", "ago"]
        ))
        if date_el:
            parsed = HttpCrawler._parse_relative_date(date_el.get_text(strip=True))
            if parsed:
                return parsed

        return None

    @staticmethod
    def _parse_relative_date(text: str) -> datetime | None:
        """Parse relative date strings like '2 days ago', '3h ago'."""
        text = text.lower().strip()
        now = datetime.now(timezone.utc)
        m = re.search(r'(\d+)\s*(second|minute|hour|day|week|month)s?\s*ago', text)
        if m:
            n, unit = int(m.group(1)), m.group(2)
            deltas = {"second": 1, "minute": 60, "hour": 3600, "day": 86400, "week": 604800, "month": 2592000}
            return now - timedelta(seconds=n * deltas.get(unit, 86400))
        # Try ISO format
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%b %d, %Y", "%d %b %Y"):
            try:
                return datetime.strptime(text, fmt).replace(tzinfo=timezone.utc)
            except ValueError:
                continue
        return None
