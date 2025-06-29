#!/usr/bin/env python3
"""
Uber Eats Menu Scraper - Phase 2 Implementation
Basic scraper structure for Uber Eats restaurant menus
Requires live testing and selector refinement to be functional
"""

import asyncio
import json
import logging
import random
import re
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
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
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class UberEatsScraper:
    """Uber Eats-specific menu scraper with platform optimizations"""
    
    def __init__(self, headless: bool = True, timeout: int = 30000):
        self.headless = headless
        self.timeout = timeout
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        
        # Uber Eats-specific selectors (require live testing to refine)
        self.menu_selectors = [
            # Potential Uber Eats menu item selectors
            '[data-testid="store-item"]',
            '[data-testid="menu-item"]',
            '[data-test="store-item"]',
            '.MenuItem',
            '.StoreItem',
            '[class*="MenuItem"]',
            '[class*="StoreItem"]',
            '[class*="menu-item"]',
            '[class*="item-card"]',
            '.item-card',
            '.menu-item-card',
            
            # Uber-specific patterns
            '[data-baseweb="block"][role="button"]',
            'div[role="button"][class*="item"]',
            'li[class*="item"]',
            
            # Generic fallback selectors
            '.menu-item', '.dish', '.food-item',
            '[class*="item"][class*="card"]'
        ]
        
        # Uber Eats-specific price patterns
        self.price_patterns = [
            r'\$\d+\.\d{2}',  # $12.99
            r'\$\d+',         # $12
            r'\d+\.\d{2}',    # 12.99 (without $)
            r'Price:\s*\$?\d+(?:\.\d{2})?',  # Price: $12.99
            r'USD\s*\$?\d+(?:\.\d{2})?'     # USD $12.99
        ]
        
        # Uber Eats navigation patterns
        self.navigation_selectors = {
            'menu_section': '[data-testid="menu-category"]',
            'load_more': '[data-testid="load-more"]',
            'expand_menu': '[data-testid="expand-menu"]',
            'view_menu': 'button[class*="menu"]',
            'close_modal': '[data-testid="modal-close"]'
        }
    
    async def setup_browser(self) -> bool:
        """Setup browser with Uber Eats-optimized configuration"""
        try:
            playwright = await async_playwright().start()
            
            # Uber Eats-optimized browser setup
            self.browser = await playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--no-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-features=VizDisplayCompositor',
                    '--disable-web-security',
                    '--disable-features=TranslateUI',
                    '--disable-ipc-flooding-protection',
                    '--disable-dev-shm-usage',
                    '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                ]
            )
            
            # Create page with desktop settings (Uber Eats works well on desktop)
            self.page = await self.browser.new_page()
            
            # Set realistic desktop viewport
            await self.page.set_viewport_size({"width": 1366, "height": 768})
            
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
                
                // Override permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
            """)
            
            logger.info("✅ Uber Eats browser setup completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Uber Eats browser setup failed: {e}")
            return False
    
    async def navigate_to_restaurant(self, url: str, max_retries: int = 3) -> bool:
        """Navigate to Uber Eats restaurant page with retry logic"""
        for attempt in range(max_retries):
            try:
                logger.info(f"🌐 Navigating to Uber Eats restaurant (attempt {attempt + 1}/{max_retries})")
                
                # Random delay to appear human-like
                await asyncio.sleep(random.uniform(2, 4))
                
                # Navigate with timeout
                response = await self.page.goto(
                    url, 
                    wait_until='domcontentloaded',
                    timeout=self.timeout
                )
                
                if response and response.status == 200:
                    # Wait for Uber Eats content to load
                    await asyncio.sleep(random.uniform(3, 6))
                    
                    # Check for location prompt or other modals
                    await self._handle_ubereats_modals()
                    
                    # Wait for dynamic content
                    await self._wait_for_menu_content()
                    
                    # Scroll to trigger lazy loading
                    await self._scroll_to_load_content()
                    
                    logger.info("✅ Uber Eats navigation successful")
                    return True
                else:
                    logger.warning(f"⚠️ HTTP {response.status if response else 'No response'}")
                    
            except Exception as e:
                logger.error(f"❌ Uber Eats navigation attempt {attempt + 1} failed: {e}")
                
            if attempt < max_retries - 1:
                await asyncio.sleep(random.uniform(5, 8))
        
        return False
    
    async def _handle_ubereats_modals(self):
        """Handle Uber Eats-specific modals and popups"""
        try:
            # Common Uber Eats modal selectors (require live testing)
            modal_selectors = [
                '[data-testid="modal-close"]',
                '[data-testid="location-modal"] button',
                '[data-testid="promo-modal"] button',
                'button[aria-label="Close"]',
                'button[aria-label="Dismiss"]',
                '.modal button[class*="close"]',
                '[role="dialog"] button[aria-label*="close"]',
                'button[class*="close"][class*="modal"]'
            ]
            
            for selector in modal_selectors:
                try:
                    element = await self.page.query_selector(selector)
                    if element:
                        await element.click()
                        await asyncio.sleep(1)
                        logger.info(f"✅ Closed Uber Eats modal with selector: {selector}")
                        break
                except Exception:
                    continue
            
            # Handle location permission requests
            try:
                # Deny location access if prompted
                context = self.page.context
                await context.grant_permissions([], origin=self.page.url)
            except Exception:
                pass
                    
        except Exception as e:
            logger.debug(f"Uber Eats modal handling failed: {e}")
    
    async def _wait_for_menu_content(self):
        """Wait for menu content to load dynamically"""
        try:
            # Wait for menu items to appear
            await self.page.wait_for_selector(
                'div[role="button"], .menu-item, [class*="item"]',
                timeout=10000
            )
            
            # Additional wait for content stabilization
            await asyncio.sleep(2)
            
            logger.info("✅ Menu content loaded")
            
        except Exception as e:
            logger.debug(f"Menu content wait failed: {e}")
    
    async def _scroll_to_load_content(self):
        """Scroll page to trigger lazy loading of menu items"""
        try:
            # Scroll down gradually to load all menu items
            for i in range(6):
                await self.page.evaluate('window.scrollBy(0, window.innerHeight * 0.8)')
                await asyncio.sleep(random.uniform(1.5, 2.5))
            
            # Scroll back to top
            await self.page.evaluate('window.scrollTo(0, 0)')
            await asyncio.sleep(1)
            
            logger.info("✅ Completed Uber Eats scroll loading")
            
        except Exception as e:
            logger.debug(f"Uber Eats scroll loading failed: {e}")
    
    async def extract_menu_items(self, url: str) -> Dict[str, Any]:
        """Extract menu items from Uber Eats restaurant page"""
        start_time = time.time()
        result = {
            'url': url,
            'platform': 'ubereats',
            'success': False,
            'items': [],
            'total_items': 0,
            'processing_time': 0,
            'extraction_method': None,
            'error': None
        }
        
        try:
            # Navigate to the restaurant page
            if not await self.navigate_to_restaurant(url):
                result['error'] = 'Navigation failed'
                return result
            
            # Extract menu items using multiple strategies
            items = []
            extraction_method = None
            
            # Strategy 1: Uber Eats-specific selectors
            for selector in self.menu_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    if elements and len(elements) > 0:
                        logger.info(f"📋 Found {len(elements)} items with selector: {selector}")
                        
                        for element in elements[:35]:  # Limit to prevent overwhelming
                            item_data = await self._extract_ubereats_item(element)
                            if item_data and self._is_valid_menu_item(item_data):
                                items.append(item_data)
                        
                        if items:
                            extraction_method = f'ubereats_selector: {selector}'
                            break
                            
                except Exception as e:
                    logger.debug(f"Uber Eats selector {selector} failed: {e}")
                    continue
            
            # Strategy 2: Fallback text extraction
            if not items:
                items = await self._extract_by_text_patterns()
                if items:
                    extraction_method = 'text_patterns'
            
            # Strategy 3: JSON data extraction (Uber Eats often uses JSON)
            if not items:
                items = await self._extract_from_json_data()
                if items:
                    extraction_method = 'json_data'
            
            # Process results
            if items:
                unique_items = self._deduplicate_items(items)
                
                result.update({
                    'success': True,
                    'items': unique_items,
                    'total_items': len(unique_items),
                    'extraction_method': extraction_method
                })
                
                logger.info(f"✅ Successfully extracted {len(unique_items)} Uber Eats menu items")
            else:
                result['error'] = 'No menu items found'
                logger.warning("⚠️ No Uber Eats menu items extracted")
                
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"❌ Uber Eats extraction failed: {e}")
        
        finally:
            result['processing_time'] = round(time.time() - start_time, 2)
        
        return result
    
    async def _extract_ubereats_item(self, element) -> Optional[Dict[str, Any]]:
        """Extract data from an Uber Eats menu item element"""
        try:
            # Get text content
            text_content = await element.text_content()
            if not text_content or len(text_content.strip()) < 3:
                return None
            
            # Extract item details (requires live testing to refine)
            name = await self._extract_item_name(element, text_content)
            price = self._extract_price(text_content)
            description = await self._extract_item_description(element, text_content, name)
            
            # Try to get image URL
            image_url = await self._extract_item_image(element)
            
            # Try to get additional details
            category = await self._extract_item_category(element)
            
            return {
                'name': name,
                'description': description,
                'price': price,
                'image_url': image_url,
                'category': category,
                'raw_text': text_content.strip(),
                'platform': 'ubereats'
            }
            
        except Exception as e:
            logger.debug(f"Uber Eats item extraction failed: {e}")
            return None
    
    async def _extract_item_name(self, element, text_content: str) -> str:
        """Extract item name from Uber Eats element"""
        try:
            # Try specific name selectors first (require live testing)
            name_selectors = [
                '[data-testid="rich-text"]',
                '[data-testid="item-name"]',
                '.item-name',
                'h3', 'h4', 'h5',
                '[class*="name"]',
                '[class*="title"]',
                'span[class*="title"]',
                'div[class*="title"]'
            ]
            
            for selector in name_selectors:
                name_element = await element.query_selector(selector)
                if name_element:
                    name = await name_element.text_content()
                    if name and len(name.strip()) > 0:
                        return name.strip()[:100]
            
            # Fallback to first line of text
            lines = [line.strip() for line in text_content.split('\n') if line.strip()]
            if lines:
                name = lines[0]
                # Remove price from name if present
                name = re.sub(r'\$\d+(?:\.\d{2})?', '', name).strip()
                return name[:100]
                
        except Exception as e:
            logger.debug(f"Uber Eats name extraction failed: {e}")
        
        return "Unknown Item"
    
    async def _extract_item_description(self, element, text_content: str, name: str) -> str:
        """Extract item description from Uber Eats element"""
        try:
            # Try specific description selectors (require live testing)
            desc_selectors = [
                '[data-testid="item-description"]',
                '.item-description',
                '.description',
                'p',
                '[class*="description"]',
                'span[class*="description"]',
                'div[class*="description"]'
            ]
            
            for selector in desc_selectors:
                desc_element = await element.query_selector(selector)
                if desc_element:
                    description = await desc_element.text_content()
                    if description and len(description.strip()) > 0:
                        return description.strip()[:500]
            
            # Fallback to text processing
            description = text_content.replace(name, '', 1)
            for pattern in self.price_patterns:
                description = re.sub(pattern, '', description)
            
            description = re.sub(r'\s+', ' ', description).strip()
            return description[:500]
            
        except Exception as e:
            logger.debug(f"Uber Eats description extraction failed: {e}")
        
        return ""
    
    async def _extract_item_image(self, element) -> Optional[str]:
        """Extract item image URL from Uber Eats element"""
        try:
            # Try to find image within the item element
            img_element = await element.query_selector('img')
            if img_element:
                src = await img_element.get_attribute('src')
                if src and src.startswith(('http', '//', 'data:')):
                    return src
                
                # Try srcset for higher quality images
                srcset = await img_element.get_attribute('srcset')
                if srcset:
                    # Extract first URL from srcset
                    urls = re.findall(r'(https?://[^\s,]+)', srcset)
                    if urls:
                        return urls[0]
        except Exception as e:
            logger.debug(f"Uber Eats image extraction failed: {e}")
        
        return None
    
    async def _extract_item_category(self, element) -> Optional[str]:
        """Extract item category from Uber Eats element"""
        try:
            # Look for category information in parent elements
            parent = element
            for _ in range(3):  # Check up to 3 levels up
                parent = await parent.query_selector('xpath=..')
                if parent:
                    category_element = await parent.query_selector('[class*="category"], [class*="section"]')
                    if category_element:
                        category = await category_element.text_content()
                        if category and len(category.strip()) > 0:
                            return category.strip()[:50]
        except Exception as e:
            logger.debug(f"Uber Eats category extraction failed: {e}")
        
        return None
    
    def _extract_price(self, text: str) -> Optional[str]:
        """Extract price from text using Uber Eats patterns"""
        for pattern in self.price_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        return None
    
    async def _extract_by_text_patterns(self) -> List[Dict[str, Any]]:
        """Fallback extraction using text patterns"""
        items = []
        
        try:
            # Get all text content
            content = await self.page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Look for text that contains price patterns
            text_elements = soup.find_all(text=True)
            
            for text in text_elements:
                if text and len(text.strip()) > 10:
                    if any(re.search(pattern, text) for pattern in self.price_patterns):
                        item = {
                            'name': self._extract_name_from_text(text),
                            'description': '',
                            'price': self._extract_price(text),
                            'raw_text': text.strip(),
                            'platform': 'ubereats'
                        }
                        if self._is_valid_menu_item(item):
                            items.append(item)
            
        except Exception as e:
            logger.debug(f"Uber Eats text pattern extraction failed: {e}")
        
        return items[:15]  # Limit results
    
    async def _extract_from_json_data(self) -> List[Dict[str, Any]]:
        """Extract menu items from JSON data (Uber Eats often uses JSON)"""
        items = []
        
        try:
            # Look for JSON data in script tags
            content = await self.page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string and 'menu' in script.string.lower():
                    try:
                        # Try to extract JSON data
                        json_match = re.search(r'\{.*"menu".*\}', script.string, re.DOTALL)
                        if json_match:
                            data = json.loads(json_match.group(0))
                            # Process JSON data (implementation depends on actual structure)
                            json_items = self._process_json_menu_data(data)
                            items.extend(json_items)
                    except (json.JSONDecodeError, Exception):
                        continue
            
        except Exception as e:
            logger.debug(f"Uber Eats JSON extraction failed: {e}")
        
        return items[:20]  # Limit results
    
    def _process_json_menu_data(self, data: Dict) -> List[Dict[str, Any]]:
        """Process JSON menu data (placeholder - requires actual data structure)"""
        items = []
        
        # This is a placeholder implementation
        # Actual implementation would depend on Uber Eats JSON structure
        try:
            if isinstance(data, dict):
                # Look for menu items in various possible structures
                for key, value in data.items():
                    if isinstance(value, list) and key.lower() in ['items', 'menu', 'products']:
                        for item_data in value:
                            if isinstance(item_data, dict) and 'name' in item_data:
                                item = {
                                    'name': item_data.get('name', ''),
                                    'description': item_data.get('description', ''),
                                    'price': item_data.get('price', ''),
                                    'platform': 'ubereats'
                                }
                                items.append(item)
        except Exception as e:
            logger.debug(f"JSON processing failed: {e}")
        
        return items
    
    def _extract_name_from_text(self, text: str) -> str:
        """Extract item name from raw text"""
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if lines:
            name = lines[0]
            name = re.sub(r'\$\d+(?:\.\d{2})?', '', name).strip()
            return name[:100]
        return "Unknown Item"
    
    def _is_valid_menu_item(self, item: Dict[str, Any]) -> bool:
        """Validate if extracted data represents a valid menu item"""
        if not item or not item.get('name'):
            return False
        
        name = item['name'].lower()
        
        # Filter out non-menu items
        invalid_patterns = [
            'submit', 'button', 'click', 'menu', 'section',
            'category', 'view', 'more', 'see', 'add to cart',
            'order', 'delivery', 'pickup', 'uber', 'eats',
            'restaurant', 'store', 'location'
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
    
    async def cleanup(self):
        """Clean up browser resources"""
        try:
            if self.page:
                await self.page.close()
            if self.browser:
                await self.browser.close()
            logger.info("🧹 Uber Eats scraper cleanup completed")
        except Exception as e:
            logger.error(f"❌ Uber Eats cleanup failed: {e}")

# Example usage and testing
if __name__ == "__main__":
    async def test_ubereats_scraper():
        scraper = UberEatsScraper(headless=True)
        
        try:
            await scraper.setup_browser()
            
            # Test with a sample Uber Eats URL (replace with actual URL)
            test_url = "https://www.ubereats.com/store/example-restaurant"
            result = await scraper.extract_menu_items(test_url)
            
            print(f"\n🎯 UBER EATS SCRAPER TEST RESULTS:")
            print(f"Success: {result['success']}")
            print(f"Items extracted: {result['total_items']}")
            print(f"Processing time: {result['processing_time']}s")
            print(f"Extraction method: {result['extraction_method']}")
            
            if result['items']:
                print(f"\n📋 Sample items:")
                for i, item in enumerate(result['items'][:3], 1):
                    print(f"  {i}. {item['name']} - {item.get('price', 'No price')}")
                    if item.get('description'):
                        print(f"     Description: {item['description'][:100]}...")
                    if item.get('category'):
                        print(f"     Category: {item['category']}")
            
            if result.get('error'):
                print(f"\n❌ Error: {result['error']}")
            
        finally:
            await scraper.cleanup()
    
    # Run the test
    asyncio.run(test_ubereats_scraper())