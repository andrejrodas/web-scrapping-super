"""Parser for misuperfresh.com.gt catalog pages."""

from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup, Tag
from utils.logger import logger


class MisuperfreshParser:
    """Parser for extracting product data from misuperfresh.com.gt."""

    @staticmethod
    def parse_products(soup: BeautifulSoup, debug: bool = False) -> List[Dict[str, Any]]:
        """
        Extract product names and prices from the page.

        Args:
            soup: BeautifulSoup object of the page
            debug: Enable debug mode for detailed logging

        Returns:
            List of dictionaries containing product data
        """
        products = []
        
        # Try to load suggested selectors from debug output
        suggested_selectors = MisuperfreshParser._load_suggested_selectors()
        
        # Common selectors for product containers
        # Try multiple common patterns including Flutter-specific ones
        product_selectors = [
            # Flutter-specific
            "flt-scene-host > *",
            "canvas + *",
            "[data-flutter]",
            # Common e-commerce patterns
            "div.product-item",
            "div.product",
            "article.product",
            "div.item-product",
            "li.product",
            "[data-product-id]",
            # Add suggested selectors
            *suggested_selectors,
        ]

        product_elements = []
        for selector in product_selectors:
            try:
                found = soup.select(selector)
                if found:
                    product_elements = found
                    logger.info(f"Found {len(product_elements)} elements using selector: {selector}")
                    if debug:
                        logger.debug(f"Sample element HTML: {str(product_elements[0])[:200]}...")
                    break
            except Exception as e:
                if debug:
                    logger.debug(f"Selector '{selector}' failed: {e}")
                continue

        if not product_elements:
            # Fallback: try to find any elements that might contain products
            logger.warning("No products found with common selectors, trying fallback methods")
            
            # Look for price patterns and their parent elements
            price_elements = soup.find_all(string=lambda text: text and ("Q" in text or "$" in text))
            logger.debug(f"Found {len(price_elements)} potential price elements")
            
            if price_elements and debug:
                # Try to find common parent containers
                parent_containers = set()
                for price_elem in price_elements[:10]:
                    parent = price_elem.parent
                    if parent:
                        classes = parent.get("class", [])
                        if classes:
                            parent_containers.add(".".join(classes))
                
                if parent_containers:
                    logger.info(f"Found potential product containers: {list(parent_containers)[:5]}")
                    # Try these as selectors
                    for container_class in list(parent_containers)[:3]:
                        try:
                            found = soup.select(f"div.{container_class}")
                            if found and len(found) >= 3:  # At least 3 similar elements
                                product_elements = found
                                logger.info(f"Using fallback selector: div.{container_class} ({len(found)} elements)")
                                break
                        except:
                            continue

        for element in product_elements:
            product_data = MisuperfreshParser._extract_product_data(element, debug=debug)
            if product_data:
                products.append(product_data)

        logger.info(f"Extracted {len(products)} products from page")
        return products

    @staticmethod
    def _load_suggested_selectors() -> List[str]:
        """Load suggested selectors from debug output if available."""
        from pathlib import Path
        import json
        
        suggestions_file = Path("selector_suggestions.json")
        if suggestions_file.exists():
            try:
                with open(suggestions_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    suggestions = data.get("suggestions", [])
                    if suggestions:
                        logger.info(f"Loaded {len(suggestions)} suggested selectors from debug output")
                        return suggestions
            except Exception as e:
                logger.debug(f"Could not load suggested selectors: {e}")
        
        return []

    @staticmethod
    def _extract_product_data(element: Tag, debug: bool = False) -> Optional[Dict[str, Any]]:
        """
        Extract name and price from a product element.

        Args:
            element: BeautifulSoup Tag element containing product data
            debug: Enable debug logging

        Returns:
            Dictionary with product name and price, or None if extraction fails
        """
        try:
            # Try multiple common patterns for product name
            name = None
            name_selectors = [
                "h2.product-name",
                "h3.product-name",
                ".product-title",
                ".name",
                "a.product-link",
                "h2",
                "h3",
            ]

            for selector in name_selectors:
                name_elem = element.select_one(selector)
                if name_elem:
                    name = name_elem.get_text(strip=True)
                    break

            if not name:
                # Fallback: get text from first heading or link
                name_elem = element.find("h2") or element.find("h3") or element.find("a")
                if name_elem:
                    name = name_elem.get_text(strip=True)

            # Try multiple common patterns for price
            price = None
            price_selectors = [
                ".price",
                ".product-price",
                ".price-current",
                "[class*='price']",
                ".cost",
            ]

            for selector in price_selectors:
                price_elem = element.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    price = MisuperfreshParser._clean_price(price_text)
                    if price:
                        break

            if not price:
                # Fallback: search for price patterns in all text
                all_text = element.get_text()
                price = MisuperfreshParser._extract_price_from_text(all_text)

            if name and price:
                return {
                    "name": name,
                    "price": price,
                }
            elif name:
                if debug:
                    logger.debug(f"Found product name but no price: {name}")
                    logger.debug(f"Element HTML: {str(element)[:300]}...")
                return {"name": name, "price": None}
            elif debug:
                logger.debug(f"Could not extract product data from element")
                logger.debug(f"Element HTML: {str(element)[:300]}...")

        except Exception as e:
            if debug:
                logger.error(f"Error extracting product data: {e}", exc_info=True)
            return None

        return None

    @staticmethod
    def _clean_price(price_text: str) -> Optional[str]:
        """
        Clean and extract price from text.

        Args:
            price_text: Raw price text

        Returns:
            Cleaned price string or None
        """
        if not price_text:
            return None

        # Remove common currency symbols and whitespace, keep numbers and decimal point
        import re
        # Look for patterns like Q123.45, $123.45, 123.45, etc.
        price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
        if price_match:
            return price_match.group(0)
        return None

    @staticmethod
    def _extract_price_from_text(text: str) -> Optional[str]:
        """
        Extract price from text using regex patterns.

        Args:
            text: Text to search for price

        Returns:
            Price string or None
        """
        import re
        # Pattern for prices: Q123.45, $123.45, 123.45, etc.
        patterns = [
            r'Q\s*([\d,]+\.?\d*)',
            r'\$\s*([\d,]+\.?\d*)',
            r'([\d,]+\.?\d*)\s*(?:Q|quetzales|GTQ)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).replace(',', '')
        return None

    @staticmethod
    def find_next_page(soup: BeautifulSoup, base_url: str) -> Optional[str]:
        """
        Find the next page URL from pagination.

        Args:
            soup: BeautifulSoup object of the current page
            base_url: Base URL for building relative URLs

        Returns:
            Next page URL or None if not found
        """
        from urllib.parse import urljoin

        # Common pagination selectors
        next_selectors = [
            'a[aria-label="Next"]',
            'a.next',
            'a[class*="next"]',
            'a:contains("Siguiente")',
            'a:contains("Next")',
            'a:contains(">")',
        ]

        for selector in next_selectors:
            try:
                next_link = soup.select_one(selector)
                if next_link and next_link.get("href"):
                    href = next_link["href"]
                    return urljoin(base_url, href)
            except Exception as e:
                logger.debug(f"Error with selector {selector}: {e}")

        # Fallback: look for links containing "page" or numbers
        all_links = soup.find_all("a", href=True)
        current_url = None
        for link in all_links:
            href = link.get("href", "")
            text = link.get_text(strip=True).lower()
            if "siguiente" in text or "next" in text or (text.isdigit() and int(text) > 1):
                if href:
                    return urljoin(base_url, href)

        return None

