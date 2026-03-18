"""Signal crawler — detects hiring signals from news, blogs, funding sites."""

import logging
import re
from bs4 import BeautifulSoup
import httpx
from fake_useragent import UserAgent

from .base import BaseCrawler, CrawledItem
from app.config import settings

logger = logging.getLogger(__name__)
ua = UserAgent()

# Patterns that indicate hiring signals
SIGNAL_PATTERNS = [
    (r"(?:raised?|secures?|closes?)\s+\$[\d.]+[MBK]\b", "funding_round"),
    (r"\b(?:series\s+[A-F]|seed\s+round|funding\s+round)\b", "funding_round"),
    (r"\bhiring\s+(?:\d+|\w+)\s+(?:engineers?|developers?|people)\b", "team_expansion"),
    (r"\bwe(?:'re| are)\s+(?:hiring|growing|expanding)\b", "team_expansion"),
    (r"\b(?:launch(?:es|ed|ing)?|announc(?:es|ed|ing)?)\s+(?:new|their)\s+(?:product|platform|service)\b", "product_launch"),
    (r"\b(?:acquir(?:es|ed|ing)|merger|acquisition)\b", "acquisition"),
    (r"\b(?:IPO|going\s+public|S-1\s+filing)\b", "ipo_filing"),
    (r"\bnew\s+(?:CTO|VP\s+of\s+Engineering|Head\s+of|Chief)\b", "exec_hire"),
    (r"\b(?:opens?\s+(?:new\s+)?office|expands?\s+to)\b", "expansion"),
]


class SignalCrawler(BaseCrawler):
    """Detects hiring signals from news, blogs, and funding announcements."""

    name = "signal_crawler"
    source_type = "signal"
    requires_js = False

    async def crawl(self, url: str, **kwargs) -> list[CrawledItem]:
        source_name = kwargs.get("source_name", "unknown")
        headers = {"User-Agent": ua.random}

        try:
            async with httpx.AsyncClient(
                timeout=settings.request_timeout_seconds,
                follow_redirects=True,
            ) as client:
                resp = await client.get(url, headers=headers)
                resp.raise_for_status()
                return await self.parse(resp.text, url, source_name=source_name)
        except Exception as e:
            logger.error(f"Signal crawl failed for {url}: {e}")
            return []

    async def parse(self, html: str, url: str, **kwargs) -> list[CrawledItem]:
        source_name = kwargs.get("source_name", "unknown")
        soup = BeautifulSoup(html, "lxml")
        items: list[CrawledItem] = []

        # Extract articles / posts
        for article in soup.find_all(["article", "div"], class_=lambda c: c and any(
            k in str(c).lower() for k in ["post", "article", "entry", "story", "news", "item"]
        )):
            title_el = article.find(["h1", "h2", "h3", "a"])
            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            body = article.get_text(separator=" ", strip=True)[:5000]

            if not title or len(title) < 10:
                continue

            # Check for hiring signal patterns
            full_text = f"{title} {body}".lower()
            detected_signals = []
            for pattern, signal_type in SIGNAL_PATTERNS:
                if re.search(pattern, full_text, re.IGNORECASE):
                    detected_signals.append(signal_type)

            if not detected_signals:
                continue

            link = ""
            link_el = article.find("a", href=True)
            if link_el:
                link = link_el["href"]
                if not link.startswith("http"):
                    from urllib.parse import urljoin
                    link = urljoin(url, link)

            # Try to extract company name from title
            company_name = self._extract_company(title, body)

            items.append(CrawledItem(
                source=source_name,
                item_type="signal",
                url=link or url,
                title=title,
                raw_html=str(article)[:5000],
                extracted_data={
                    "signal_types": detected_signals,
                    "company_name": company_name,
                    "description": body[:2000],
                    "confidence": min(0.3 + 0.15 * len(detected_signals), 0.95),
                },
            ))

        logger.info(f"Signal crawler found {len(items)} signals from {url}")
        return items

    @staticmethod
    def _extract_company(title: str, body: str) -> str:
        """Heuristic company name extraction from signal text."""
        # Look for patterns like "CompanyName raises..." or "CompanyName announces..."
        match = re.match(r"^([A-Z][A-Za-z0-9.]+(?:\s+[A-Z][A-Za-z0-9.]+){0,3})\s+(?:raises?|secures?|closes?|announc|launch|hir|acquir|opens?|expands?)", title)
        if match:
            return match.group(1).strip()
        return ""
