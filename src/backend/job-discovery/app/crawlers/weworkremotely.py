"""WeWorkRemotely.com HTML scraper."""

import logging
from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from .base import BaseCrawler, CrawledJob

logger = logging.getLogger(__name__)


class WeWorkRemotelyCrawler(BaseCrawler):
    source = "WeWorkRemotely"
    _BASE_URL = "https://weworkremotely.com"

    async def crawl(self, keywords: list[str]) -> list[CrawledJob]:
        jobs: list[CrawledJob] = []
        try:
            for kw in keywords:
                url = f"{self._BASE_URL}/remote-jobs/search?term={quote_plus(kw)}"
                resp = await self._fetch(url)
                soup = BeautifulSoup(resp.text, "lxml")
                for article in soup.select("li.feature, li:not(.ad)"):
                    link_tag = article.select_one("a[href*='/remote-jobs/']")
                    if not link_tag:
                        continue
                    parsed = self._parse_listing(article, link_tag)
                    if parsed:
                        jobs.append(parsed)
        except Exception:
            logger.exception("WeWorkRemotely crawl failed")
        return jobs

    def _parse_listing(self, article, link_tag) -> CrawledJob | None:
        href = link_tag.get("href", "")
        if not href:
            return None
        full_link = f"{self._BASE_URL}{href}" if href.startswith("/") else href

        title_el = article.select_one(".title")
        company_el = article.select_one(".company")

        title = title_el.get_text(strip=True) if title_el else link_tag.get_text(strip=True)
        company = company_el.get_text(strip=True) if company_el else ""

        if not title:
            return None

        return CrawledJob(
            external_id=self.make_external_id(self.source, href),
            source=self.source,
            job_title=title,
            company_name=company,
            job_link=full_link,
            location="Remote",
            is_remote=True,
            raw_data={"href": href},
        )
