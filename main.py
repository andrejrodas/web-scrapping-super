"""Main entry point for the web scraping pipeline."""

import sys
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from scraper.browser_scraper import BrowserScraper
from scraper.api_scraper import ApiScraper
from scraper.parsers.misuperfresh_parser import MisuperfreshParser
from storage.file_storage import FileStorage
from config.settings import settings
from utils.logger import logger


def scrape_page_api(scraper: ApiScraper, url: str) -> dict:
    """
    Scrape a page using API interception (preferred for Flutter apps).

    Args:
        scraper: API scraper instance
        url: URL to scrape

    Returns:
        Dictionary with scraped data
    """
    logger.info(f"Scraping page via API: {url}")
    result = scraper.scrape(url, wait_time=20)
    return result


def scrape_page(scraper: BrowserScraper, url: str) -> dict:
    """
    Scrape a single page and extract products.

    Args:
        scraper: Browser scraper instance
        url: URL to scrape

    Returns:
        Dictionary with scraped data
    """
    logger.info(f"Scraping page: {url}")
    result = scraper.scrape(url, wait_time=15)
    
    if result.get("html"):
        soup = BeautifulSoup(result["html"], "html.parser")
        # Enable debug mode if no products found
        debug_mode = False
        products = MisuperfreshParser.parse_products(soup, debug=debug_mode)
        if len(products) == 0:
            logger.warning("No products found. Re-running with debug mode enabled...")
            debug_mode = True
            products = MisuperfreshParser.parse_products(soup, debug=debug_mode)
        next_page = MisuperfreshParser.find_next_page(soup, settings.base_url)
        
        result["products"] = products
        result["next_page"] = next_page
        result["product_count"] = len(products)
        
        logger.info(f"Found {len(products)} products on page")
        if next_page:
            logger.info(f"Next page URL: {next_page}")
        else:
            logger.info("No next page found - reached last page")
    else:
        result["products"] = []
        result["next_page"] = None
        result["product_count"] = 0
        logger.error("Failed to scrape page - no HTML content")

    return result


def scrape_all_pages_api(scraper: ApiScraper, start_url: str, max_pages: int = 100) -> List[Dict[str, Any]]:
    """
    Scrape all pages using API interception with pagination support.

    Args:
        scraper: API scraper instance
        start_url: Starting URL
        max_pages: Maximum number of pages to scrape

    Returns:
        List of all products from all pages
    """
    all_products = []
    current_url = start_url
    page_num = 1

    logger.info(f"Starting pagination scraping from: {start_url}")

    while current_url and page_num <= max_pages:
        logger.info("=" * 60)
        logger.info(f"SCRAPING PAGE {page_num}")
        logger.info("=" * 60)

        result = scrape_page_api(scraper, current_url)
        products = result.get("products", [])
        all_products.extend(products)

        logger.info(f"Page {page_num}: Found {len(products)} products (Total so far: {len(all_products)})")

        # Check for next page
        next_page = result.get("next_page")
        if next_page and next_page != current_url:
            current_url = next_page
            page_num += 1
            # Wait between pages
            scraper.wait_between_requests()
        else:
            logger.info("No more pages available")
            break

    logger.info(f"Completed pagination: {page_num} pages, {len(all_products)} total products")
    return all_products


def scrape_multiple_urls(urls: List[str], use_api: bool = True) -> List[Dict[str, Any]]:
    """
    Scrape multiple URLs and collect all products.

    Args:
        urls: List of URLs to scrape
        use_api: Whether to use API scraper (True) or browser scraper (False)

    Returns:
        List of all products from all URLs
    """
    all_products = []

    if use_api:
        logger.info(f"Scraping {len(urls)} URLs using API scraper...")
        with ApiScraper() as scraper:
            for i, url in enumerate(urls, 1):
                logger.info(f"\n{'=' * 60}")
                logger.info(f"URL {i}/{len(urls)}: {url}")
                logger.info(f"{'=' * 60}")

                # Scrape all pages for this URL
                products = scrape_all_pages_api(scraper, url)
                all_products.extend(products)

                logger.info(f"URL {i} complete: {len(products)} products")
    else:
        logger.info(f"Scraping {len(urls)} URLs using browser scraper...")
        with BrowserScraper(headless=True) as scraper:
            for i, url in enumerate(urls, 1):
                logger.info(f"\n{'=' * 60}")
                logger.info(f"URL {i}/{len(urls)}: {url}")
                logger.info(f"{'=' * 60}")

                result = scrape_page(scraper, url)
                products = result.get("products", [])
                all_products.extend(products)

                logger.info(f"URL {i} complete: {len(products)} products")

    return all_products


