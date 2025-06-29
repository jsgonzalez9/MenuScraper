"""
Uber Eats Menu Scraper
This module provides functionality to scrape menu data from Uber Eats restaurant pages.
"""

import asyncio
import logging
import random
import re
from typing import Dict, List, Optional, Any

try:
    from playwright.async_api import async_playwright, Browser, Page
    from bs4 import BeautifulSoup
except ImportError:
    print("❌ Playwright or BeautifulSoup not installed. Run: pip install playwright beautifulsoup4")
    pass

# Configure logging for this module
logger = logging.getLogger(__name__)
if not logger.hasHandlers():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )

class UberEatsMenuScraper:
    """Scrapes menu data from Uber Eats restaurant pages."""

    def __init__(self, headless: bool = True, timeout: int = 30000):
        self.headless = headless
        self.timeout = timeout
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None

        # Placeholder selectors - THESE WILL LIKELY NEED ADJUSTMENT.
        # Based on common patterns and pure speculation for Uber Eats.
        self.selectors = {
            "restaurant_name": 'h1, [data-testid*="restaurant-name"], [aria-label*="restaurant name"]', # Example
            "menu_category": 'div[data-testid*="category-title"], h2[id*="category"]', # Example
            "menu_item_card": 'div[data-testid*="menu-item"], div[role="article"], li[role="listitem"]', # Example
            "item_name": 'div[data-testid*="item-title"], span[data-testid*="item-name"], h3, h4', # Example
            "item_description": 'div[data-testid*="item-description"], p[class*="description"]', # Example
            "item_price": 'div[data-testid*="item-price"], span[class*="price"]', # Example
        }

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
            self.page = await context.new_page()
            await self.page.set_extra_http_headers({
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
            })
            logger.info("✅ Uber Eats Scraper: Browser setup completed.")
            return True
        except Exception as e:
            logger.error(f"❌ Uber Eats Scraper: Browser setup failed: {e}")
            return False

    async def close_browser(self):
        """Closes the Playwright browser."""
        try:
            if self.page: await self.page.close()
            if self.browser: await self.browser.close()
            logger.info("🧹 Uber Eats Scraper: Browser cleanup completed.")
        except Exception as e:
            logger.error(f"❌ Uber Eats Scraper: Cleanup failed: {e}")

    async def _navigate_and_wait(self, url: str, wait_for_selector: Optional[str] = None) -> bool:
        """Navigates and waits for content or a specific selector."""
        try:
            logger.info(f"🌐 Navigating to Uber Eats URL: {url}")
            await self.page.goto(url, wait_until='domcontentloaded', timeout=self.timeout)
            logger.info(f"✅ Navigated to {url}, DOM content loaded.")

            if wait_for_selector:
                logger.info(f"Waiting for selector: '{wait_for_selector}'")
                await self.page.wait_for_selector(wait_for_selector, timeout=self.timeout * 0.75)
                logger.info(f"✅ Selector '{wait_for_selector}' found.")
            else:
                logger.info("No specific selector for waiting, using generic sleep.")
                await asyncio.sleep(random.uniform(5, 8))

            logger.info("✅ Initial page load and wait completed.")
            return True
        except Exception as e:
            logger.error(f"❌ Navigation or wait failed for {url}: {e}")
            return False

    async def _scroll_page_to_load_all(self):
        """Scrolls page to load all lazy-loaded content."""
        logger.info("📜 Scrolling page for Uber Eats...")
        try:
            last_height = await self.page.evaluate("document.body.scrollHeight")
            for _ in range(10): # Max 10 scroll attempts
                await self.page.mouse.wheel(0, 15000) # Scroll down
                await asyncio.sleep(random.uniform(1.5, 2.5))
                new_height = await self.page.evaluate("document.body.scrollHeight")
                if new_height == last_height:
                    logger.info("📜 Reached end of page or no new content.")
                    break
                last_height = new_height
        except Exception as e:
            logger.error(f"❌ Error during scrolling: {e}")

    def _extract_price(self, text: str) -> Optional[str]:
        if not text: return None
        for pattern in self.price_patterns:
            match = re.search(pattern, text)
            if match: return match.group(0)
        return None

    async def _extract_menu_item_details(self, item_element) -> Optional[Dict[str, Any]]:
        """Extracts details from a single menu item Playwright element."""
        try:
            name_el = await item_element.query_selector(self.selectors["item_name"])
            name = (await name_el.text_content()).strip() if name_el else "Unknown Item"

            desc_el = await item_element.query_selector(self.selectors["item_description"])
            description = (await desc_el.text_content()).strip() if desc_el else ""

            price_el = await item_element.query_selector(self.selectors["item_price"])
            price_text = await price_el.text_content() if price_el else None
            price = self._extract_price(price_text) if price_text else None

            if name == "Unknown Item" and not price: return None

            return {"name": name, "description": description, "price": price}
        except Exception as e:
            logger.debug(f"Failed to extract item details: {e}")
            return None

    async def scrape_menu(self, url: str) -> Dict[str, Any]:
        """Main method to scrape menu data from an Uber Eats URL."""
        result = {'restaurant_name': None, 'url': url, 'success': False, 'menu_items': [], 'total_items': 0, 'error': None}

        if not await self._navigate_and_wait(url, self.selectors["menu_item_card"]):
            result['error'] = "Navigation or initial page load failed."
            return result

        await self._scroll_page_to_load_all()

        try:
            name_el = await self.page.query_selector(self.selectors["restaurant_name"])
            if name_el: result['restaurant_name'] = (await name_el.text_content()).strip()
        except Exception as e:
            logger.warning(f"Could not extract restaurant name: {e}")

        items_extracted = []
        try:
            item_elements = await self.page.query_selector_all(self.selectors["menu_item_card"])
            logger.info(f"Found {len(item_elements)} potential Uber Eats menu item elements.")

            for el in item_elements:
                details = await self._extract_menu_item_details(el)
                if details: items_extracted.append(details)

            if items_extracted:
                result.update({'success': True, 'menu_items': items_extracted, 'total_items': len(items_extracted)})
                logger.info(f"✅ Successfully extracted {len(items_extracted)} items from Uber Eats.")
            else:
                result['error'] = "No menu items found with current selectors on Uber Eats."
        except Exception as e:
            logger.error(f"❌ Error during Uber Eats item extraction: {e}")
            result['error'] = str(e)

        return result

