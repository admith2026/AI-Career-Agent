"""GitHub crawler — finds hiring signals from repos, orgs, and job postings."""

import logging
from datetime import datetime
import httpx
from fake_useragent import UserAgent

from .base import BaseCrawler, CrawledItem
from app.config import settings

logger = logging.getLogger(__name__)
ua = UserAgent()


class GitHubCrawler(BaseCrawler):
    """Crawls GitHub for hiring signals — job issues, team growth, tech stacks."""

    name = "github_crawler"
    source_type = "github"
    requires_js = False

    GITHUB_API = "https://api.github.com"

    async def crawl(self, url: str, **kwargs) -> list[CrawledItem]:
        source_name = kwargs.get("source_name", "github")
        # url might be a search query like "hiring .NET remote"
        search_query = kwargs.get("query", url)

        items: list[CrawledItem] = []

        try:
            async with httpx.AsyncClient(
                timeout=settings.request_timeout_seconds,
                follow_redirects=True,
            ) as client:
                headers = {"User-Agent": ua.random, "Accept": "application/vnd.github.v3+json"}

                # Search issues for hiring posts
                resp = await client.get(
                    f"{self.GITHUB_API}/search/issues",
                    params={"q": f"{search_query} is:issue is:open", "per_page": 30, "sort": "created"},
                    headers=headers,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    for issue in data.get("items", []):
                        title = issue.get("title", "")
                        body = issue.get("body", "") or ""
                        if not any(kw in title.lower() for kw in ["hiring", "job", "position", "engineer", "developer", "remote"]):
                            continue

                        items.append(CrawledItem(
                            source=source_name,
                            item_type="job",
                            url=issue.get("html_url", ""),
                            title=title,
                            external_id=f"gh-issue-{issue.get('id', '')}",
                            extracted_data={
                                "job_description": body[:3000],
                                "company_name": issue.get("repository_url", "").split("/")[-2] if "repository_url" in issue else "",
                                "source": "github_issues",
                            },
                            date_posted=self._parse_gh_date(issue.get("created_at")),
                        ))

                # Search repos for careers/jobs repos
                resp2 = await client.get(
                    f"{self.GITHUB_API}/search/repositories",
                    params={"q": f"{search_query} careers jobs hiring", "per_page": 10, "sort": "updated"},
                    headers=headers,
                )
                if resp2.status_code == 200:
                    for repo in resp2.json().get("items", []):
                        items.append(CrawledItem(
                            source=source_name,
                            item_type="signal",
                            url=repo.get("html_url", ""),
                            title=f"{repo.get('full_name', '')} — {repo.get('description', '')}",
                            external_id=f"gh-repo-{repo.get('id', '')}",
                            extracted_data={
                                "signal_types": ["team_expansion"],
                                "company_name": repo.get("owner", {}).get("login", ""),
                                "stars": repo.get("stargazers_count", 0),
                                "language": repo.get("language", ""),
                            },
                        ))

        except Exception as e:
            logger.error(f"GitHub crawl failed: {e}")

        logger.info(f"GitHub crawler found {len(items)} items")
        return items

    async def parse(self, html: str, url: str, **kwargs) -> list[CrawledItem]:
        # GitHub crawler uses API, not HTML parsing
        return []

    @staticmethod
    def _parse_gh_date(date_str: str | None) -> datetime | None:
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None
