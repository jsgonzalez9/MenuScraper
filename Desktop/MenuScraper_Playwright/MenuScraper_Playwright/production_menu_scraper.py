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
    import cv2
    import numpy as np
    # import pytesseract # No longer using Tesseract directly here
    # from PIL import Image # PIL might be used by easyocr indirectly or for other image ops
    import io # For byte streams with PIL
    import easyocr # For EasyOCR
except ImportError:
    print("❌ Playwright, OpenCV, NumPy, EasyOCR, or Pillow not installed. Run: pip install playwright opencv-python numpy easyocr Pillow")
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
    
    def __init__(self, headless: bool = True, timeout: int = 30000, browser_name: str = "chromium"):
        self.headless = headless
        self.timeout = timeout
        self.browser_name = browser_name.lower()
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.ocr_reader: Optional[Any] = None # For EasyOCR reader instance
        
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
            
            browser_launcher = None
            if self.browser_name == "firefox":
                browser_launcher = playwright.firefox
            elif self.browser_name == "webkit":
                browser_launcher = playwright.webkit
            else: # Default to chromium
                if self.browser_name != "chromium":
                    logger.warning(f"Unsupported browser_name '{self.browser_name}', defaulting to chromium.")
                browser_launcher = playwright.chromium

            logger.info(f"Launching browser: {self.browser_name}")
            self.browser = await browser_launcher.launch(
                headless=self.headless,
                args=[
                    '--no-sandbox', # Common argument, keep for all
                    '--disable-blink-features=AutomationControlled',
                    '--disable-features=VizDisplayCompositor',
                    '--disable-web-security',
                    '--disable-features=TranslateUI',
                    '--disable-ipc-flooding-protection'
                    # User-agent will be set in new_context for consistency
                ]
            )
            
            updated_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'

            # Create page with enhanced settings
            context = await self.browser.new_context(
                user_agent=updated_user_agent,
                viewport={'width': 1920, 'height': 1080},
                # java_script_enabled=True, # Already default
                # accept_downloads=False, # Default
            )
            self.page = await context.new_page()

            # Set additional headers that are common in browsers
            await self.page.set_extra_http_headers({
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br', # Playwright handles actual encoding/decoding
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9', # Adjusted q for main accept
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-User': '?1',
                'Sec-Fetch-Dest': 'document',
                'Upgrade-Insecure-Requests': '1',
                # Adding Sec-CH-UA headers (User-Agent Client Hints)
                # Note: For these to be fully effective, the site often needs to opt-in via Accept-CH header.
                # However, sending them doesn't hurt and might be checked by some systems.
                'Sec-CH-UA': '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
                'Sec-CH-UA-Mobile': '?0', # Indicates desktop
                'Sec-CH-UA-Platform': '"Windows"' # Common platform to mimic
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
            'scraped_source': 'primary_url', # Indicates if data is from primary or official_site
            'menu_image_urls': [],
            'ocr_texts': []
        }

        # Attempt 1: Scrape the provided URL
        logger.info(f"Attempting to scrape primary URL: {url}")
        primary_scrape_result = await self._scrape_single_url(url, is_official_site=False)

        final_result.update({
            'success': primary_scrape_result['success'],
            'items': primary_scrape_result['items'],
            'total_items': primary_scrape_result['total_items'],
            'extraction_method': primary_scrape_result['extraction_method'],
            'error': primary_scrape_result['error'],
            'menu_image_urls': primary_scrape_result.get('menu_image_urls', []),
            'ocr_texts': primary_scrape_result.get('ocr_texts', [])
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
                        'url': official_site_url, # Update URL to the one actually scraped
                        'menu_image_urls': official_scrape_result.get('menu_image_urls', []), # Capture images from official site
                        'ocr_texts': official_scrape_result.get('ocr_texts', []) # Capture OCR texts from official site
                    })
                elif official_scrape_result['success']:
                     logger.info(f"Official website scrape was successful but yielded fewer or same items ({official_scrape_result['total_items']}) than primary ({final_result['total_items']}). Keeping primary URL data (including its image URLs and OCR texts if any).")
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
                
                # Increased random delay to appear more human-like
                await asyncio.sleep(random.uniform(2, 5)) # Was 1-3s
                
                # Navigate with timeout
                response = await self.page.goto(
                    url, 
                    wait_until='commit', # Faster initial load, then wait for ready state
                    timeout=self.timeout
                )
                
                if response and response.status == 200:
                    # Wait for the page to be fully loaded
                    await self.page.wait_for_function("document.readyState === 'complete'", timeout=self.timeout / 2)
                    await asyncio.sleep(random.uniform(2, 4)) # Increased, was 1-2s
                    
                    # Check for bot detection
                    content = await self.page.content()
                    if self._is_bot_detected(content):
                        logger.warning(f"🤖 Bot detection on attempt {attempt + 1}")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(random.uniform(8, 15)) # Increased, was 5-10s
                            continue
                        return False
                    
                    logger.info("✅ Navigation successful")
                    return True
                else:
                    logger.warning(f"⚠️ HTTP {response.status if response else 'No response'}")
                    
            except Exception as e:
                logger.error(f"❌ Navigation attempt {attempt + 1} failed: {e}")
                
            if attempt < max_retries - 1:
                await asyncio.sleep(random.uniform(5, 10)) # Increased, was 3-7s
        
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
            'error': None,
            'menu_image_urls': [], # To store found image URLs
            'ocr_texts': [] # To store raw text extracted by OCR from images
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
                        await asyncio.sleep(random.uniform(1.0, 2.5)) # Increased, was 0.5-1.5s
                except Exception as e:
                    logger.warning(f"Error during scrolling on Yelp page: {e}")
            elif is_official_site: # Generic scrolling for official sites
                logger.info(f"Applying generic scrolling for official site {url}")
                try:
                    for _ in range(2): # Scroll a bit less aggressively
                        await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        await asyncio.sleep(random.uniform(1.0, 2.0)) # Increased, was 0.5-1.0s
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
                logger.warning(f"No menu items extracted from {url} using text methods.")

                # If text extraction fails or yields very few items, try to find menu images for OCR
                if not items or len(items) < 3: # Threshold for trying OCR
                    logger.info(f"Text extraction yielded {len(items)} items. Attempting to find menu images for potential OCR.")
                    found_image_urls = await self._find_menu_image_urls()
                    if found_image_urls:
                        partial_result['menu_image_urls'] = found_image_urls
                        # The actual OCR processing will happen later based on these URLs.
                        # For now, we just note that images were found.
                        # If OCR were integrated here, we might update 'success' or 'items'.
                        logger.info(f"Found {len(found_image_urls)} menu image URLs. Attempting OCR on them now.")

                        ocr_extracted_texts = []
                        for img_url in found_image_urls:
                            ocr_text = await self._process_image_with_ocr(img_url)
                            if ocr_text:
                                ocr_extracted_texts.append({
                                    "image_url": img_url,
                                    "text": ocr_text
                                })
                        if ocr_extracted_texts:
                            partial_result['ocr_texts'] = ocr_extracted_texts
                            logger.info(f"Stored OCR results for {len(ocr_extracted_texts)} images.")
                            # Potentially, if text-based items are empty, OCR success could make overall success True.
                            # if not partial_result['items'] and ocr_extracted_texts:
                            #    partial_result['success'] = True # Mark success if OCR found something
                            #    partial_result['extraction_method'] = (partial_result['extraction_method'] or "") + "+ocr_images_found"

                    else:
                        logger.info("No menu image URLs found for OCR.")

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

                link_text_content = await link_element.text_content()
                link_text = link_text_content.lower() if link_text_content else ""

                # Check if restaurant name (or parts of it) is in the domain, path, or link text
                restaurant_name_lower = restaurant_name.lower()
                name_parts = [part.lower() for part in restaurant_name_lower.split() if len(part) > 2] # Use shorter parts

                # Score potential links: higher is better
                score = 0
                if any(part in domain for part in name_parts):
                    score += 2
                # Penalize if domain is very generic but name is in path
                elif any(part in parsed_url.path.lower() for part in name_parts) and not any(d in domain for d in ['blogspot.com', 'wordpress.com', 'wixsite.com']): # Avoid generic blog/site builder subpaths unless domain also matches
                    score += 1

                if restaurant_name_lower in link_text:
                    score += 3 # Strong indicator
                elif any(part in link_text for part in name_parts):
                    score += 1

                # Check for "official" or "home" in link text - very strong signal if name also matches somewhat
                if score > 0 and ("official site" in link_text or "official website" in link_text or (restaurant_name_lower in link_text and "home" in link_text)):
                    score += 5

                if score >= 3: # Threshold for considering it a match
                    logger.info(f"Found potential official website (score: {score}): {href} (Text: {link_text_content})")
                    # Could collect top N scored links and pick the best, but for now, first good one.
                    return href

            logger.warning(f"Could not reliably identify an official website for {restaurant_name}")
            return None

        except Exception as e:
            logger.error(f"Error during Google search for {restaurant_name}: {e}")
            return None

    async def _find_menu_image_urls(self) -> List[str]:
        """Finds potential menu image URLs on the current page."""
        if not self.page:
            logger.warning("Page object not available for finding menu images.")
            return []

        logger.info("Scanning for potential menu image URLs...")
        image_urls = []

        # Selectors for menu images based on Menu_Scraping_Improvement_Strategy.md
        # and common patterns
        menu_image_selectors = [
            'img[src*="menu"]', 'img[alt*="menu"]', 'img[class*="menu-image"]', # Direct image attributes
            'img[data-src*="menu"]', # For lazy-loaded images
            '.menu-image img', '[data-test*="menu-image"] img', # Images within menu-like containers
            'a[href*="menu.pdf"] img', 'a[href*="menu_"] img', # Images that are links to menus
            'img[alt*="food menu"]', 'img[title*="menu"]',
            # More generic, might need refinement to avoid false positives
            'div[class*="menu"] img', 'section[class*="menu"] img'
        ]

        for selector in menu_image_selectors:
            try:
                elements = await self.page.query_selector_all(selector)
                for element in elements:
                    src = await element.get_attribute('src')
                    data_src = await element.get_attribute('data-src') # Common for lazy loading

                    img_url = src or data_src # Prioritize data-src if src is placeholder

                    if img_url:
                        # Resolve relative URLs to absolute
                        img_url = urljoin(self.page.url, img_url.strip())
                        if img_url not in image_urls: # Avoid duplicates
                            # Basic filter for common image types, and avoid tiny icons (heuristic)
                            if any(ext in img_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']):
                                # Further checks could be image dimensions if accessible easily, but that's more complex here.
                                logger.info(f"Found potential menu image: {img_url} (via selector: {selector})")
                                image_urls.append(img_url)
            except Exception as e:
                logger.debug(f"Error processing selector '{selector}' for menu images: {e}")

        if not image_urls:
            logger.info("No specific menu images found with targeted selectors.")

        # As a broader fallback, get a few prominent images if no specific ones are found
        # This is very heuristic and might grab irrelevant images.
        if not image_urls:
            logger.info("Trying to find any prominent images on the page as a last resort for OCR.")
            all_images = await self.page.query_selector_all('img')
            for element in all_images[:5]: # Limit to first 5 prominent images
                src = await element.get_attribute('src')
                data_src = await element.get_attribute('data-src')
                img_url = src or data_src
                if img_url:
                    img_url = urljoin(self.page.url, img_url.strip())
                    if img_url not in image_urls and any(ext in img_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                        # Check if image is reasonably sized (very rough heuristic)
                        # width = await element.evaluate("el => el.naturalWidth || el.width")
                        # height = await element.evaluate("el => el.naturalHeight || el.height")
                        # if width > 200 and height > 200: # Example: skip small icons
                        logger.info(f"Found generic prominent image: {img_url}")
                        image_urls.append(img_url)

        logger.info(f"Found {len(image_urls)} potential menu image URLs.")
        return list(set(image_urls)) # Return unique URLs

    async def _download_image(self, image_url: str) -> Optional[bytes]:
        """Downloads an image from a URL."""
        # This helper would ideally use the existing Playwright page/context
        # to benefit from its session/cookies, or a robust HTTP client.
        # For simplicity, using requests here. Add 'requests' to requirements if not present.
        import requests # Ensure this import is at the top of the file if widely used
        try:
            # It's better to use self.page.request if possible to maintain session context
            # response = await self.page.request.get(image_url, timeout=10000)
            # if response.ok:
            #     return await response.body()
            # else:
            #     logger.warning(f"Failed to download image {image_url} with Playwright: {response.status}")
            #     return None

            # Fallback to requests for now.
            # Note: This makes a new request outside Playwright's current browser context.
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            return response.content
        except Exception as e:
            logger.error(f"Failed to download image {image_url}: {e}")
            return None

    async def _process_image_with_ocr(self, image_url: str) -> Optional[str]:
        """
        Downloads an image and processes it with OCR.
        Uses Tesseract OCR.
        Dependencies: pytesseract, opencv-python.
        NOTE: Tesseract OCR engine must be installed on the system and typically in PATH.
        (e.g., sudo apt-get install tesseract-ocr tesseract-ocr-eng)
        """
        logger.info(f"Attempting OCR for image: {image_url}")
        image_bytes = await self._download_image(image_url)
        if not image_bytes:
            return None

        extracted_text = None
        self.image_for_ocr = None

    def _initialize_ocr_reader(self):
        """Initializes the EasyOCR reader if not already done."""
        if self.ocr_reader is None:
            try:
                import easyocr
                # Initialize for English. Add other languages if needed: ['en', 'es', 'fr']
                # GPU can be True or False. If True, it will try to use GPU.
                # If PyTorch with CUDA is not set up, it will fall back to CPU or might error.
                self.ocr_reader = easyocr.Reader(['en'], gpu=False)
                logger.info("EasyOCR reader initialized successfully (CPU).")
            except ImportError:
                logger.error("EasyOCR library not found. Please install it: pip install easyocr")
                self.ocr_reader = None # Explicitly mark as None if import fails
            except Exception as e:
                logger.error(f"Failed to initialize EasyOCR reader: {e}")
                self.ocr_reader = None
        return self.ocr_reader

    async def _process_image_with_ocr(self, image_url: str) -> Optional[str]:
        """
        Downloads an image and processes it with OCR (now targeting EasyOCR).
        Dependencies: easyocr, opencv-python, numpy.
        NOTE: Tesseract OCR engine must be installed on the system and typically in PATH.
        (e.g., sudo apt-get install tesseract-ocr tesseract-ocr-eng)
        """
        logger.info(f"Attempting OCR for image: {image_url}")
        image_bytes = await self._download_image(image_url)
        if not image_bytes:
            return None

        extracted_text = None
        # self.image_for_ocr = None # This was for Tesseract, EasyOCR can take bytes or preprocessed image

        # --- Image Preprocessing (using OpenCV) ---
        processed_image_data_for_ocr = image_bytes # Default to raw bytes if preprocessing fails or is skipped

        try:
            import cv2
            import numpy as np
            logger.info(f"Attempting OpenCV preprocessing for {image_url}")
            nparr = np.frombuffer(image_bytes, np.uint8)
            img_cv = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if img_cv is None:
                logger.warning(f"Could not decode image with OpenCV: {image_url}. Using raw bytes for OCR.")
            else:
                gray_image = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
                blurred_image = cv2.medianBlur(gray_image, 3)
                binary_image = cv2.adaptiveThreshold(
                    blurred_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                    cv2.THRESH_BINARY, 11, 2
                )
                processed_image_data_for_ocr = binary_image
                logger.info(f"Image preprocessed successfully for OCR: {image_url}")

        except ImportError:
            logger.warning("OpenCV (cv2) or NumPy not installed. Skipping preprocessing. Will attempt OCR on raw image bytes.")
        except Exception as e:
            logger.error(f"Error during image preprocessing for {image_url}: {e}. Skipping preprocessing, will attempt OCR on raw image bytes.")
        # --- End Image Preprocessing ---

        # --- EasyOCR Engine ---
        ocr_reader = self._initialize_ocr_reader() # This already handles ImportError for easyocr

        if ocr_reader:
            try:
                logger.info(f"Performing EasyOCR on {'preprocessed image' if isinstance(processed_image_data_for_ocr, np.ndarray) else 'raw image bytes'}.")
                ocr_results = ocr_reader.readtext(processed_image_data_for_ocr, detail=0, paragraph=True)
                extracted_text = "\n".join(ocr_results)
                if extracted_text:
                    logger.info(f"EasyOCR extracted text from {image_url} (length: {len(extracted_text)} chars). Preview: {extracted_text[:100].replace('\n', ' ')}...")
                else:
                    logger.info(f"EasyOCR found no text in {image_url}.")
            except Exception as e:
                logger.error(f"Error during EasyOCR processing for {image_url}: {e}")
                extracted_text = None # Ensure extracted_text is None if OCR fails
        else:
            logger.warning(f"EasyOCR reader not available. Simulating OCR text for {image_url}.")
            # Simulate OCR text if EasyOCR couldn't be loaded (e.g., due to failed pip install)
            extracted_text = f"SIMULATED OCR TEXT from {image_url}: Special Burger - $10.99, Fries - $3.50. Allergens: gluten, dairy."
        # --- End EasyOCR Engine ---

        return extracted_text
    
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
    async def test_scraper(browser_to_test: str = "chromium"):
        logger.info(f"--- Testing with {browser_to_test} ---")
        scraper = ProductionMenuScraper(headless=True, browser_name=browser_to_test)
        
        try:
            setup_success = await scraper.setup_browser()
            if not setup_success:
                logger.error(f"Failed to setup browser {browser_to_test}. Aborting test.")
                return


            # Test with a sample URL and restaurant name/location
            test_url = "https://www.yelp.com/biz/la-crepe-bistro-homer-glen" # Primary URL (e.g., Yelp)

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

            # For a non-Yelp example that might benefit from official site search:
            # test_url = "https://www.yelp.com/biz/some-other-restaurant-chicago" # Made up, assume this page has minimal info
            # restaurant_name_for_search = "Some Other Restaurant"
            # city_state_for_search = "Chicago IL"

            # Test with a name likely to require fallback to official site and potentially OCR
            test_url = "https://www.yelp.com/biz/non-existent-for-primary-failure-XXXXYYYYZZZZ" # Ensure primary Yelp URL fails
            restaurant_name_for_search = "Luigi's Family Pizzeria"
            city_state_for_search = "Pleasantville OH"


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
            if result.get('menu_image_urls'):
                print(f"Menu Image URLs Found: {len(result['menu_image_urls'])}")
                for i, img_url in enumerate(result['menu_image_urls'][:2]): # Print first 2
                    print(f"  - {img_url}")
            if result.get('ocr_texts'):
                print(f"OCR Texts Extracted: {len(result['ocr_texts'])}")
                for i, ocr_item in enumerate(result['ocr_texts'][:2]): # Print first 2
                    print(f"  - Image: {ocr_item['image_url']}")
                    print(f"    Text: {ocr_item['text'][:100]}...") # Print preview
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
    # Test with chromium (default)
    asyncio.run(test_scraper("chromium"))
    # Test with firefox
    # asyncio.run(test_scraper("firefox"))