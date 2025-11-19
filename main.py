"""Main entry point for the web scraping pipeline."""

import sys
from typing import List, Dict, Any
from scraper.api_scraper import ApiScraper
from storage.file_storage import FileStorage
from config.settings import settings
from utils.logger import logger


def scrape_page_api(scraper: ApiScraper, url: str) -> dict:
    """
    Scrape a page using API interception.

    Args:
        scraper: API scraper instance
        url: URL to scrape

    Returns:
        Dictionary with scraped data
    """
    logger.info(f"Scraping page via API: {url}")
    result = scraper.scrape(url, wait_time=20)
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


def scrape_multiple_urls(urls: List[str]) -> List[Dict[str, Any]]:
    """
    Scrape multiple URLs and collect all products.

    Args:
        urls: List of URLs to scrape

    Returns:
        List of all products from all URLs
    """
    all_products = []

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

    return all_products


def main():
    """Main function to orchestrate the scraping pipeline."""
    logger.info("Starting web scraping pipeline")

    # Define URLs to scrape (can be extended to read from config/file)
    urls_to_scrape = [
        settings.catalog_url,  # Current URL
    ]

    logger.info(f"Scraping {len(urls_to_scrape)} URL(s)")
    for i, url in enumerate(urls_to_scrape, 1):
        logger.info(f"  {i}. {url}")

    # Scrape via API interception
    logger.info("\nAttempting to scrape via API interception...")
    try:
        all_products = scrape_multiple_urls(urls_to_scrape)

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

            logger.info("Scraping pipeline completed")
            return
        else:
            logger.warning("API scraper found no products.")
    except Exception as e:
        logger.error(f"API scraper failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error in main: {e}", exc_info=True)
        sys.exit(1)
