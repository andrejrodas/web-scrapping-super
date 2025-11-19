"""Synchronous scraper implementation using requests and BeautifulSoup."""

import time
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup
from scraper.base_scraper import BaseScraper
from config.settings import settings
from utils.logger import logger


class SyncScraper(BaseScraper):
    """Synchronous web scraper using requests and BeautifulSoup."""

    def __init__(self, **kwargs):
        """Initialize the synchronous scraper."""
        super().__init__(**kwargs)
        self.delay = settings.delay

    def fetch_html(self, url: str) -> Optional[BeautifulSoup]:
        """
        Fetch and parse HTML from a URL.

        Args:
            url: URL to fetch

        Returns:
            BeautifulSoup object or None if failed
        """
        response = self.fetch_page(url)
        if response:
            return BeautifulSoup(response.content, "html.parser")
        return None

    def scrape(self, url: str) -> Dict[str, Any]:
        """
        Scrape data from a URL.

        Args:
            url: URL to scrape

        Returns:
            Dictionary containing scraped data and HTML
        """
        soup = self.fetch_html(url)
        if not soup:
            return {"url": url, "products": [], "next_page": None, "error": "Failed to fetch page"}

        return {
            "url": url,
            "soup": soup,
            "html": str(soup) if soup else None,
        }

    def get_next_page_url(self, soup: BeautifulSoup, current_url: str) -> Optional[str]:
        """
        Extract the next page URL from the current page.

        Args:
            soup: BeautifulSoup object of the current page
            current_url: Current page URL

        Returns:
            Next page URL or None if not found
        """
        # This will be implemented based on the actual page structure
        # Common patterns: look for "next" link, pagination buttons, etc.
        next_link = soup.find("a", {"class": "next"}) or soup.find("a", string="Siguiente")
        if next_link and next_link.get("href"):
            return self.build_url(next_link["href"])
        return None

    def wait_between_requests(self):
        """Wait between requests to be respectful to the server."""
        if self.delay > 0:
            time.sleep(self.delay)

