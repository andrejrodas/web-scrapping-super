"""Constants and default values for the web scraping pipeline."""

# Default scraping parameters
DEFAULT_TIMEOUT = 30
DEFAULT_RETRIES = 3
DEFAULT_DELAY = 1  # seconds between requests

# Storage formats
STORAGE_FORMAT_CSV = "csv"
STORAGE_FORMAT_JSON = "json"
STORAGE_FORMAT_PARQUET = "parquet"

# User agent to avoid blocking
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
)

