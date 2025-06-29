"""
DoorDash Menu Scraper
This module provides functionality to scrape menu data from DoorDash restaurant pages.
"""

import asyncio
import logging
import random
import re
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin

try:
    from playwright.async_api import async_playwright, Browser, Page
    from bs4 import BeautifulSoup
except ImportError:
    print("❌ Playwright or BeautifulSoup not installed. Run: pip install playwright beautifulsoup4")
    # Consider exiting or raising a more specific error if this is critical at import time
    # For now, this allows the class to be defined even if imports fail,
    # though an instance would fail to operate.
    pass

# Configure logging for this module
logger = logging.getLogger(__name__)
# Basic configuration if no root logger is set (e.g., when run standalone)
if not logger.hasHandlers():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )

class DoorDashMenuScraper:
    """Scrapes menu data from DoorDash restaurant pages."""

    def __init__(self, headless: bool = True, timeout: int = 30000):
        self.headless = headless
        self.timeout = timeout
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None

        # Placeholder selectors - THESE WILL LIKELY NEED ADJUSTMENT
        # Based on common patterns; actual DoorDash selectors will differ.
        # These are highly speculative and likely need to be replaced with correct ones
        # after inspecting the live DoorDash page structure.
        self.selectors = {
            "restaurant_name": 'h1, [data-testid*="RestaurantName"], [class*="RestaurantName"]', # More generic h1
            "menu_category": '[data-testid*="MenuCategory"], [class*="MenuCategory"], [role="tab"]', # Generic category attempts
            # Try to find any div that might look like an item card
            "menu_item_card": """
                div[data-testid*="MenuItem"],
                div[class*="MenuItem"],
                div[class*="item"],
                div[role="listitem"]
            """,
            "item_name": """
                span[data-testid*="ItemName"], span[data-testid*="ItemTitle"],
                div[data-testid*="ItemName"], div[data-testid*="ItemTitle"],
                h2, h3, h4, span[class*="itemName"], div[class*="itemName"],
                span[class*="itemTitle"], div[class*="itemTitle"]
            """,
            "item_description": """
                div[data-testid*="ItemDescription"], span[data-testid*="ItemDescription"],
                p[data-testid*="ItemDescription"],
                div[class*="itemDescription"], span[class*="itemDescription"], p[class*="itemDescription"]
            """,
            "item_price": """
                span[data-testid*="ItemPrice"], div[data-testid*="ItemPrice"],
                span[class*="itemPrice"], div[class*="itemPrice"],
                span[class*="Price"], div[class*="Price"]
            """,
            "item_image": 'img[data-testid*="ItemImage"], img[class*="ItemImage"]'
        }

        # Price extraction patterns - can reuse or adapt from ProductionMenuScraper
        self.price_patterns = [
            r'\$\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?',
            r'\d{1,3}(?:,\d{3})*(?:\.\d{2})?\s*\$',
            r'USD\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?'
        ]

    async def setup_browser(self) -> bool:
        """Sets up the Playwright browser and page context."""
        try:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--no-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                ]
            )
            context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                java_script_enabled=True,
            )
            await context.add_cookies([
                # Placeholder for potential consent cookies if needed
                # {
                #     "name": "cookie_consent", "value": "true",
                #     "domain": ".doordash.com", "path": "/"
                # }
            ])
            self.page = await context.new_page()
            await self.page.set_extra_http_headers({
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            })
            logger.info("✅ DoorDash Scraper: Browser setup completed successfully")
            return True
        except Exception as e:
            logger.error(f"❌ DoorDash Scraper: Browser setup failed: {e}")
            return False

    async def close_browser(self):
        """Closes the Playwright browser."""
        try:
            if self.page:
                await self.page.close()
            if self.browser:
                await self.browser.close()
            logger.info("🧹 DoorDash Scraper: Browser cleanup completed")
        except Exception as e:
            logger.error(f"❌ DoorDash Scraper: Cleanup failed: {e}")

    async def _navigate_and_wait(self, url: str, wait_for_selector: Optional[str] = None) -> bool:
        """Navigates to a URL and waits for content or a specific selector."""
        try:
            logger.info(f"🌐 Navigating to DoorDash URL: {url}")
            # Go to the page, wait for DOM content to be loaded.
            await self.page.goto(url, wait_until='domcontentloaded', timeout=self.timeout)
            logger.info(f"✅ Navigated to {url}, DOM content loaded.")

            # Wait for dynamic content to load.
            # If a specific selector is provided, wait for that. This is preferred.
            if wait_for_selector:
                logger.info(f"Waiting for selector: '{wait_for_selector}'")
                try:
                    await self.page.wait_for_selector(wait_for_selector, timeout=self.timeout * 0.75) # Give more time
                    logger.info(f"✅ Selector '{wait_for_selector}' found.")
                except Exception as e:
                    logger.warning(f"⚠️ Timed out waiting for selector '{wait_for_selector}'. Page might not have loaded as expected. Error: {e}")
                    # Potentially try a generic sleep if selector fails, or let it propagate
                    logger.info("Attempting a generic sleep as fallback for selector timeout.")
                    await asyncio.sleep(random.uniform(5, 8))
            else:
                # If no specific selector, fall back to a longer sleep after domcontentloaded.
                # This is less reliable than waiting for a specific element.
                logger.info("No specific selector provided for waiting, using a generic sleep.")
                await asyncio.sleep(random.uniform(5, 8)) # Increased sleep duration

            logger.info("✅ Initial page load and wait completed.")
            return True
        except Exception as e:
            logger.error(f"❌ Navigation or wait failed for {url}: {e}")
            return False

    async def _scroll_page_to_load_all(self):
        """Scrolls the page to ensure all lazy-loaded content is present."""
        logger.info("📜 Scrolling page to load all menu items...")
        try:
            last_height = await self.page.evaluate("document.body.scrollHeight")
            scroll_attempts = 0
            MAX_SCROLL_ATTEMPTS = 10 # Prevent infinite loops

            while scroll_attempts < MAX_SCROLL_ATTEMPTS:
                await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(random.uniform(1.5, 2.5)) # Wait for new content to load

                new_height = await self.page.evaluate("document.body.scrollHeight")
                if new_height == last_height:
                    logger.info("📜 Reached end of page or no new content loaded.")
                    break
                last_height = new_height
                scroll_attempts += 1
            if scroll_attempts == MAX_SCROLL_ATTEMPTS:
                 logger.warning("📜 Max scroll attempts reached.")
        except Exception as e:
            logger.error(f"❌ Error during scrolling: {e}")

    def _extract_price(self, text: str) -> Optional[str]:
        """Extracts price from a text string using defined regex patterns."""
        if not text: return None
        for pattern in self.price_patterns:
            match = re.search(pattern, text)
            if match:
                price_str = match.group(0)
                # Basic cleaning: remove currency symbols for potential float conversion later
                # price_cleaned = re.sub(r'[$\sUSD]', '', price_str).strip()
                return price_str # Return the matched string including symbol for now
        return None

    async def _extract_menu_item_details(self, item_element) -> Optional[Dict[str, Any]]:
        """Extracts details from a single menu item Playwright element."""
        try:
            name_el = await item_element.query_selector(self.selectors["item_name"])
            name = await name_el.text_content() if name_el else None
            name = name.strip() if name else "Unknown Item"

            desc_el = await item_element.query_selector(self.selectors["item_description"])
            description = await desc_el.text_content() if desc_el else ""
            description = description.strip()

            price_el = await item_element.query_selector(self.selectors["item_price"])
            price_text = await price_el.text_content() if price_el else None
            price = self._extract_price(price_text) if price_text else None

            # Basic validation
            if name == "Unknown Item" and not price:
                return None

            return {
                "name": name,
                "description": description,
                "price": price,
                # "category": category_name, # Category would be handled by iterating through sections
                "image_url": None # Placeholder for image extraction
            }
        except Exception as e:
            logger.debug(f"Failed to extract details for an item: {e}")
            return None

    async def scrape_menu(self, url: str) -> Dict[str, Any]:
        """
        Main method to scrape menu data from a given DoorDash restaurant URL.
        """
        result = {
            'restaurant_name': None,
            'url': url,
            'success': False,
            'menu_items': [],
            'total_items': 0,
            'error': None
        }

        if not await self._navigate_and_wait(url, self.selectors["menu_item_card"]): # Wait for at least one menu item
            result['error'] = "Navigation or initial page load failed."
            return result

        await self._scroll_page_to_load_all()

        # Extract restaurant name (example)
        try:
            name_element = await self.page.query_selector(self.selectors["restaurant_name"])
            if name_element:
                result['restaurant_name'] = (await name_element.text_content()).strip()
        except Exception as e:
            logger.warning(f"Could not extract restaurant name: {e}")

        # This is a simplified approach. A real implementation would iterate through categories.
        # For now, let's try to get all item cards directly.
        menu_items_extracted = []
        try:
            item_elements = await self.page.query_selector_all(self.selectors["menu_item_card"])
            logger.info(f"Found {len(item_elements)} potential menu item elements.")

            for el in item_elements:
                item_details = await self._extract_menu_item_details(el)
                if item_details:
                    menu_items_extracted.append(item_details)

            if menu_items_extracted:
                result['success'] = True
                result['menu_items'] = menu_items_extracted
                result['total_items'] = len(menu_items_extracted)
                logger.info(f"✅ Successfully extracted {len(menu_items_extracted)} items.")
            else:
                result['error'] = "No menu items found with current selectors."
                logger.warning(result['error'])

        except Exception as e:
            logger.error(f"❌ Error during menu item extraction: {e}")
            result['error'] = str(e)

        return result

