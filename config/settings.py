"""Configuration settings for the web scraping pipeline."""

import os
from typing import Optional
from config.constants import (
    DEFAULT_TIMEOUT,
    DEFAULT_RETRIES,
    DEFAULT_DELAY,
    DEFAULT_USER_AGENT,
)


class Settings:
    """Configuration settings loaded from environment variables or defaults."""

    def __init__(self):
        # Target URL
        self.base_url: str = os.getenv(
            "BASE_URL", "https://www.misuperfresh.com.gt"
        )
        self.catalog_url: str = os.getenv(
            "CATALOG_URL",
            "https://www.misuperfresh.com.gt/catalog/9?minPrice=0&maxPrice=225",
        )

        # Scraping parameters
        self.timeout: int = int(os.getenv("TIMEOUT", str(DEFAULT_TIMEOUT)))
        self.max_retries: int = int(os.getenv("MAX_RETRIES", str(DEFAULT_RETRIES)))
        self.delay: float = float(os.getenv("DELAY", str(DEFAULT_DELAY)))
        self.user_agent: str = os.getenv("USER_AGENT", DEFAULT_USER_AGENT)

        # Storage settings
        self.output_dir: str = os.getenv("OUTPUT_DIR", "data")
        self.storage_format: str = os.getenv("STORAGE_FORMAT", "json")

        # API scraping settings
        self.api_force_all_products: bool = os.getenv("API_FORCE_ALL_PRODUCTS", "true").lower() == "true"
        self.api_cache_config: bool = os.getenv("API_CACHE_CONFIG", "true").lower() == "true"

        # Logging
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")
        self.log_file: Optional[str] = os.getenv("LOG_FILE", "scraper.log")


# Global settings instance
settings = Settings()

