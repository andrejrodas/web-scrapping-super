"""Base scraper class with common functionality."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from urllib.parse import urljoin, urlparse
import requests
from config.settings import settings
from utils.logger import logger
from utils.error_handler import retry_with_backoff


class BaseScraper(ABC):
    """Abstract base class for web scrapers."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: Optional[int] = None,
        user_agent: Optional[str] = None,
    ):
        """
        Initialize the base scraper.

        Args:
            base_url: Base URL for the website
            timeout: Request timeout in seconds
            user_agent: User agent string for requests
        """
        self.base_url = base_url or settings.base_url
        self.timeout = timeout or settings.timeout
        self.user_agent = user_agent or settings.user_agent
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create and configure a requests session."""
        session = requests.Session()
        session.headers.update({"User-Agent": self.user_agent})
        return session

    @retry_with_backoff(
        max_retries=3,
        exceptions=(requests.RequestException, requests.Timeout),
    )
    def fetch_page(self, url: str) -> Optional[requests.Response]:
        """
        Fetch a web page with retry logic.

        Args:
            url: URL to fetch

        Returns:
            Response object or None if failed
        """
        try:
            logger.info(f"Fetching URL: {url}")
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            logger.debug(f"Successfully fetched URL: {url} (Status: {response.status_code})")
            return response
        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            raise

    def build_url(self, path: str) -> str:
        """
        Build a full URL from a path.

        Args:
            path: Relative or absolute path

        Returns:
            Full URL
        """
        if urlparse(path).netloc:
            return path
        return urljoin(self.base_url, path)

    @abstractmethod
    def scrape(self, url: str) -> Dict[str, Any]:
        """
        Scrape data from a URL.

        Args:
            url: URL to scrape

        Returns:
            Dictionary containing scraped data
        """
        pass

