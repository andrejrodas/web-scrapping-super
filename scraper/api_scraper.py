"""API-based scraper that intercepts Flutter app API calls."""

import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from playwright.sync_api import sync_playwright, Page, Response
from scraper.base_scraper import BaseScraper
from config.settings import settings
from utils.logger import logger


class ApiScraper(BaseScraper):
    """Scraper that extracts data by intercepting API calls from Flutter app."""

    def __init__(self, **kwargs):
        """Initialize the API scraper."""
        super().__init__(**kwargs)
        self.delay = settings.delay
        self.playwright = None
        self.browser = None
        self.context = None
        self.page: Optional[Page] = None
        self.api_responses: List[Dict[str, Any]] = []
        self._start_browser()

    def _start_browser(self):
        """Start the Playwright browser."""
        try:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=True)
            self.context = self.browser.new_context(
                user_agent=self.user_agent,
                viewport={"width": 1920, "height": 1080},
            )
            self.page = self.context.new_page()
            logger.info("Browser started for API interception")
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

    def wait_between_requests(self):
        """Wait between requests to be respectful to the server."""
        if self.delay > 0:
            time.sleep(self.delay)

    def _setup_api_interception(self):
        """Set up API response interception."""
        self.api_responses = []

        def handle_response(response: Response):
            """Sync handler - read body immediately."""
            url = response.url
            if "msf-api.gta.com.gt" in url:
                try:
                    content_type = response.headers.get("content-type", "")
                    if "application/json" in content_type or "json" in content_type.lower():
                        # Use response.json() which should work in the handler
                        try:
                            # Try to get the response asynchronously - we need to wait for it
                            # Actually, in sync API, we can use response.json() directly
                            body = response.json()
                            self.api_responses.append({
                                "url": url,
                                "method": response.request.method,
                                "status": response.status,
                                "body": body,
                                "timestamp": time.time(),
                            })
                            logger.info(f"Captured API response: {url} (Status: {response.status})")
                            if isinstance(body, list):
                                logger.info(f"  Found {len(body)} items")
                                if len(body) > 0:
                                    logger.info(f"  Sample item keys: {list(body[0].keys()) if isinstance(body[0], dict) else 'N/A'}")
                            elif isinstance(body, dict):
                                logger.info(f"  Keys: {list(body.keys())}")
                        except Exception as e:
                            logger.warning(f"Could not parse JSON from {url}: {e}")
                            # Try alternative: read body as text
                            try:
                                body_text = response.text()
                                logger.debug(f"Response text (first 200 chars): {body_text[:200]}")
                            except:
                                pass
                except Exception as e:
                    logger.debug(f"Error processing response {url}: {e}")

        self.page.on("response", handle_response)

    def scrape(self, url: str, wait_time: int = 20) -> Dict[str, Any]:
        """
        Scrape data by intercepting API calls.

        Args:
            url: URL to scrape
            wait_time: Time to wait for API calls in seconds

        Returns:
            Dictionary containing scraped data
        """
        try:
            # Set up API interception before navigating
            self._setup_api_interception()

            logger.info(f"Navigating to: {url}")
            
            # Use route interception to capture and potentially modify API requests
            captured_response = None
            original_request_body = None
            
            def handle_route(route):
                """Handle route requests - capture request body and let them through."""
                request = route.request
                if "msf-api.gta.com.gt/api/products" in request.url and request.method == "POST":
                    # Capture the original request body
                    try:
                        if request.post_data:
                            original_request_body = json.loads(request.post_data)
                            logger.info(f"Captured POST request body: {json.dumps(original_request_body, indent=2)}")
                    except:
                        pass
                route.continue_()
            
            self.page.route("**/msf-api.gta.com.gt/api/**", handle_route)
            
            # Set up response waiting BEFORE navigation using context manager
            with self.page.expect_response(
                lambda response: ("msf-api.gta.com.gt/api/products" in response.url or 
                                 "msf-api.gta.com.gt/api/catalog/subcategory" in response.url) and
                                response.status == 200,
                timeout=30000
            ) as response_info:
                # Now navigate
                self.page.goto(url, wait_until="networkidle", timeout=60000)
                
                # Get the response from the context manager
                try:
                    products_response = response_info.value
                    logger.info(f"Received API response: {products_response.url}")
                    # Read body immediately while response is still valid
                    try:
                        body = products_response.json()
                        captured_response = {
                            "url": products_response.url,
                            "method": products_response.request.method,
                            "status": products_response.status,
                            "body": body,
                        }
                        self.api_responses.append(captured_response)
                        logger.info("Successfully captured products API response")
                        if isinstance(body, list):
                            logger.info(f"  Found {len(body)} items")
                        elif isinstance(body, dict):
                            logger.info(f"  Keys: {list(body.keys())}")
                    except Exception as e:
                        logger.warning(f"Could not parse products API response: {e}")
                except Exception as e:
                    logger.warning(f"Error getting response: {e}")
            
            # Wait additional time for other API calls
            if not captured_response:
                logger.info(f"Waiting {wait_time} seconds for API calls...")
                time.sleep(wait_time)
            
            # Try making additional API calls with different parameters to get more products
            # The API uses POST with type parameter - type 7 might be "on offer", let's try other types
            # Only do this if we got very few products (likely filtered) OR if force_all_products is enabled
            if captured_response:
                products_count = len(captured_response.get("body", {}).get("products", []))
                
                # Check if we should force "all products" mode
                force_all = settings.api_force_all_products
                
                # Load cached best configuration
                best_config = None
                cache_file = Path("config/api_config_cache.json")
                if settings.api_cache_config and cache_file.exists():
                    try:
                        with open(cache_file, "r", encoding="utf-8") as f:
                            cache = json.load(f)
                            # Use cached config if available
                            if "best_config" in cache:
                                best_config = cache["best_config"]
                                logger.info(f"Using cached best config: {best_config}")
                    except Exception as e:
                        logger.debug(f"Could not load cache: {e}")
                
                # If we got few products OR force_all is enabled, try other configurations
                if products_count <= 5 or force_all:
                    if force_all:
                        logger.info("Force all products mode enabled, trying additional API calls...")
                    else:
                        logger.info(f"Only {products_count} product(s) found, trying additional API calls with different parameters...")
                    
                    # Extract subcategory ID from URL
                    from urllib.parse import urlparse
                    parsed = urlparse(url)
                    path_parts = parsed.path.split('/')
                    subcategory_id = None
                    if 'catalog' in path_parts:
                        try:
                            catalog_idx = path_parts.index('catalog')
                            if catalog_idx + 1 < len(path_parts):
                                subcategory_id = int(path_parts[catalog_idx + 1])
                        except:
                            pass
                    
                    # Extract price filters from URL
                    from urllib.parse import parse_qs
                    query_params = parse_qs(parsed.query)
                    min_price = query_params.get("minPrice", ["0"])[0]
                    max_price = query_params.get("maxPrice", ["9999"])[0]
                    
                    # Try different type values - prioritize the best config if cached
                    test_configs = [
                        {"type": 0, "subcategoryId": subcategory_id},  # All products in subcategory (usually best)
                        {"type": 1, "subcategoryId": subcategory_id},  # Featured
                        {"subcategoryId": subcategory_id},  # No type filter
                        {"type": 0},  # All products, no subcategory
                        {},  # No filters at all
                    ]
                    
                    # If we have a cached best config, try it first
                    if best_config and best_config in test_configs:
                        test_configs.remove(best_config)
                        test_configs.insert(0, best_config)
                    
                    best_config_found = None
                    max_products_found = products_count
                    
                    for i, config in enumerate(test_configs, 1):
                        try:
                            logger.info(f"Trying API call {i}/{len(test_configs)} with config: {config}...")
                            
                            # Build request body
                            request_body = {
                                "channel": "web",
                                "store": {"code": 204}
                            }
                            
                            # Add config parameters
                            request_body.update(config)
                            
                            # Add price filters if available
                            if min_price and max_price:
                                request_body["minPrice"] = float(min_price)
                                request_body["maxPrice"] = float(max_price)
                            
                            # Make a direct API call
                            api_response = self.page.request.post(
                                "https://msf-api.gta.com.gt/api/products",
                                data=json.dumps(request_body),
                                headers={
                                    "Content-Type": "application/json",
                                    "Referer": "https://www.misuperfresh.com.gt/",
                                }
                            )
                            
                            if api_response.status == 200:
                                body = api_response.json()
                                products = body.get("products", [])
                                logger.info(f"  Config {config}: Found {len(products)} products")
                                
                                if len(products) > max_products_found:
                                    max_products_found = len(products)
                                    best_config_found = config
                                    logger.info(f"  NEW BEST! Found {len(products)} products with config: {config}")
                                
                                if len(products) > products_count:
                                    # Found more products!
                                    self.api_responses.append({
                                        "url": "https://msf-api.gta.com.gt/api/products",
                                        "method": "POST",
                                        "status": 200,
                                        "body": body,
                                    })
                                    # Don't break - collect all responses with more products
                        except Exception as e:
                            logger.debug(f"Error testing config {config}: {e}")
                            continue
                    
                    # Cache the best configuration for future use
                    if best_config_found and settings.api_cache_config:
                        try:
                            cache_file.parent.mkdir(parents=True, exist_ok=True)
                            cache = {"best_config": best_config_found, "last_updated": time.time()}
                            with open(cache_file, "w", encoding="utf-8") as f:
                                json.dump(cache, f, indent=2)
                            logger.info(f"Cached best config: {best_config_found}")
                        except Exception as e:
                            logger.debug(f"Could not cache config: {e}")

            # Collect all products from all API responses
            # Use the response with the most products
            products_data = None
            subcategory_data = None
            max_products = 0

            for response in self.api_responses:
                resp_url = response["url"]
                if "/api/products" in resp_url or "/api/catalog/subcategory" in resp_url:
                    body = response.get("body")
                    if body:
                        if "/api/products" in resp_url:
                            # Count products in this response
                            products_list = body.get("products", []) if isinstance(body, dict) else []
                            product_count = len(products_list) if isinstance(products_list, list) else 0
                            
                            # Use the response with the most products
                            if product_count > max_products:
                                max_products = product_count
                                products_data = body
                                logger.info(f"Found products data with {product_count} products")
                        elif "/api/catalog/subcategory" in resp_url:
                            subcategory_data = body
                            logger.info(f"Found subcategory data")
            
            # If we have multiple responses, merge all products
            all_products_lists = []
            for response in self.api_responses:
                if "/api/products" in response.get("url", ""):
                    body = response.get("body", {})
                    if isinstance(body, dict) and "products" in body:
                        products_list = body["products"]
                        if isinstance(products_list, list):
                            all_products_lists.append(products_list)
            
            # If we have multiple product lists, merge them and deduplicate
            if len(all_products_lists) > 1:
                logger.info(f"Merging products from {len(all_products_lists)} API responses...")
                merged_products = []
                seen_barcodes = set()
                
                for products_list in all_products_lists:
                    for product in products_list:
                        barcode = product.get("barcode")
                        if barcode and barcode not in seen_barcodes:
                            seen_barcodes.add(barcode)
                            merged_products.append(product)
                
                logger.info(f"Merged {len(merged_products)} unique products from {len(all_products_lists)} responses")
                
                # Update products_data with merged list
                if products_data and isinstance(products_data, dict):
                    products_data["products"] = merged_products

            # Parse products from API response
            products = []
            if products_data:
                products = self._parse_api_products(products_data)
            elif subcategory_data:
                # Try to extract products from subcategory data
                products = self._parse_subcategory_data(subcategory_data)

            # Check for pagination info in the API response
            pagination_info = None
            next_page_url = None
            
            if products_data and isinstance(products_data, dict):
                # Look for pagination fields
                pagination_fields = ["pagination", "pageInfo", "page_info", "paging", "meta"]
                for field in pagination_fields:
                    if field in products_data:
                        pagination_info = products_data[field]
                        break
                
                # Check if there's a next page
                if pagination_info:
                    if isinstance(pagination_info, dict):
                        has_next = pagination_info.get("hasNext", pagination_info.get("has_next", False))
                        next_page = pagination_info.get("nextPage", pagination_info.get("next_page"))
                        if has_next or next_page:
                            # Construct next page URL if we have page number
                            current_page = pagination_info.get("currentPage", pagination_info.get("current_page", 1))
                            total_pages = pagination_info.get("totalPages", pagination_info.get("total_pages"))
                            if total_pages and current_page < total_pages:
                                # Try to construct next page URL
                                from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
                                parsed = urlparse(url)
                                params = parse_qs(parsed.query)
                                params["page"] = [str(current_page + 1)]
                                new_query = urlencode(params, doseq=True)
                                next_page_url = urlunparse(parsed._replace(query=new_query))
                                logger.info(f"Pagination detected: page {current_page}/{total_pages}, next: {next_page_url}")

            return {
                "url": url,
                "products": products,
                "product_count": len(products),
                "api_responses": len(self.api_responses),
                "pagination": pagination_info,
                "next_page": next_page_url,
                "raw_data": {
                    "products": products_data,
                    "subcategory": subcategory_data,
                },
            }

        except Exception as e:
            logger.error(f"Error scraping via API: {e}", exc_info=True)
            return {
                "url": url,
                "products": [],
                "product_count": 0,
                "error": str(e),
            }

    def _parse_api_products(self, data: Any) -> List[Dict[str, Any]]:
        """
        Parse products from API response.

        Args:
            data: API response data (list or dict)

        Returns:
            List of product dictionaries
        """
        products = []

        if isinstance(data, list):
            # Direct list of products
            logger.info(f"Processing list with {len(data)} items")
            for item in data:
                product = self._extract_product_from_api_item(item)
                if product:
                    products.append(product)
        elif isinstance(data, dict):
            # Try common keys - products is the most likely
            possible_keys = ["products", "items", "data", "results", "content"]
            logger.info(f"Processing dict with keys: {list(data.keys())}")
            
            for key in possible_keys:
                if key in data:
                    value = data[key]
                    logger.info(f"Found key '{key}' with type: {type(value)}")
                    
                    if isinstance(value, list):
                        logger.info(f"  Processing {len(value)} items from '{key}'")
                        for item in value:
                            product = self._extract_product_from_api_item(item)
                            if product:
                                products.append(product)
                        if products:
                            break  # Found products, stop looking
                    elif isinstance(value, dict):
                        # Nested dict, try to extract from it
                        logger.info(f"  '{key}' is a dict, trying to extract from it")
                        nested_products = self._parse_api_products(value)
                        products.extend(nested_products)
                        if products:
                            break
            
            # If no list found, try to extract from dict directly
            if not products:
                logger.info("No products list found, trying to extract from dict directly")
                product = self._extract_product_from_api_item(data)
                if product:
                    products.append(product)

        logger.info(f"Parsed {len(products)} products from API data")
        return products

    def _parse_subcategory_data(self, data: Any) -> List[Dict[str, Any]]:
        """Parse products from subcategory API response."""
        return self._parse_api_products(data)

    def _extract_product_from_api_item(self, item: Any) -> Optional[Dict[str, Any]]:
        """
        Extract product name and price from API item.

        Args:
            item: API item (dict or other)

        Returns:
            Product dictionary or None
        """
        if not isinstance(item, dict):
            return None

        # Try common field names for product name
        name = None
        name_fields = ["name", "productName", "title", "productTitle", "nombre", "descripcion", "description", "productDescription"]
        for field in name_fields:
            if field in item:
                name_value = item[field]
                if name_value:
                    name = str(name_value).strip()
                    break

        # Try common field names for price
        price = None
        price_fields = ["price", "precio", "cost", "costo", "amount", "valor", "unitPrice", "unit_price", "salePrice", "sale_price"]
        for field in price_fields:
            if field in item:
                price_value = item[field]
                if price_value is not None:
                    # Convert to string and clean
                    price = str(price_value).strip()
                    # Remove currency symbols if present
                    price = price.replace("Q", "").replace("$", "").replace(",", "").strip()
                    # Keep only numbers and decimal point
                    import re
                    price_match = re.search(r'[\d.]+', price)
                    if price_match:
                        price = price_match.group(0)
                break

        if name:
            product = {
                "name": name,
                "price": price,
            }
            
            # Extract additional useful fields
            if "description" in item:
                product["description"] = str(item["description"]).strip()
            
            if "barcode" in item:
                product["barcode"] = item["barcode"]
            
            if "stock" in item:
                product["stock"] = item["stock"]
            
            # Extract offer information
            if "offer" in item and isinstance(item["offer"], dict):
                offer = item["offer"]
                if offer.get("price"):
                    product["offer_price"] = str(offer["price"])
                if offer.get("description"):
                    product["offer_description"] = str(offer["description"]).strip()
            
            # Extract image URL
            if "thumbnail" in item and isinstance(item["thumbnail"], dict):
                if "url" in item["thumbnail"]:
                    product["image_url"] = item["thumbnail"]["url"]
            elif "images" in item and isinstance(item["images"], list) and len(item["images"]) > 0:
                if isinstance(item["images"][0], dict) and "url" in item["images"][0]:
                    product["image_url"] = item["images"][0]["url"]
            
            # Extract category/subcategory info
            if "subcategory" in item and isinstance(item["subcategory"], dict):
                subcat = item["subcategory"]
                if "name" in subcat:
                    product["subcategory"] = str(subcat["name"]).strip()
                if "category" in subcat and isinstance(subcat["category"], dict):
                    if "name" in subcat["category"]:
                        product["category"] = str(subcat["category"]["name"]).strip()
            
            # Keep raw data for reference
            product["raw_data"] = item
            
            return product
        elif logger.isEnabledFor(10):  # DEBUG level
            logger.debug(f"Could not extract product from item. Available keys: {list(item.keys())}")

        return None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup browser."""
        self.close()