if __name__ == "__main__":
    async def main_test_ubereats():
        # IMPORTANT: Replace with a REAL Uber Eats restaurant URL for testing
        test_ubereats_url = None # E.g., "https://www.ubereats.com/store/your-restaurant/..."

        if not test_ubereats_url:
            print("👉 Please provide a valid Uber Eats restaurant URL in the script for testing.")
            return

        scraper = UberEatsMenuScraper(headless=True) # Set False to see browser
        if await scraper.setup_browser():
            try:
                print(f"🚀 Starting Uber Eats scrape for: {test_ubereats_url}")
                data = await scraper.scrape_menu(test_ubereats_url)

                print("\n📊 UBER EATS SCRAPE RESULTS:")
                print(f"Restaurant: {data.get('restaurant_name', 'N/A')}")
                print(f"Success: {data['success']}")
                print(f"Items: {data['total_items']}")
                if data['error']: print(f"Error: {data['error']}")

                if data['menu_items']:
                    print("\n📋 Sample Items (first 3):")
                    for i, item in enumerate(data['menu_items'][:3]):
                        print(f"  {i+1}. {item['name']} - {item.get('price', 'N/A')}")
            finally:
                await scraper.close_browser()

    asyncio.run(main_test_ubereats())
# Notes:
# - Similar to DoorDash, Uber Eats has strong anti-scraping. Success is not guaranteed.
# - Selectors are placeholders and need validation against a live page.
# - Consider more advanced anti-detection techniques for production use.
