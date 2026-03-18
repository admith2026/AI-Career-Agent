"""Reddit crawler — monitors subreddits for job posts and hiring signals."""

import logging
from datetime import datetime, timezone
import httpx
from fake_useragent import UserAgent

from .base import BaseCrawler, CrawledItem
from app.config import settings

logger = logging.getLogger(__name__)
ua = UserAgent()

HIRING_SUBREDDITS = [
    "forhire", "remotejs", "dotnetjobs", "cscareerquestions",
    "remotework", "freelance", "startups",
]


class RedditCrawler(BaseCrawler):
    """Crawls Reddit for job postings and hiring discussions."""

    name = "reddit_crawler"
    source_type = "reddit"
    requires_js = False

    async def crawl(self, url: str, **kwargs) -> list[CrawledItem]:
        source_name = kwargs.get("source_name", "reddit")
        subreddits = kwargs.get("subreddits", HIRING_SUBREDDITS)
        items: list[CrawledItem] = []

        headers = {"User-Agent": f"CareerBot/1.0 ({ua.random})"}

        async with httpx.AsyncClient(
            timeout=settings.request_timeout_seconds,
            follow_redirects=True,
        ) as client:
            for subreddit in subreddits:
                try:
                    resp = await client.get(
                        f"https://www.reddit.com/r/{subreddit}/new.json?limit=50",
                        headers=headers,
                    )
                    if resp.status_code != 200:
                        continue

                    data = resp.json()
                    for child in data.get("data", {}).get("children", []):
                        post = child.get("data", {})
                        title = post.get("title", "")
                        selftext = post.get("selftext", "")

                        # Filter for hiring-related posts
                        text_lower = f"{title} {selftext}".lower()
                        is_hiring = any(kw in text_lower for kw in [
                            "hiring", "[hiring]", "job", "position", "looking for",
                            "remote", "contract", "freelance", ".net", "engineer",
                        ])
                        if not is_hiring:
                            continue

                        item_type = "job" if any(k in text_lower for k in ["[hiring]", "position", "looking for"]) else "signal"

                        created_utc = post.get("created_utc", 0)
                        date_posted = datetime.fromtimestamp(created_utc, tz=timezone.utc) if created_utc else None

                        items.append(CrawledItem(
                            source=source_name,
                            item_type=item_type,
                            url=f"https://www.reddit.com{post.get('permalink', '')}",
                            title=title,
                            external_id=f"reddit-{post.get('id', '')}",
                            extracted_data={
                                "job_description": selftext[:3000],
                                "subreddit": subreddit,
                                "score": post.get("score", 0),
                                "author": post.get("author", ""),
                                "created_utc": created_utc,
                            },
                            date_posted=date_posted,
                        ))
                except Exception as e:
                    logger.error(f"Reddit crawl r/{subreddit} failed: {e}")

        logger.info(f"Reddit crawler found {len(items)} items")
        return items

    async def parse(self, html: str, url: str, **kwargs) -> list[CrawledItem]:
        return []
