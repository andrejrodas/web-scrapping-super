# Web Scraping Pipeline - MiSuperFresh

A robust web scraping pipeline for extracting product data from MiSuperFresh (misuperfresh.com.gt), built with data engineering and DevOps best practices.

## Features

- **API-based scraping**: Intercepts Flutter app API calls for reliable data extraction
- **Automatic pagination**: Handles multiple pages automatically
- **Smart configuration caching**: Caches best API configurations for faster subsequent runs
- **Multiple URL support**: Scrape multiple catalog URLs in one run
- **Data export**: Saves data in JSON and CSV formats
- **Error handling**: Robust error handling with retry logic
- **Logging**: Comprehensive logging for debugging and monitoring

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Install Playwright browser:
```bash
python -m playwright install chromium
```

## Usage

### Basic Usage

Run the scraper with default settings:
```bash
python main.py
```

This will:
- Use the URL from `config/settings.py`
- Extract all products automatically
- Save results to `data/` folder (JSON and CSV)

### Customize URL

**Option 1: Edit `config/settings.py`**
```python
self.catalog_url: str = "https://www.misuperfresh.com.gt/catalog/9?minPrice=0&maxPrice=225"
```

**Option 2: Use environment variable**
```bash
set CATALOG_URL=https://www.misuperfresh.com.gt/catalog/10?minPrice=0&maxPrice=500
python main.py
```

**Option 3: Edit `main.py` to add multiple URLs**
```python
urls_to_scrape = [
    settings.catalog_url,
    "https://www.misuperfresh.com.gt/catalog/10?minPrice=0&maxPrice=500",
    # Add more URLs here
]
```

## Configuration

Configuration is managed in `config/settings.py` and can be overridden with environment variables:

- `API_FORCE_ALL_PRODUCTS`: Force "all products" mode (default: `true`)
- `API_CACHE_CONFIG`: Enable configuration caching (default: `true`)
- `CATALOG_URL`: Target URL to scrape
- `OUTPUT_DIR`: Output directory for scraped data (default: `data`)
- `LOG_LEVEL`: Logging level (default: `INFO`)

## Project Structure

```
.
├── main.py                 # Main entry point
├── requirements.txt        # Python dependencies
├── config/                 # Configuration files
│   ├── settings.py         # Settings and configuration
│   ├── constants.py        # Default constants
│   └── api_config_cache.json  # Cached API configurations
├── scraper/                # Scraping logic
│   ├── api_scraper.py      # API-based scraper (primary)
│   ├── browser_scraper.py  # Browser-based scraper (fallback)
│   ├── base_scraper.py     # Base scraper class
│   └── parsers/            # Data parsers
│       └── misuperfresh_parser.py
├── storage/                 # Data storage
│   └── file_storage.py     # File-based storage (JSON, CSV)
├── processing/              # Data processing (for future use)
├── utils/                   # Utilities
│   └── logger.py           # Logging configuration
└── tests/                   # Unit tests

```

## Output

Scraped data is saved to the `data/` directory with timestamps:
- `products_YYYYMMDD_HHMMSS.json` - Full data with metadata
- `products_YYYYMMDD_HHMMSS.csv` - Tabular format for analysis

## How It Works

1. **API Interception**: Uses Playwright to intercept API calls from the Flutter web app
2. **Smart Configuration**: Automatically tests different API configurations to get all products
3. **Caching**: Caches the best configuration for faster subsequent runs
4. **Data Extraction**: Extracts product information including:
   - Name, description, price
   - Offer price and description
   - Stock, barcode
   - Category, subcategory
   - Image URLs

## Logging

Logs are written to:
- Console (INFO level and above)
- `scraper.log` file (all levels)

## Requirements

- Python 3.7+
- Playwright
- See `requirements.txt` for full list

## License

This project is for educational and research purposes.

