"""Browser-based scraper using Playwright for JavaScript-rendered pages."""

import time
from typing import Dict, Any, Optional
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
from scraper.base_scraper import BaseScraper
from config.settings import settings
from utils.logger import logger


class BrowserScraper(BaseScraper):
    """Browser-based web scraper using Playwright for JavaScript-rendered content."""

    def __init__(self, headless: bool = True, **kwargs):
        """
        Initialize the browser scraper.

        Args:
            headless: Run browser in headless mode
        """
        super().__init__(**kwargs)
        self.headless = headless
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self._start_browser()

    def _start_browser(self):
        """Start the Playwright browser."""
        try:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=self.headless)
            self.context = self.browser.new_context(
                user_agent=self.user_agent,
                viewport={"width": 1920, "height": 1080},
            )
            self.page = self.context.new_page()
            logger.info("Browser started successfully")
        except Exception as e:
            logger.error(f"Failed to start browser: {e}")
            raise

    def close(self):
        """Close the browser and cleanup."""
        try:
            if self.page:
                self.page.close()
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
            logger.info("Browser closed")
        except Exception as e:
            logger.error(f"Error closing browser: {e}")

    def fetch_html(self, url: str, wait_selector: Optional[str] = None, wait_time: int = 10) -> Optional[str]:
        """
        Fetch and return HTML from a JavaScript-rendered page.

        Args:
            url: URL to fetch
            wait_selector: CSS selector to wait for (optional)
            wait_time: Maximum time to wait in seconds

        Returns:
            HTML content as string or None if failed
        """
        try:
            logger.info(f"Navigating to: {url}")
            self.page.goto(url, wait_until="networkidle", timeout=60000)

            # Wait for Flutter app to load - try multiple approaches
            logger.info("Waiting for Flutter app to render...")
            
            # Wait for Flutter canvas or shadow DOM elements
            try:
                # Try waiting for Flutter-specific elements
                self.page.wait_for_selector("flt-scene-host, canvas, [data-flutter]", timeout=wait_time * 1000)
                logger.info("Flutter elements detected")
            except:
                logger.warning("Flutter elements not found, waiting for any content...")
            
            # Additional wait for content to render
            time.sleep(5)
            
            # Try to wait for any visible content
            try:
                # Wait for any div or element with text content
                self.page.wait_for_function(
                    "document.body.innerText.length > 100",
                    timeout=wait_time * 1000
                )
                logger.info("Page content detected")
            except:
                logger.warning("Content check timeout, proceeding anyway...")

            # Wait for specific selector if provided
            if wait_selector:
                logger.info(f"Waiting for selector: {wait_selector}")
                try:
                    self.page.wait_for_selector(wait_selector, timeout=wait_time * 1000)
                except:
                    logger.warning(f"Selector {wait_selector} not found")

            # Get the rendered HTML
            html = self.page.content()
            logger.debug(f"Successfully fetched HTML (length: {len(html)} bytes)")
            
            # Also try to get inner text to see if content is there
            body_text = self.page.evaluate("document.body.innerText")
            logger.info(f"Body text length: {len(body_text) if body_text else 0} characters")
            if body_text and len(body_text) > 100:
                logger.info(f"Sample body text: {body_text[:200]}...")
            
            return html

        except Exception as e:
            logger.error(f"Error fetching HTML from {url}: {e}")
            return None

    def scrape(self, url: str, wait_selector: Optional[str] = None, wait_time: int = 5) -> Dict[str, Any]:
        """
        Scrape data from a JavaScript-rendered URL.

        Args:
            url: URL to scrape
            wait_selector: CSS selector to wait for before scraping
            wait_time: Maximum time to wait in seconds

        Returns:
            Dictionary containing scraped data
        """
        html = self.fetch_html(url, wait_selector, wait_time)
        if not html:
            return {"url": url, "html": None, "error": "Failed to fetch page"}

        return {
            "url": url,
            "html": html,
        }

    def get_screenshot(self, filename: str = "screenshot.png"):
        """
        Take a screenshot of the current page.

        Args:
            filename: Output filename for screenshot
        """
        try:
            self.page.screenshot(path=filename)
            logger.info(f"Screenshot saved to: {filename}")
        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")

    def wait_between_requests(self):
        """Wait between requests to be respectful to the server."""
        if self.delay > 0:
            time.sleep(self.delay)

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup browser."""
        self.close()

