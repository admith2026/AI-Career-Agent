"""LinkedIn job search scraper (public listing pages)."""

import logging
from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from .base import BaseCrawler, CrawledJob

logger = logging.getLogger(__name__)


class LinkedInCrawler(BaseCrawler):
    source = "LinkedIn"
    _BASE_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"

    async def crawl(self, keywords: list[str]) -> list[CrawledJob]:
        jobs: list[CrawledJob] = []
        try:
            for kw in keywords:
                url = (
                    f"{self._BASE_URL}"
                    f"?keywords={quote_plus(kw)}"
                    f"&f_WT=2"  # Remote filter
                    f"&f_JT=C"  # Contract type
                    f"&start=0"
                )
                resp = await self._fetch(url)
                soup = BeautifulSoup(resp.text, "lxml")
                for card in soup.select("li"):
                    parsed = self._parse_card(card)
                    if parsed:
                        jobs.append(parsed)
        except Exception:
            logger.exception("LinkedIn crawl failed")
        return jobs

    def _parse_card(self, card) -> CrawledJob | None:
        link_tag = card.select_one("a.base-card__full-link, a[href*='linkedin.com/jobs/view']")
        if not link_tag:
            return None
        href = link_tag.get("href", "").split("?")[0]
        if not href:
            return None

        title_el = card.select_one(".base-search-card__title")
        company_el = card.select_one(".base-search-card__subtitle a")
        location_el = card.select_one(".job-search-card__location")

        title = title_el.get_text(strip=True) if title_el else ""
        company = company_el.get_text(strip=True) if company_el else ""
        location = location_el.get_text(strip=True) if location_el else "Remote"

        if not title:
            return None

        return CrawledJob(
            external_id=self.make_external_id(self.source, href),
            source=self.source,
            job_title=title,
            company_name=company,
            job_link=href,
            location=location,
            is_remote="remote" in location.lower(),
            contract_type="Contract",
            raw_data={"href": href},
        )