# Example Usage (for testing)
if __name__ == "__main__":
    async def main():
        # IMPORTANT: Replace with a REAL DoorDash restaurant URL for testing
        test_doordash_url = "https://www.doordash.com/store/donald's-famous-hot-dogs-chicago-179890/388150/?event_type=autocomplete&pickup=false"
        # test_doordash_url = None # Needs a real URL

        if not test_doordash_url or "some-restaurant" in test_doordash_url: # Keep the "some-restaurant" check in case URL is cleared
            print("👉 Please provide a valid DoorDash restaurant URL in the script for testing.")
            return

        scraper = DoorDashMenuScraper(headless=True) # Set headless=False to see browser

        if await scraper.setup_browser():
            try:
                print(f"🚀 Starting DoorDash scrape for: {test_doordash_url}")
                scrape_data = await scraper.scrape_menu(test_doordash_url)

                print("\n📊 SCRAPE RESULTS:")
                print(f"Restaurant: {scrape_data.get('restaurant_name', 'N/A')}")
                print(f"Success: {scrape_data['success']}")
                print(f"Total Items: {scrape_data['total_items']}")
                if scrape_data['error']:
                    print(f"Error: {scrape_data['error']}")

                if scrape_data['menu_items']:
                    print("\n📋 Sample Items (first 3):")
                    for i, item in enumerate(scrape_data['menu_items'][:3]):
                        print(f"  {i+1}. {item['name']} - {item.get('price', 'N/A')}")
                        if item.get('description'):
                            print(f"     Desc: {item['description'][:60]}...")

            except Exception as e:
                print(f"🚨 An error occurred during the main test execution: {e}")
            finally:
                await scraper.close_browser()
        else:
            print("❌ Failed to setup browser for DoorDash scraper.")

    asyncio.run(main())

# To run this:
# 1. Ensure playwright and beautifulsoup4 are installed: pip install playwright beautifulsoup4
# 2. Install playwright browsers: playwright install
# 3. Replace `test_doordash_url` with an actual DoorDash restaurant URL.
# 4. Run the script: python doordash_scraper.py
#
# Note: DoorDash employs anti-scraping measures. Success is not guaranteed and selectors
# will likely need frequent updates. This script provides a basic framework.
# Consider using proxies, more advanced fingerprinting evasion, or CAPTCHA solving
# services for more robust scraping, which are outside this basic script's scope.
