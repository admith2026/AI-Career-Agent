"""RemoteOK.com JSON API crawler."""

import logging
from datetime import datetime
from urllib.parse import quote_plus

from .base import BaseCrawler, CrawledJob

logger = logging.getLogger(__name__)


class RemoteOKCrawler(BaseCrawler):
    source = "RemoteOK"
    _BASE_URL = "https://remoteok.com/api"

    async def crawl(self, keywords: list[str]) -> list[CrawledJob]:
        jobs: list[CrawledJob] = []
        try:
            # RemoteOK returns JSON with all remote jobs; first element is metadata
            for kw in keywords:
                tag = quote_plus(kw.lower().replace(" ", "-"))
                url = f"{self._BASE_URL}?tag={tag}"
                resp = await self._fetch(url)
                data = resp.json()
                for item in data:
                    if not isinstance(item, dict) or "id" not in item:
                        continue
                    jobs.append(self._parse(item))
        except Exception:
            logger.exception("RemoteOK crawl failed")
        return jobs

    def _parse(self, item: dict) -> CrawledJob:
        date_posted = None
        if item.get("date"):
            try:
                date_posted = datetime.fromisoformat(item["date"].replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass

        return CrawledJob(
            external_id=self.make_external_id(self.source, str(item["id"])),
            source=self.source,
            job_title=item.get("position", ""),
            company_name=item.get("company", ""),
            job_description=item.get("description", ""),
            job_link=f"https://remoteok.com/remote-jobs/{item['slug']}" if item.get("slug") else item.get("url", ""),
            salary_or_rate=item.get("salary", ""),
            location=item.get("location", "Remote"),
            is_remote=True,
            contract_type="Contract" if "contract" in (item.get("tags") or []) else None,
            date_posted=date_posted,
            raw_data=item,
        )
