#!/usr/bin/env python3
"""
DoorDash Menu Scraper - Phase 2 Implementation
Basic scraper structure for DoorDash restaurant menus
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

class DoorDashScraper:
    """DoorDash-specific menu scraper with platform optimizations"""
    
    def __init__(self, headless: bool = True, timeout: int = 30000):
        self.headless = headless
        self.timeout = timeout
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        
        # DoorDash-specific selectors (require live testing to refine)
        self.menu_selectors = [
            # Potential DoorDash menu item selectors
            '[data-testid="menu-item"]',
            '[data-testid="store-item"]',
            '.MenuItem',
            '.StoreItem',
            '[class*="MenuItem"]',
            '[class*="StoreItem"]',
            '[class*="menu-item"]',
            '[class*="item-card"]',
            '.item-card',
            '.menu-item-card',
            
            # Generic fallback selectors
            '.menu-item', '.dish', '.food-item',
            '[class*="item"][class*="card"]',
            'div[role="button"][class*="item"]'
        ]
        
        # DoorDash-specific price patterns
        self.price_patterns = [
            r'\$\d+\.\d{2}',  # $12.99
            r'\$\d+',         # $12
            r'\d+\.\d{2}',    # 12.99 (without $)
            r'Price:\s*\$?\d+(?:\.\d{2})?'  # Price: $12.99
        ]
        
        # DoorDash navigation patterns
        self.navigation_selectors = {
            'menu_section': '[data-testid="menu-category"]',
            'load_more': '[data-testid="load-more"]',
            'expand_menu': '[data-testid="expand-menu"]',
            'view_menu': 'button[class*="menu"]'
        }
    
    async def setup_browser(self) -> bool:
        """Setup browser with DoorDash-optimized configuration"""
        try:
            playwright = await async_playwright().start()
            
            # DoorDash-optimized browser setup
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
            
            # Create page with mobile-friendly settings (DoorDash is mobile-first)
            self.page = await self.browser.new_page()
            
            # Set realistic mobile viewport
            await self.page.set_viewport_size({"width": 375, "height": 812})
            
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
            
            logger.info("✅ DoorDash browser setup completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ DoorDash browser setup failed: {e}")
            return False
    
    async def navigate_to_restaurant(self, url: str, max_retries: int = 3) -> bool:
        """Navigate to DoorDash restaurant page with retry logic"""
        for attempt in range(max_retries):
            try:
                logger.info(f"🌐 Navigating to DoorDash restaurant (attempt {attempt + 1}/{max_retries})")
                
                # Random delay to appear human-like
                await asyncio.sleep(random.uniform(2, 4))
                
                # Navigate with timeout
                response = await self.page.goto(
                    url, 
                    wait_until='domcontentloaded',
                    timeout=self.timeout
                )
                
                if response and response.status == 200:
                    # Wait for DoorDash content to load
                    await asyncio.sleep(random.uniform(3, 5))
                    
                    # Check for location prompt or other modals
                    await self._handle_doordash_modals()
                    
                    # Scroll to trigger lazy loading
                    await self._scroll_to_load_content()
                    
                    logger.info("✅ DoorDash navigation successful")
                    return True
                else:
                    logger.warning(f"⚠️ HTTP {response.status if response else 'No response'}")
                    
            except Exception as e:
                logger.error(f"❌ DoorDash navigation attempt {attempt + 1} failed: {e}")
                
            if attempt < max_retries - 1:
                await asyncio.sleep(random.uniform(5, 8))
        
        return False
    
    async def _handle_doordash_modals(self):
        """Handle DoorDash-specific modals and popups"""
        try:
            # Common DoorDash modal selectors (require live testing)
            modal_selectors = [
                '[data-testid="location-modal"] button[data-testid="close"]',
                '[data-testid="promo-modal"] button[data-testid="close"]',
                'button[aria-label="Close"]',
                '.modal button[class*="close"]',
                '[role="dialog"] button'
            ]
            
            for selector in modal_selectors:
                try:
                    element = await self.page.query_selector(selector)
                    if element:
                        await element.click()
                        await asyncio.sleep(1)
                        logger.info(f"✅ Closed modal with selector: {selector}")
                        break
                except Exception:
                    continue
                    
        except Exception as e:
            logger.debug(f"Modal handling failed: {e}")
    
    async def _scroll_to_load_content(self):
        """Scroll page to trigger lazy loading of menu items"""
        try:
            # Scroll down gradually to load all menu items
            for i in range(5):
                await self.page.evaluate('window.scrollBy(0, window.innerHeight)')
                await asyncio.sleep(random.uniform(1, 2))
            
            # Scroll back to top
            await self.page.evaluate('window.scrollTo(0, 0)')
            await asyncio.sleep(1)
            
            logger.info("✅ Completed scroll loading")
            
        except Exception as e:
            logger.debug(f"Scroll loading failed: {e}")
    
    async def extract_menu_items(self, url: str) -> Dict[str, Any]:
        """Extract menu items from DoorDash restaurant page"""
        start_time = time.time()
        result = {
            'url': url,
            'platform': 'doordash',
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
            
            # Strategy 1: DoorDash-specific selectors
            for selector in self.menu_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    if elements and len(elements) > 0:
                        logger.info(f"📋 Found {len(elements)} items with selector: {selector}")
                        
                        for element in elements[:30]:  # Limit to prevent overwhelming
                            item_data = await self._extract_doordash_item(element)
                            if item_data and self._is_valid_menu_item(item_data):
                                items.append(item_data)
                        
                        if items:
                            extraction_method = f'doordash_selector: {selector}'
                            break
                            
                except Exception as e:
                    logger.debug(f"DoorDash selector {selector} failed: {e}")
                    continue
            
            # Strategy 2: Fallback text extraction
            if not items:
                items = await self._extract_by_text_patterns()
                if items:
                    extraction_method = 'text_patterns'
            
            # Process results
            if items:
                unique_items = self._deduplicate_items(items)
                
                result.update({
                    'success': True,
                    'items': unique_items,
                    'total_items': len(unique_items),
                    'extraction_method': extraction_method
                })
                
                logger.info(f"✅ Successfully extracted {len(unique_items)} DoorDash menu items")
            else:
                result['error'] = 'No menu items found'
                logger.warning("⚠️ No DoorDash menu items extracted")
                
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"❌ DoorDash extraction failed: {e}")
        
        finally:
            result['processing_time'] = round(time.time() - start_time, 2)
        
        return result
    
    async def _extract_doordash_item(self, element) -> Optional[Dict[str, Any]]:
        """Extract data from a DoorDash menu item element"""
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
            
            return {
                'name': name,
                'description': description,
                'price': price,
                'image_url': image_url,
                'raw_text': text_content.strip(),
                'platform': 'doordash'
            }
            
        except Exception as e:
            logger.debug(f"DoorDash item extraction failed: {e}")
            return None
    
    async def _extract_item_name(self, element, text_content: str) -> str:
        """Extract item name from DoorDash element"""
        try:
            # Try specific name selectors first (require live testing)
            name_selectors = [
                '[data-testid="item-name"]',
                '.item-name',
                'h3', 'h4',
                '[class*="name"]',
                '[class*="title"]'
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
            logger.debug(f"Name extraction failed: {e}")
        
        return "Unknown Item"
    
    async def _extract_item_description(self, element, text_content: str, name: str) -> str:
        """Extract item description from DoorDash element"""
        try:
            # Try specific description selectors (require live testing)
            desc_selectors = [
                '[data-testid="item-description"]',
                '.item-description',
                '.description',
                'p',
                '[class*="description"]'
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
            logger.debug(f"Description extraction failed: {e}")
        
        return ""
    
    async def _extract_item_image(self, element) -> Optional[str]:
        """Extract item image URL from DoorDash element"""
        try:
            # Try to find image within the item element
            img_element = await element.query_selector('img')
            if img_element:
                src = await img_element.get_attribute('src')
                if src and src.startswith(('http', '//', 'data:')):
                    return src
        except Exception as e:
            logger.debug(f"Image extraction failed: {e}")
        
        return None
    
    def _extract_price(self, text: str) -> Optional[str]:
        """Extract price from text using DoorDash patterns"""
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
                            'platform': 'doordash'
                        }
                        if self._is_valid_menu_item(item):
                            items.append(item)
            
        except Exception as e:
            logger.debug(f"Text pattern extraction failed: {e}")
        
        return items[:15]  # Limit results
    
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
            'order', 'delivery', 'pickup'
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
            logger.info("🧹 DoorDash scraper cleanup completed")
        except Exception as e:
            logger.error(f"❌ DoorDash cleanup failed: {e}")

# Example usage and testing
if __name__ == "__main__":
    async def test_doordash_scraper():
        scraper = DoorDashScraper(headless=True)
        
        try:
            await scraper.setup_browser()
            
            # Test with a sample DoorDash URL (replace with actual URL)
            test_url = "https://www.doordash.com/store/example-restaurant"
            result = await scraper.extract_menu_items(test_url)
            
            print(f"\n🎯 DOORDASH SCRAPER TEST RESULTS:")
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
            
            if result.get('error'):
                print(f"\n❌ Error: {result['error']}")
            
        finally:
            await scraper.cleanup()
    
    # Run the test
    asyncio.run(test_doordash_scraper())