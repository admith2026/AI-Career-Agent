"""Dice.com job search scraper."""

import logging
from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from .base import BaseCrawler, CrawledJob

logger = logging.getLogger(__name__)


class DiceCrawler(BaseCrawler):
    source = "Dice"
    _BASE_URL = "https://www.dice.com"

    async def crawl(self, keywords: list[str]) -> list[CrawledJob]:
        jobs: list[CrawledJob] = []
        try:
            for kw in keywords:
                url = (
                    f"{self._BASE_URL}/jobs"
                    f"?q={quote_plus(kw)}"
                    f"&filters.isRemote=true"
                    f"&filters.employmentType=CONTRACTS"
                    f"&page=1&pageSize=20"
                )
                resp = await self._fetch(url)
                soup = BeautifulSoup(resp.text, "lxml")
                for card in soup.select("dhi-search-card, div.card"):
                    parsed = self._parse_card(card)
                    if parsed:
                        jobs.append(parsed)
        except Exception:
            logger.exception("Dice crawl failed")
        return jobs

    def _parse_card(self, card) -> CrawledJob | None:
        title_el = card.select_one("a.card-title-link, h5 a")
        if not title_el:
            return None
        title = title_el.get_text(strip=True)
        href = title_el.get("href", "")
        if not href:
            return None
        full_link = f"{self._BASE_URL}{href}" if href.startswith("/") else href

        company_el = card.select_one("a[data-cy='search-result-company-name'], span.card-company")
        location_el = card.select_one("span.search-result-location, span.card-location")

        company = company_el.get_text(strip=True) if company_el else ""
        location = location_el.get_text(strip=True) if location_el else "Remote"

        return CrawledJob(
            external_id=self.make_external_id(self.source, href),
            source=self.source,
            job_title=title,
            company_name=company,
            job_link=full_link,
            location=location,
            is_remote=True,
            contract_type="Contract",
            raw_data={"href": href},
        )
