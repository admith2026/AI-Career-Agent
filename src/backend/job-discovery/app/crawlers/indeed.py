"""Indeed.com job search scraper."""

import logging
from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from .base import BaseCrawler, CrawledJob

logger = logging.getLogger(__name__)


class IndeedCrawler(BaseCrawler):
    source = "Indeed"
    _BASE_URL = "https://www.indeed.com"

    async def crawl(self, keywords: list[str]) -> list[CrawledJob]:
        jobs: list[CrawledJob] = []
        try:
            for kw in keywords:
                url = (
                    f"{self._BASE_URL}/jobs"
                    f"?q={quote_plus(kw)}"
                    f"&l=Remote"
                    f"&jt=contract"
                    f"&sort=date"
                    f"&fromage=3"  # Last 3 days
                )
                resp = await self._fetch(url)
                soup = BeautifulSoup(resp.text, "lxml")
                for card in soup.select("div.job_seen_beacon, div.cardOutline"):
                    parsed = self._parse_card(card)
                    if parsed:
                        jobs.append(parsed)
        except Exception:
            logger.exception("Indeed crawl failed")
        return jobs

    def _parse_card(self, card) -> CrawledJob | None:
        title_el = card.select_one("h2.jobTitle a, a.jcs-JobTitle")
        if not title_el:
            return None
        title = title_el.get_text(strip=True)
        href = title_el.get("href", "")
        if not href:
            return None

        full_link = f"{self._BASE_URL}{href}" if href.startswith("/") else href
        jk = title_el.get("data-jk", href)

        company_el = card.select_one("[data-testid='company-name'], span.companyName")
        location_el = card.select_one("[data-testid='text-location'], div.companyLocation")
        salary_el = card.select_one("div.salary-snippet-container, div.metadata.salary-snippet-container")

        company = company_el.get_text(strip=True) if company_el else ""
        location = location_el.get_text(strip=True) if location_el else "Remote"
        salary = salary_el.get_text(strip=True) if salary_el else ""

        return CrawledJob(
            external_id=self.make_external_id(self.source, str(jk)),
            source=self.source,
            job_title=title,
            company_name=company,
            job_link=full_link,
            salary_or_rate=salary,
            location=location,
            is_remote="remote" in location.lower(),
            contract_type="Contract",
            raw_data={"jk": jk, "href": href},
        )
