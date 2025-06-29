#!/usr/bin/env python3
"""
Production Menu Scraper - Final Implementation
Combines successful elements from Enhanced Scraper with production-ready features
Target: 50%+ success rate with robust error handling and practical deployment
"""

import asyncio
import json
import logging
import random
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urljoin, urlparse

try:
    from playwright.async_api import async_playwright, Browser, Page
except ImportError:
    print("❌ Playwright not installed. Run: pip install playwright")
    exit(1)

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("❌ BeautifulSoup not installed. Run: pip install beautifulsoup4")
    exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('production_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ProductionMenuScraper:
    """Production-ready menu scraper with enhanced success rate and reliability"""
    
    def __init__(self, headless: bool = True, timeout: int = 30000):
        self.headless = headless
        self.timeout = timeout
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        
        # Enhanced extraction patterns based on successful Enhanced Scraper
        self.menu_selectors = [
            # Yelp-specific selectors (proven successful)
            'div[data-testid="menu-item"]',
            'div.menu-item',
            'div.menu-section-item',
            'div[class*="menu"][class*="item"]',
            
            # Generic menu selectors
            '.menu-item', '.menu-entry', '.dish', '.food-item',
            '[class*="menu-item"]', '[class*="dish"]', '[class*="food"]',
            'li[class*="menu"]', 'div[class*="menu"]',
            
            # Structured data selectors
            '[itemtype*="MenuItem"]', '[itemtype*="Food"]',
            '.menu .item', '.menu-list .item', '.food-menu .item'
        ]
        
        # Allergen detection patterns
        self.allergen_patterns = {
            'gluten': r'\b(gluten|wheat|flour|bread|pasta|cereal)\b',
            'dairy': r'\b(milk|cheese|butter|cream|yogurt|dairy)\b',
            'nuts': r'\b(nuts?|almond|walnut|pecan|cashew|peanut)\b',
            'shellfish': r'\b(shrimp|crab|lobster|shellfish|seafood)\b',
            'eggs': r'\b(egg|eggs|mayonnaise)\b',
            'soy': r'\b(soy|soybean|tofu|tempeh)\b',
            'fish': r'\b(fish|salmon|tuna|cod|halibut)\b',
            'sesame': r'\b(sesame|tahini)\b'
        }
        
        # Price extraction patterns
        self.price_patterns = [
            r'\$\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?',  # $12.99 or $ 12.99 or $1,234.56
            r'\d{1,3}(?:,\d{3})*(?:\.\d{2})?\s*\$',  # 12.99$ or 1,234.56$
            r'USD\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?', # USD 12.99 or USD 1,234.56
            r'\$\d+',                               # $12 (integer)
            r'\d+\.\d{2}',                          # 12.99 (no currency symbol)
            r'\d+\s*dollars?',                      # 12 dollars
            r'Price:\s*\$?\d+(?:\.\d{2})?'          # Price: $12.99
        ]
    
    async def setup_browser(self) -> bool:
        """Setup browser with stealth configuration"""
        try:
            playwright = await async_playwright().start()
            
            # Enhanced browser setup for better success rate
            self.browser = await playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--no-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-features=VizDisplayCompositor',
                    '--disable-web-security',
                    '--disable-features=TranslateUI',
                    '--disable-ipc-flooding-protection',
                    '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                ]
            )
            
            # Create page with enhanced settings
            context = await self.browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080},
                # java_script_enabled=True, # Already default
                # accept_downloads=False, # Default
            )
            self.page = await context.new_page()

            # Set additional headers that are common in browsers
            await self.page.set_extra_http_headers({
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-User': '?1',
                'Sec-Fetch-Dest': 'document',
                'Upgrade-Insecure-Requests': '1'
            })
            
            # Set realistic viewport (already set in new_context, but doesn't hurt to ensure)
            await self.page.set_viewport_size({"width": 1920, "height": 1080})
            
            # Add stealth scripts
            await self.page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
                
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en'],
                });
            """)
            
            logger.info("✅ Browser setup completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Browser setup failed: {e}")
            return False

    async def extract_menu_items(self, url: str, restaurant_name: Optional[str] = None, city_state: Optional[str] = None) -> Dict[str, Any]:
        """
        Extract menu items from a given URL.
        If initial extraction is poor and restaurant_name is provided,
        attempts to find and scrape the official restaurant website.
        """
        start_time = time.time()
        final_result = {
            'url': url, # Initial URL
            'success': False,
            'items': [],
            'total_items': 0,
            'processing_time': 0,
            'extraction_method': None,
            'allergen_summary': {},
            'price_coverage': 0,
            'error': None,
            'scraped_source': 'primary_url' # Indicates if data is from primary or official_site
        }

        # Attempt 1: Scrape the provided URL
        logger.info(f"Attempting to scrape primary URL: {url}")
        primary_scrape_result = await self._scrape_single_url(url, is_official_site=False)

        final_result.update({
            'success': primary_scrape_result['success'],
            'items': primary_scrape_result['items'],
            'total_items': primary_scrape_result['total_items'],
            'extraction_method': primary_scrape_result['extraction_method'],
            'error': primary_scrape_result['error']
        })

        # Condition to try official website: primary scrape not very successful AND name is provided
        MIN_ITEMS_THRESHOLD = 3 # If primary scrape finds less than this, try official site
        should_try_official_site = (
            restaurant_name and
            (not final_result['success'] or final_result['total_items'] < MIN_ITEMS_THRESHOLD)
        )

        if should_try_official_site:
            logger.info(f"Primary URL scrape yielded {final_result['total_items']} items. Attempting to find and scrape official website for '{restaurant_name}'.")
            official_site_url = await self._find_restaurant_website(restaurant_name, city_state)

            if official_site_url and official_site_url != url: # Ensure it's a new, valid URL
                logger.info(f"Found potential official website: {official_site_url}. Scraping it now.")
                official_scrape_result = await self._scrape_single_url(official_site_url, is_official_site=True)

                # If official site scrape is better or primary failed, use official site data
                if official_scrape_result['success'] and \
                   (not final_result['success'] or official_scrape_result['total_items'] > final_result['total_items']):
                    logger.info(f"Official website scrape was more successful. Using its data.")
                    final_result.update({
                        'success': official_scrape_result['success'],
                        'items': official_scrape_result['items'],
                        'total_items': official_scrape_result['total_items'],
                        'extraction_method': official_scrape_result['extraction_method'],
                        'error': official_scrape_result['error'], # Could be None if successful
                        'scraped_source': 'official_site',
                        'url': official_site_url # Update URL to the one actually scraped
                    })
                elif official_scrape_result['success']:
                     logger.info(f"Official website scrape was successful but yielded fewer or same items ({official_scrape_result['total_items']}) than primary ({final_result['total_items']}). Keeping primary URL data.")
                else:
                    logger.warning(f"Official website scrape failed. Keeping primary URL data. Error: {official_scrape_result.get('error')}")
            elif official_site_url == url:
                logger.info("Official website found is the same as the primary URL. No secondary scrape needed.")
            else:
                logger.info(f"Could not find a different official website for '{restaurant_name}'. Sticking with primary URL data.")

        # Final calculations for allergens and price coverage based on the chosen item list
        if final_result['items']:
            final_result['allergen_summary'] = self._summarize_allergens(final_result['items'])
            final_result['price_coverage'] = self._calculate_price_coverage(final_result['items'])

        final_result['processing_time'] = round(time.time() - start_time, 2)

        if final_result['success']:
            logger.info(f"Extraction complete for {final_result['url']} ({final_result['scraped_source']}). Items: {final_result['total_items']}.")
        else:
            logger.warning(f"Extraction failed for {final_result['url']} ({final_result['scraped_source']}). Error: {final_result.get('error')}")

        return final_result

    async def navigate_with_retry(self, url: str, max_retries: int = 3) -> bool:
        """Navigate to URL with retry logic and bot detection handling"""
        for attempt in range(max_retries):
            try:
                logger.info(f"🌐 Navigating to {url} (attempt {attempt + 1}/{max_retries})")
                
                # Random delay to appear more human-like
                await asyncio.sleep(random.uniform(1, 3))
                
                # Navigate with timeout
                response = await self.page.goto(
                    url, 
                    wait_until='commit', # Faster initial load, then wait for ready state
                    timeout=self.timeout
                )
                
                if response and response.status == 200:
                    # Wait for the page to be fully loaded
                    await self.page.wait_for_function("document.readyState === 'complete'", timeout=self.timeout / 2)
                    await asyncio.sleep(random.uniform(1, 2)) # Additional small random delay
                    
                    # Check for bot detection
                    content = await self.page.content()
                    if self._is_bot_detected(content):
                        logger.warning(f"🤖 Bot detection on attempt {attempt + 1}")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(random.uniform(5, 10))
                            continue
                        return False
                    
                    logger.info("✅ Navigation successful")
                    return True
                else:
                    logger.warning(f"⚠️ HTTP {response.status if response else 'No response'}")
                    
            except Exception as e:
                logger.error(f"❌ Navigation attempt {attempt + 1} failed: {e}")
                
            if attempt < max_retries - 1:
                await asyncio.sleep(random.uniform(3, 7))
        
        return False
    
    def _is_bot_detected(self, content: str) -> bool:
        """Check if bot detection is present"""
        bot_indicators = [
            "robot", "captcha", "verification", "blocked",
            "access denied", "suspicious activity",
            "please verify", "security check"
        ]
        content_lower = content.lower()
        return any(indicator in content_lower for indicator in bot_indicators)
    
    # The duplicated extract_menu_items method (lines 260-368) has been removed.
    # The correct one is at line 139.
    # The _scrape_single_url method (lines 370-477) now contains the core scraping logic.

    async def _scrape_single_url(self, url: str, is_official_site: bool = False) -> Dict[str, Any]:
        """Helper function to scrape a single URL, used by extract_menu_items."""
        # This is essentially the body of the original extract_menu_items,
        # refactored to be callable for both primary and official website URLs.
        partial_result = {
            'success': False,
            'items': [],
            'total_items': 0,
            'extraction_method': None,
            'error': None
            # Note: 'url' and 'processing_time' will be handled by the caller
        }

        try:
            if not await self.navigate_with_retry(url):
                partial_result['error'] = 'Navigation failed'
                return partial_result

            # --- Dynamic content handling (Yelp-specific or generic) ---
            if "yelp.com" in url and not is_official_site: # Apply Yelp specific only if it's Yelp and not an official site mistaken as Yelp
                logger.info(f"Applying Yelp-specific dynamic content handling for {url}")
                try:
                    for _ in range(3): # Scroll a few times
                        await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        await asyncio.sleep(random.uniform(0.5, 1.5))
                except Exception as e:
                    logger.warning(f"Error during scrolling on Yelp page: {e}")
            elif is_official_site: # Generic scrolling for official sites
                logger.info(f"Applying generic scrolling for official site {url}")
                try:
                    for _ in range(2): # Scroll a bit less aggressively
                        await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        await asyncio.sleep(random.uniform(0.5, 1.0))
                except Exception as e:
                    logger.warning(f"Error during scrolling on official site: {e}")
            # --- End dynamic content handling ---

            content = await self.page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            items = []
            extraction_method = None
            
            for selector in self.menu_selectors: # Uses the class's menu_selectors
                try:
                    elements = await self.page.query_selector_all(selector)
                    if elements and len(elements) > 0:
                        logger.info(f"Found {len(elements)} potential items with selector: {selector} on {url}")
                        current_items = []
                        for element in elements[:30]: # Increased limit slightly
                            item_data = await self._extract_item_data(element)
                            if item_data and self._is_valid_menu_item(item_data):
                                current_items.append(item_data)
                        
                        if current_items:
                            items.extend(current_items) # Use extend to accumulate from multiple selectors if needed (though loop breaks)
                            extraction_method = f'css_selector: {selector}'
                            logger.info(f"Extracted {len(current_items)} items using {selector} on {url}")
                            if len(items) > 5 : # If a selector yields good results, break early
                                break
                            
                except Exception as e:
                    logger.debug(f"Selector {selector} failed on {url}: {e}")
                    continue
            
            if not items:
                logger.info(f"CSS selectors yielded no items on {url}. Trying text patterns.")
                items = self._extract_by_text_patterns(soup)
                if items:
                    extraction_method = 'text_patterns'
            
            if not items:
                logger.info(f"Text patterns yielded no items on {url}. Trying structured data.")
                items = self._extract_structured_data(soup)
                if items:
                    extraction_method = 'structured_data'
            
            if items:
                unique_items = self._deduplicate_items(items)
                for item in unique_items:
                    item['allergens'] = self._detect_allergens(item.get('description', '') + ' ' + item.get('name', ''))
                
                partial_result.update({
                    'success': True,
                    'items': unique_items,
                    'total_items': len(unique_items),
                    'extraction_method': extraction_method,
                    # Allergen summary & price coverage will be calculated on the final item list
                })
                logger.info(f"Successfully extracted {len(unique_items)} menu items from {url}")
            else:
                partial_result['error'] = 'No menu items found'
                logger.warning(f"No menu items extracted from {url}")
                
        except Exception as e:
            partial_result['error'] = str(e)
            logger.error(f"Extraction from {url} failed: {e}")
        
        return partial_result

    async def _extract_item_data(self, element) -> Optional[Dict[str, Any]]:
        """Extract data from a menu item element"""
        try:
            # Get text content
            text_content = await element.text_content()
            if not text_content or len(text_content.strip()) < 3:
                return None
            
            # Get HTML for more detailed extraction
            html_content = await element.inner_html()
            
            # Extract name (usually the first line or prominent text)
            name = self._extract_item_name(text_content)
            
            # Extract price
            price = self._extract_price(text_content)
            
            # Extract description
            description = self._extract_description(text_content, name)
            
            return {
                'name': name,
                'description': description,
                'price': price,
                'raw_text': text_content.strip(),
                'allergens': []  # Will be populated later
            }
            
        except Exception as e:
            logger.debug(f"Item extraction failed: {e}")
            return None
    
    def _extract_item_name(self, text: str) -> str:
        """Extract item name from text"""
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if lines:
            # Usually the first non-empty line is the name
            name = lines[0]
            # Remove price from name if present
            name = re.sub(r'\$\d+(?:\.\d{2})?', '', name).strip()
            return name[:100]  # Limit length
        return "Unknown Item"
    
    def _extract_price(self, text: str) -> Optional[str]:
        """Extract price from text"""
        for pattern in self.price_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        return None
    
    def _extract_description(self, text: str, name: str) -> str:
        """Extract description from text"""
        # Remove the name and price to get description
        description = text.replace(name, '', 1)
        
        # Remove price
        for pattern in self.price_patterns:
            description = re.sub(pattern, '', description)
        
        # Clean up
        description = re.sub(r'\s+', ' ', description).strip()
        return description[:500]  # Limit length
    
    def _extract_by_text_patterns(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract menu items using text patterns"""
        items = []
        
        # Look for text that looks like menu items
        text_elements = soup.find_all(text=True)
        
        for text in text_elements:
            if text and len(text.strip()) > 10:
                # Check if text contains price patterns (good indicator of menu items)
                if any(re.search(pattern, text) for pattern in self.price_patterns):
                    item = {
                        'name': self._extract_item_name(text),
                        'description': self._extract_description(text, ''),
                        'price': self._extract_price(text),
                        'raw_text': text.strip(),
                        'allergens': []
                    }
                    if self._is_valid_menu_item(item):
                        items.append(item)
        
        return items[:10]  # Limit results
    
    def _extract_structured_data(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract menu items from structured data"""
        items = []
        
        # Look for JSON-LD structured data
        scripts = soup.find_all('script', type='application/ld+json')
        for script in scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and 'hasMenu' in data:
                    # Process restaurant menu data
                    menu_items = self._process_structured_menu(data)
                    items.extend(menu_items)
            except (json.JSONDecodeError, KeyError):
                continue
        
        # Look for microdata
        microdata_items = soup.find_all(attrs={'itemtype': re.compile(r'MenuItem|Food')})
        for item in microdata_items:
            menu_item = self._process_microdata_item(item)
            if menu_item:
                items.append(menu_item)
        
        return items
    
    def _process_structured_menu(self, data: Dict) -> List[Dict[str, Any]]:
        """Process structured menu data"""
        items = []
        # Implementation would depend on the specific structured data format
        # This is a placeholder for structured data processing
        return items
    
    def _process_microdata_item(self, element) -> Optional[Dict[str, Any]]:
        """Process microdata menu item"""
        try:
            name_elem = element.find(attrs={'itemprop': 'name'})
            desc_elem = element.find(attrs={'itemprop': 'description'})
            price_elem = element.find(attrs={'itemprop': 'price'})
            
            if name_elem:
                return {
                    'name': name_elem.get_text(strip=True),
                    'description': desc_elem.get_text(strip=True) if desc_elem else '',
                    'price': price_elem.get_text(strip=True) if price_elem else None,
                    'raw_text': element.get_text(strip=True),
                    'allergens': []
                }
        except Exception:
            pass
        return None
    
    def _is_valid_menu_item(self, item: Dict[str, Any]) -> bool:
        """Validate if extracted data represents a valid menu item"""
        if not item or not item.get('name'):
            return False
        
        name = item['name'].lower()
        
        # Filter out non-menu items
        invalid_patterns = [
            'submit', 'button', 'click', 'menu', 'section',
            'category', 'view', 'more', 'see', 'robot', 'verify'
        ]
        
        if any(pattern in name for pattern in invalid_patterns):
            return False
        
        # Must have reasonable length
        if len(item['name']) < 2 or len(item['name']) > 100:
            return False
        
        return True
    
    def _deduplicate_items(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate menu items"""
        seen_names = set()
        unique_items = []
        
        for item in items:
            name_key = item['name'].lower().strip()
            if name_key not in seen_names:
                seen_names.add(name_key)
                unique_items.append(item)
        
        return unique_items
    
    def _detect_allergens(self, text: str) -> List[str]:
        """Detect allergens in menu item text"""
        allergens = []
        text_lower = text.lower()
        
        for allergen, pattern in self.allergen_patterns.items():
            if re.search(pattern, text_lower):
                allergens.append(allergen)
        
        return allergens
    
    def _summarize_allergens(self, items: List[Dict[str, Any]]) -> Dict[str, int]:
        """Summarize allergen occurrences across all items"""
        allergen_counts = {}
        
        for item in items:
            for allergen in item.get('allergens', []):
                allergen_counts[allergen] = allergen_counts.get(allergen, 0) + 1
        
        return allergen_counts
    
    def _calculate_price_coverage(self, items: List[Dict[str, Any]]) -> float:
        """Calculate percentage of items with price information"""
        if not items:
            return 0.0
        
        items_with_price = sum(1 for item in items if item.get('price'))
        return round((items_with_price / len(items)) * 100, 1)

    async def _find_restaurant_website(self, restaurant_name: str, city_state: Optional[str] = None) -> Optional[str]:
        """Attempt to find the official restaurant website using Google search."""
        if not self.page:
            logger.error("Page object not available for finding restaurant website.")
            return None

        query = f"{restaurant_name} {city_state if city_state else ''} official website"
        search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        logger.info(f"Searching for official website: {query}")

        try:
            await self.page.goto(search_url, wait_until='domcontentloaded', timeout=self.timeout)
            await asyncio.sleep(random.uniform(2, 4)) # Allow search results to settle

            # Try to find a link that looks like an official website
            # This is a heuristic and might need refinement
            # Common patterns: restaurant name in domain, no platform domains (yelp, tripadvisor etc.)

            # More specific selectors for Google search results
            # Google often uses <h3> tags for titles and <a> tags within them
            possible_links = await self.page.query_selector_all('div.g a') # div.g is a common container for results

            for link_element in possible_links:
                href = await link_element.get_attribute('href')
                if not href:
                    continue

                # Basic filtering for valid, non-Google related URLs
                if not href.startswith('http') or "google.com" in href or "google.co" in href:
                    continue

                # Domain analysis (simplified)
                parsed_url = urlparse(href)
                domain = parsed_url.netloc.lower()

                # Filter out common platform domains
                platform_domains = [
                    'yelp.com', 'tripadvisor.com', 'facebook.com', 'instagram.com',
                    'doordash.com', 'grubhub.com', 'ubereats.com', 'opentable.com',
                    'allmenus.com', 'menupages.com', 'thefork.com', 'zomato.com',
                    'mapquest.com', 'yellowpages.com', 'foursquare.com'
                ]
                if any(platform in domain for platform in platform_domains):
                    continue

                # Check if restaurant name (or parts of it) is in the domain or path
                # This is a simple check, can be improved with fuzzy matching
                name_parts = [part.lower() for part in restaurant_name.split() if len(part) > 3]
                if not name_parts: # Handle cases with very short restaurant names
                    if restaurant_name.lower().replace(" ", "") in domain.replace("-","").replace(".",""):
                        logger.info(f"Found potential official website: {href}")
                        return href
                elif any(part in domain for part in name_parts) or \
                     any(part in parsed_url.path.lower() for part in name_parts):
                    logger.info(f"Found potential official website: {href}")
                    return href

            logger.warning(f"Could not reliably identify an official website for {restaurant_name}")
            return None

        except Exception as e:
            logger.error(f"Error during Google search for {restaurant_name}: {e}")
            return None
    
    async def cleanup(self):
        """Clean up browser resources"""
        try:
            if self.page:
                await self.page.close()
            if self.browser:
                await self.browser.close()
            logger.info("🧹 Browser cleanup completed")
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")

# Example usage and testing
if __name__ == "__main__":
    async def test_scraper():
        scraper = ProductionMenuScraper(headless=True)
        
        try:
            await scraper.setup_browser()
            
            # Test with a sample URL and restaurant name/location
            test_url = "https://www.yelp.com/biz/la-crepe-bistro-homer-glen" # Primary URL (e.g., Yelp)
            restaurant_name_for_search = "La Crepe Bistro"
            city_state_for_search = "Homer Glen IL"

            # For a non-Yelp example that might benefit from official site search:
            # test_url = "https://www.yelp.com/biz/some-other-restaurant-chicago" # Made up, assume this page has minimal info
            # restaurant_name_for_search = "Some Other Restaurant"
            # city_state_for_search = "Chicago IL"


            print(f"Testing with URL: {test_url}")
            print(f"Restaurant Name for official site search: {restaurant_name_for_search}, Location: {city_state_for_search}")

            result = await scraper.extract_menu_items(
                test_url,
                restaurant_name=restaurant_name_for_search,
                city_state=city_state_for_search
            )
            
            print(f"\n🎯 PRODUCTION SCRAPER TEST RESULTS:")
            print(f"Final Scraped URL: {result['url']} (Source: {result['scraped_source']})")
            print(f"Success: {result['success']}")
            print(f"Items extracted: {result['total_items']}")
            print(f"Processing time: {result['processing_time']}s")
            print(f"Extraction method: {result['extraction_method']}")
            print(f"Price coverage: {result['price_coverage']}%")
            if result.get('error'):
                print(f"Error: {result['error']}")
            
            if result['items']:
                print(f"\n📋 Sample items:")
                for i, item in enumerate(result['items'][:3], 1):
                    print(f"  {i}. {item['name']} - {item.get('price', 'No price')}")
                    if item.get('allergens'):
                        print(f"     Allergens: {', '.join(item['allergens'])}")
            
        finally:
            await scraper.cleanup()
    
    # Run the test
    asyncio.run(test_scraper())