def main():
    """Main function to orchestrate the scraping pipeline."""
    logger.info("Starting web scraping pipeline")

    # Define URLs to scrape (can be extended to read from config/file)
    urls_to_scrape = [
        settings.catalog_url,  # Current URL
        # Add more URLs here as needed
        # "https://www.misuperfresh.com.gt/catalog/10?minPrice=0&maxPrice=500",
    ]

    logger.info(f"Scraping {len(urls_to_scrape)} URL(s)")
    for i, url in enumerate(urls_to_scrape, 1):
        logger.info(f"  {i}. {url}")

    # Try API scraper first (better for Flutter apps)
    logger.info("\nAttempting to scrape via API interception...")
    try:
        all_products = scrape_multiple_urls(urls_to_scrape, use_api=True)

        if all_products:
            logger.info(f"\nSuccessfully scraped {len(all_products)} total products via API")

            # Display summary
            print("\n" + "=" * 60)
            print("SCRAPING SUMMARY")
            print("=" * 60)
            print(f"Total products found: {len(all_products)}")
            print(f"URLs scraped: {len(urls_to_scrape)}")
            print("\nSample products (first 10):")
            for i, product in enumerate(all_products[:10], 1):
                print(f"  {i}. {product.get('name', 'N/A')} - {product.get('price', 'N/A')}")

            if len(all_products) > 10:
                print(f"\n  ... and {len(all_products) - 10} more products")

            # Save to files
            logger.info("\nSaving data to files...")
            storage = FileStorage()
            saved_files = storage.save(all_products, format="all")

            print("\n" + "=" * 60)
            print("FILES SAVED")
            print("=" * 60)
            for format_type, filepath in saved_files.items():
                print(f"  {format_type.upper()}: {filepath.absolute()}")

            logger.info("Scraping pipeline completed (API method)")
            return
        else:
            logger.warning("API scraper found no products, falling back to browser scraper...")
    except Exception as e:
        logger.warning(f"API scraper failed: {e}, falling back to browser scraper...")

    # Fallback to browser scraper
    logger.info("Using browser scraper (may not work for Flutter canvas rendering)...")
    with BrowserScraper(headless=True) as scraper:
        # Scrape first page
        logger.info("=" * 60)
        logger.info("SCRAPING PAGE 1")
        logger.info("=" * 60)
        page1_result = scrape_page(scraper, settings.catalog_url)
        
        # Display results
        print("\n" + "=" * 60)
        print("PAGE 1 RESULTS")
        print("=" * 60)
        print(f"URL: {page1_result['url']}")
        print(f"Products found: {page1_result.get('product_count', 0)}")
        print("\nProducts:")
        for i, product in enumerate(page1_result.get("products", []), 1):
            print(f"  {i}. {product.get('name', 'N/A')} - {product.get('price', 'N/A')}")
        
        if page1_result.get("next_page"):
            print(f"\nNext page: {page1_result['next_page']}")
            
            # Wait before next request
            scraper.wait_between_requests()
            
            # Scrape next page
            logger.info("=" * 60)
            logger.info("SCRAPING PAGE 2")
            logger.info("=" * 60)
            page2_result = scrape_page(scraper, page1_result["next_page"])
            
            # Display results
            print("\n" + "=" * 60)
            print("PAGE 2 RESULTS")
            print("=" * 60)
            print(f"URL: {page2_result['url']}")
            print(f"Products found: {page2_result.get('product_count', 0)}")
            print("\nProducts:")
            for i, product in enumerate(page2_result.get("products", []), 1):
                print(f"  {i}. {product.get('name', 'N/A')} - {product.get('price', 'N/A')}")
            
            if page2_result.get("next_page"):
                print(f"\nNext page: {page2_result['next_page']}")
            else:
                print("\nNo more pages available")
        else:
            print("\nNo next page available")

    logger.info("Scraping pipeline completed")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error in main: {e}", exc_info=True)
        sys.exit(1)

