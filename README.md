# Web Scraping & Recipe Generator Pipeline

A streamlined pipeline for extracting product data from MiSuperFresh, processing it for AI consumption, and generating personalized recipes.

## Workflow

The project consists of 3 main steps:

1.  **Scrape Data**: `main.py` extracts product data from the website.
2.  **Process Data**: `process_data.py` filters edible products and formats them for ChatGPT.
3.  **Generate Recipe**: `webapp/index.html` generates a prompt for ChatGPT to create a recipe based on the available products.

## Installation

1.  Install Python dependencies:
    ```bash
    pip install -r requirements.txt
    ```

2.  Install Playwright browser:
    ```bash
    python -m playwright install chromium
    ```

## Usage

### Step 1: Scrape Data

Run the scraper to get the latest product list:

```bash
python main.py
```

This will save JSON and CSV files to the `data/` directory (e.g., `products_YYYYMMDD_HHMMSS.json`).

### Step 2: Process Data

Process the scraped data to create a text file listing edible products and their prices:

```bash
python process_data.py
```

This will automatically find the latest JSON file in `data/` and generate a text file (e.g., `products_YYYYMMDD_HHMMSS_productos_comestibles.txt`).

### Step 3: Generate Recipe Prompt

1.  Open `webapp/index.html` in your browser.
2.  Fill out the recipe preferences form.
3.  The app will generate a prompt for ChatGPT.
4.  **Important**: Copy the content of the text file generated in Step 2.
5.  Paste the prompt into ChatGPT, and attach or paste the content of the text file when asked (or as part of the context if the prompt instructions say so).

## Data Analysis (Optional)

You can analyze the scraped data (statistics, price distribution, etc.) using the Jupyter notebook:

```bash
jupyter notebook analyze_data.ipynb
```

## Project Structure

```
.
├── main.py                    # Step 1: Scrape products
├── process_data.py           # Step 2: Process JSON to text
├── analyze_data.ipynb        # Optional: Analyze scraped data stats
├── requirements.txt
├── README.md
├── config/
│   ├── __init__.py
│   └── settings.py           # Configuration
├── scraper/
│   ├── __init__.py
│   ├── api_scraper.py        # API-based scraper
│   ├── base_scraper.py
│   └── parsers/
│       ├── __init__.py
│       └── misuperfresh_parser.py
├── storage/
│   ├── __init__.py
│   └── file_storage.py
├── utils/
│   ├── __init__.py
│   ├── logger.py
│   └── error_handler.py
├── data/                      # Generated files (gitignored)
└── webapp/                    # Step 3: Recipe generator
    ├── index.html
    ├── script.js
    └── styles.css
```

## Configuration

Configuration is managed in `config/settings.py` and can be overridden with environment variables:

-   `CATALOG_URL`: Target URL to scrape
-   `OUTPUT_DIR`: Output directory for scraped data (default: `data`)
-   `LOG_LEVEL`: Logging level (default: `INFO`)

## License

This project is for educational and research purposes.
