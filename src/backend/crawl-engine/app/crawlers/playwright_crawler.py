"""Playwright-based crawler for JavaScript-heavy pages."""

import logging
from app.config import settings
from .base import BaseCrawler, CrawledItem

logger = logging.getLogger(__name__)


class PlaywrightCrawler(BaseCrawler):
    """Crawler for JS-rendered pages — LinkedIn, dynamic career portals, SPAs."""

    name = "playwright_crawler"
    source_type = "browser"
    requires_js = True

    def __init__(self):
        self._browser = None
        self._playwright = None

    async def _get_browser(self):
        if self._browser is None:
            from playwright.async_api import async_playwright
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=settings.playwright_headless,
            )
        return self._browser

    async def crawl(self, url: str, **kwargs) -> list[CrawledItem]:
        source_name = kwargs.get("source_name", "unknown")
        wait_selector = kwargs.get("wait_selector", "body")

        try:
            browser = await self._get_browser()
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                viewport={"width": 1920, "height": 1080},
            )
            page = await context.new_page()
            await page.goto(url, wait_until="networkidle", timeout=settings.playwright_timeout_ms)

            if wait_selector != "body":
                await page.wait_for_selector(wait_selector, timeout=10000)

            html = await page.content()
            await context.close()

            return await self.parse(html, url, source_name=source_name)
        except Exception as e:
            logger.error(f"Playwright crawl failed for {url}: {e}")
            return []

    async def parse(self, html: str, url: str, **kwargs) -> list[CrawledItem]:
        from bs4 import BeautifulSoup
        source_name = kwargs.get("source_name", "unknown")
        soup = BeautifulSoup(html, "lxml")
        items: list[CrawledItem] = []

        # Extract job cards from rendered DOM
        selectors = [
            "div[data-job-id]", ".job-card", ".posting-card",
            "[class*='JobCard']", "[class*='job-listing']",
            "article", ".position-card",
        ]

        for selector in selectors:
            for el in soup.select(selector):
                title_el = el.find(["h2", "h3", "h4", "a"])
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                if not title or len(title) < 5:
                    continue

                link = ""
                link_el = el.find("a", href=True)
                if link_el:
                    link = link_el["href"]
                    if not link.startswith("http"):
                        from urllib.parse import urljoin
                        link = urljoin(url, link)

                items.append(CrawledItem(
                    source=source_name,
                    item_type="job",
                    url=link or url,
                    title=title,
                    raw_html=str(el)[:5000],
                    extracted_data={
                        "job_description": el.get_text(separator="\n", strip=True)[:3000],
                    },
                ))

            if items:
                break  # Use first matching selector

        logger.info(f"Playwright crawler extracted {len(items)} items from {url}")
        return items

    async def close(self):
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
