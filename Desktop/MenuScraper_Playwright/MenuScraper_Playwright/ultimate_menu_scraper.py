#!/usr/bin/env python3
"""
Ultimate Menu Scraper - Advanced Version with Anti-Bot Detection
Designed to achieve 50%+ success rate with sophisticated extraction strategies
"""

import re
import time
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urljoin, urlparse
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UltimateMenuScraper:
    """Ultimate menu scraper with advanced anti-detection and extraction capabilities"""
    
    def __init__(self):
        self.menu_keywords = [
            'menu', 'food', 'dining', 'cuisine', 'dishes', 'entrees', 'appetizers',
            'desserts', 'beverages', 'drinks', 'specials', 'breakfast', 'lunch',
            'dinner', 'brunch', 'takeout', 'delivery', 'order', 'eat'
        ]
        
        self.bot_detection_phrases = [
            'robot', 'captcha', 'verify', 'human', 'security check',
            'please wait', 'loading', 'checking your browser',
            'cloudflare', 'ddos protection', 'access denied'
        ]
        
        self.price_patterns = [
            r'\$\d+(?:\.\d{2})?',
            r'\d+(?:\.\d{2})?\s*(?:dollars?|usd|\$)',
            r'\b\d{1,3}(?:,\d{3})*(?:\.\d{2})?\b',
        ]
        
        self.food_categories = {
            'appetizer': ['appetizer', 'starter', 'small plate', 'shareables', 'apps'],
            'entree': ['entree', 'main', 'dinner', 'lunch', 'sandwich', 'burger', 'pasta', 'pizza'],
            'dessert': ['dessert', 'sweet', 'cake', 'ice cream', 'pie'],
            'beverage': ['drink', 'beverage', 'coffee', 'tea', 'soda', 'juice', 'beer', 'wine'],
            'salad': ['salad', 'greens'],
            'soup': ['soup', 'bisque', 'chowder']
        }
    
    def setup_stealth_browser(self, page: Page) -> None:
        """Configure browser to avoid detection"""
        try:
            # Set realistic user agent
            page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            })
            
            # Add stealth scripts
            page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
                
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en'],
                });
                
                window.chrome = {
                    runtime: {},
                };
            """)
            
        except Exception as e:
            logger.warning(f"Could not setup stealth mode: {e}")
    
    def detect_bot_protection(self, page: Page) -> bool:
        """Detect if page has bot protection"""
        try:
            page_text = page.content().lower()
            
            for phrase in self.bot_detection_phrases:
                if phrase in page_text:
                    logger.info(f"Bot detection phrase found: {phrase}")
                    return True
            
            # Check for common bot protection elements
            protection_selectors = [
                '[data-cf-beacon]',  # Cloudflare
                '.cf-browser-verification',
                '#challenge-form',
                '.captcha',
                '[data-recaptcha]'
            ]
            
            for selector in protection_selectors:
                if page.query_selector(selector):
                    logger.info(f"Bot protection element found: {selector}")
                    return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Error detecting bot protection: {e}")
            return False
    
    def bypass_bot_protection(self, page: Page) -> bool:
        """Attempt to bypass bot protection"""
        try:
            logger.info("Attempting to bypass bot protection...")
            
            # Wait for potential redirects
            time.sleep(3)
            
            # Try clicking through common protection screens
            bypass_selectors = [
                'button[type="submit"]',
                '.cf-browser-verification button',
                '#challenge-form button',
                'input[type="submit"]'
            ]
            
            for selector in bypass_selectors:
                try:
                    element = page.query_selector(selector)
                    if element and element.is_visible():
                        logger.info(f"Clicking bypass element: {selector}")
                        element.click()
                        page.wait_for_load_state('networkidle', timeout=10000)
                        time.sleep(2)
                        break
                except:
                    continue
            
            # Check if bypass was successful
            return not self.detect_bot_protection(page)
            
        except Exception as e:
            logger.warning(f"Error bypassing bot protection: {e}")
            return False
    
    def find_menu_links(self, page: Page) -> List[str]:
        """Find potential menu page links"""
        menu_links = []
        
        try:
            # Look for menu-related links
            links = page.query_selector_all('a[href]')
            
            for link in links:
                try:
                    href = link.get_attribute('href')
                    text = link.inner_text().lower().strip()
                    
                    if not href or not text:
                        continue
                    
                    # Check if link text contains menu keywords
                    for keyword in self.menu_keywords:
                        if keyword in text and len(text) < 50:
                            full_url = urljoin(page.url, href)
                            if full_url not in menu_links:
                                menu_links.append(full_url)
                                logger.info(f"Found menu link: {text} -> {full_url}")
                            break
                    
                except Exception as e:
                    continue
            
            return menu_links[:5]  # Limit to top 5 candidates
            
        except Exception as e:
            logger.warning(f"Error finding menu links: {e}")
            return []
    
    def extract_structured_data(self, page: Page) -> List[Dict[str, Any]]:
        """Extract menu items from structured data (JSON-LD, microdata)"""
        items = []
        
        try:
            # Extract JSON-LD structured data
            scripts = page.query_selector_all('script[type="application/ld+json"]')
            
            for script in scripts:
                try:
                    content = script.inner_text()
                    data = json.loads(content)
                    
                    # Handle different schema types
                    if isinstance(data, list):
                        for item in data:
                            items.extend(self._extract_from_schema(item))
                    else:
                        items.extend(self._extract_from_schema(data))
                        
                except Exception as e:
                    continue
            
            # Extract microdata
            microdata_items = page.query_selector_all('[itemtype*="schema.org"]')
            for item in microdata_items:
                try:
                    items.extend(self._extract_from_microdata(item))
                except Exception as e:
                    continue
            
            return items
            
        except Exception as e:
            logger.warning(f"Error extracting structured data: {e}")
            return []
    
    def _extract_from_schema(self, data: Dict) -> List[Dict[str, Any]]:
        """Extract menu items from schema.org data"""
        items = []
        
        try:
            schema_type = data.get('@type', '').lower()
            
            if 'restaurant' in schema_type or 'foodestablishment' in schema_type:
                # Look for menu in restaurant data
                menu = data.get('hasMenu', data.get('menu', {}))
                if menu:
                    items.extend(self._extract_menu_items_from_schema(menu))
            
            elif 'menu' in schema_type:
                items.extend(self._extract_menu_items_from_schema(data))
            
            elif 'menuitem' in schema_type or 'fooditem' in schema_type:
                item = self._create_menu_item_from_schema(data)
                if item:
                    items.append(item)
            
            # Recursively check nested objects
            for key, value in data.items():
                if isinstance(value, dict):
                    items.extend(self._extract_from_schema(value))
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            items.extend(self._extract_from_schema(item))
            
            return items
            
        except Exception as e:
            return []
    
    def _extract_menu_items_from_schema(self, menu_data: Dict) -> List[Dict[str, Any]]:
        """Extract items from menu schema data"""
        items = []
        
        try:
            # Look for menu sections
            sections = menu_data.get('hasMenuSection', menu_data.get('menuSection', []))
            if not isinstance(sections, list):
                sections = [sections]
            
            for section in sections:
                if isinstance(section, dict):
                    section_items = section.get('hasMenuItem', section.get('menuItem', []))
                    if not isinstance(section_items, list):
                        section_items = [section_items]
                    
                    for item_data in section_items:
                        if isinstance(item_data, dict):
                            item = self._create_menu_item_from_schema(item_data)
                            if item:
                                items.append(item)
            
            # Also check direct menu items
            direct_items = menu_data.get('hasMenuItem', menu_data.get('menuItem', []))
            if not isinstance(direct_items, list):
                direct_items = [direct_items]
            
            for item_data in direct_items:
                if isinstance(item_data, dict):
                    item = self._create_menu_item_from_schema(item_data)
                    if item:
                        items.append(item)
            
            return items
            
        except Exception as e:
            return []
    
    def _create_menu_item_from_schema(self, item_data: Dict) -> Optional[Dict[str, Any]]:
        """Create menu item from schema data"""
        try:
            name = item_data.get('name', '')
            if not name or len(name) < 2:
                return None
            
            description = item_data.get('description', '')
            
            # Extract price
            price = None
            offers = item_data.get('offers', item_data.get('offer', {}))
            if isinstance(offers, list) and offers:
                offers = offers[0]
            
            if isinstance(offers, dict):
                price_value = offers.get('price', offers.get('priceSpecification', {}).get('price'))
                if price_value:
                    price = f"${price_value}"
            
            # Determine category
            category = self._categorize_item(name, description)
            
            return {
                'name': name.strip(),
                'description': description.strip(),
                'price': price,
                'confidence': 0.9,
                'sources': ['structured_data'],
                'category': category,
                'extraction_method': 'schema_org'
            }
            
        except Exception as e:
            return None
    
    def _extract_from_microdata(self, element) -> List[Dict[str, Any]]:
        """Extract menu items from microdata elements"""
        items = []
        
        try:
            item_type = element.get_attribute('itemtype') or ''
            
            if 'MenuItem' in item_type or 'FoodItem' in item_type:
                name_elem = element.query_selector('[itemprop="name"]')
                desc_elem = element.query_selector('[itemprop="description"]')
                price_elem = element.query_selector('[itemprop="price"], [itemprop="offers"] [itemprop="price"]')
                
                if name_elem:
                    name = name_elem.inner_text().strip()
                    description = desc_elem.inner_text().strip() if desc_elem else ''
                    price = price_elem.inner_text().strip() if price_elem else None
                    
                    if name and len(name) > 1:
                        category = self._categorize_item(name, description)
                        
                        items.append({
                            'name': name,
                            'description': description,
                            'price': price,
                            'confidence': 0.8,
                            'sources': ['microdata'],
                            'category': category,
                            'extraction_method': 'microdata'
                        })
            
            return items
            
        except Exception as e:
            return []
    
    def extract_visual_menu_items(self, page: Page) -> List[Dict[str, Any]]:
        """Extract menu items using visual patterns and CSS selectors"""
        items = []
        
        try:
            # Enhanced CSS selectors for menu items
            menu_selectors = [
                # Common menu item patterns
                '.menu-item, .menuitem, .menu_item',
                '.food-item, .fooditem, .food_item',
                '.dish, .dish-item, .dish_item',
                '.product, .product-item',
                '[class*="menu"][class*="item"]',
                '[class*="food"][class*="item"]',
                
                # List-based patterns
                '.menu ul li, .menu ol li',
                '.food-menu li, .restaurant-menu li',
                
                # Card-based patterns
                '.menu-card, .food-card, .dish-card',
                
                # Table-based patterns
                '.menu-table tr, .price-list tr',
                
                # Generic containers that might contain menu items
                '[data-testid*="menu"], [data-cy*="menu"]',
                '[id*="menu"] .item, [class*="menu"] .item'
            ]
            
            for selector in menu_selectors:
                try:
                    elements = page.query_selector_all(selector)
                    
                    for element in elements[:50]:  # Limit to prevent overload
                        try:
                            item = self._extract_item_from_element(element)
                            if item and self._is_valid_menu_item(item):
                                items.append(item)
                        except Exception as e:
                            continue
                    
                    if len(items) >= 20:  # Stop if we have enough items
                        break
                        
                except Exception as e:
                    continue
            
            # If no items found, try broader text extraction
            if not items:
                items = self._extract_from_text_content(page)
            
            return items
            
        except Exception as e:
            logger.warning(f"Error extracting visual menu items: {e}")
            return []
    
    def _extract_item_from_element(self, element) -> Optional[Dict[str, Any]]:
        """Extract menu item data from a DOM element"""
        try:
            # Get text content
            text = element.inner_text().strip()
            if not text or len(text) < 3:
                return None
            
            # Skip obvious non-menu items
            skip_patterns = [
                r'\b(home|about|contact|location|hours|phone|email|address)\b',
                r'\b(facebook|twitter|instagram|social)\b',
                r'\b(copyright|privacy|terms|policy)\b',
                r'\b(login|register|account|profile)\b'
            ]
            
            text_lower = text.lower()
            for pattern in skip_patterns:
                if re.search(pattern, text_lower):
                    return None
            
            # Try to extract name, description, and price
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            if not lines:
                return None
            
            name = lines[0]
            description = ''
            price = None
            
            # Look for price in the text
            for line in lines:
                price_match = self._extract_price_from_text(line)
                if price_match:
                    price = price_match
                    break
            
            # If multiple lines, second line might be description
            if len(lines) > 1 and not price:
                description = lines[1]
            elif len(lines) > 2:
                description = lines[1]
            
            # Clean up name (remove price if it's included)
            name = re.sub(r'\$\d+(?:\.\d{2})?', '', name).strip()
            
            if len(name) < 2:
                return None
            
            category = self._categorize_item(name, description)
            
            return {
                'name': name,
                'description': description,
                'price': price,
                'confidence': 0.7,
                'sources': ['visual'],
                'category': category,
                'extraction_method': 'visual_extraction'
            }
            
        except Exception as e:
            return None
    
    def _extract_from_text_content(self, page: Page) -> List[Dict[str, Any]]:
        """Extract menu items from page text content as fallback"""
        items = []
        
        try:
            # Get page text
            text = page.inner_text()
            
            # Skip if this looks like a bot protection page
            if any(phrase in text.lower() for phrase in self.bot_detection_phrases):
                return []
            
            # Look for menu-like patterns in text
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            potential_items = []
            
            for line in lines:
                # Skip very short or very long lines
                if len(line) < 5 or len(line) > 200:
                    continue
                
                # Skip lines that look like navigation or headers
                if any(word in line.lower() for word in ['home', 'about', 'contact', 'menu', 'location']):
                    continue
                
                # Look for lines that might be menu items
                if self._looks_like_menu_item(line):
                    potential_items.append(line)
            
            # Process potential items
            for item_text in potential_items[:15]:  # Limit to prevent spam
                price = self._extract_price_from_text(item_text)
                name = re.sub(r'\$\d+(?:\.\d{2})?', '', item_text).strip()
                
                if len(name) > 2:
                    category = self._categorize_item(name, '')
                    
                    items.append({
                        'name': name,
                        'description': '',
                        'price': price,
                        'confidence': 0.5,
                        'sources': ['text'],
                        'category': category,
                        'extraction_method': 'text_content'
                    })
            
            return items
            
        except Exception as e:
            logger.warning(f"Error extracting from text content: {e}")
            return []
    
    def _looks_like_menu_item(self, text: str) -> bool:
        """Check if text looks like a menu item"""
        text_lower = text.lower()
        
        # Has price indicator
        if re.search(r'\$\d+', text):
            return True
        
        # Contains food-related words
        food_words = [
            'chicken', 'beef', 'pork', 'fish', 'salmon', 'shrimp', 'pasta', 'pizza',
            'burger', 'sandwich', 'salad', 'soup', 'steak', 'rice', 'noodles',
            'cheese', 'bread', 'sauce', 'grilled', 'fried', 'baked', 'roasted'
        ]
        
        if any(word in text_lower for word in food_words):
            return True
        
        # Looks like a dish name (title case, reasonable length)
        if text.istitle() and 10 <= len(text) <= 50:
            return True
        
        return False
    
    def _extract_price_from_text(self, text: str) -> Optional[str]:
        """Extract price from text"""
        for pattern in self.price_patterns:
            match = re.search(pattern, text)
            if match:
                price = match.group()
                if not price.startswith('$'):
                    price = f'${price}'
                return price
        return None
    
    def _categorize_item(self, name: str, description: str) -> str:
        """Categorize menu item"""
        text = f"{name} {description}".lower()
        
        for category, keywords in self.food_categories.items():
            if any(keyword in text for keyword in keywords):
                return category
        
        return 'entree'  # Default category
    
    def _is_valid_menu_item(self, item: Dict[str, Any]) -> bool:
        """Validate if item is a legitimate menu item"""
        name = item.get('name', '').lower()
        
        # Skip bot detection text
        if any(phrase in name for phrase in self.bot_detection_phrases):
            return False
        
        # Skip navigation items
        nav_words = ['home', 'about', 'contact', 'menu', 'location', 'hours', 'phone']
        if any(word in name for word in nav_words):
            return False
        
        # Skip very short names
        if len(name.strip()) < 3:
            return False
        
        # Skip items that are just numbers or symbols
        if re.match(r'^[\d\s\$\.\-]+$', name):
            return False
        
        return True
    
    def ultimate_menu_detection(self, page: Page, url: str) -> Dict[str, Any]:
        """Ultimate menu detection with all strategies"""
        start_time = time.time()
        
        result = {
            'menu_items': [],
            'total_items': 0,
            'scraping_success': False,
            'ocr_used': False,
            'menu_page_found': False,
            'source': 'ultimate_scraping',
            'strategies_used': 0,
            'raw_candidates': 0,
            'processing_time': 0,
            'extraction_methods': [],
            'quality_score': 0.0
        }
        
        try:
            logger.info(f"Starting ultimate menu detection for: {url}")
            
            # Setup stealth mode
            self.setup_stealth_browser(page)
            
            # Navigate to URL
            try:
                page.goto(url, wait_until='networkidle', timeout=25000)
                time.sleep(2)
            except Exception as e:
                result['error'] = f"Navigation failed: {str(e)}"
                return result
            
            # Check for bot protection
            if self.detect_bot_protection(page):
                logger.info("Bot protection detected, attempting bypass...")
                if not self.bypass_bot_protection(page):
                    result['error'] = "Could not bypass bot protection"
                    return result
            
            all_items = []
            extraction_methods = []
            
            # Strategy 1: Extract structured data
            logger.info("Trying structured data extraction...")
            structured_items = self.extract_structured_data(page)
            if structured_items:
                all_items.extend(structured_items)
                extraction_methods.append('structured')
                result['strategies_used'] += 1
                logger.info(f"Found {len(structured_items)} items via structured data")
            
            # Strategy 2: Extract from current page
            logger.info("Trying visual extraction on current page...")
            visual_items = self.extract_visual_menu_items(page)
            if visual_items:
                all_items.extend(visual_items)
                extraction_methods.append('visual')
                result['strategies_used'] += 1
                logger.info(f"Found {len(visual_items)} items via visual extraction")
            
            # Strategy 3: Try menu links if not enough items
            if len(all_items) < 5:
                logger.info("Searching for dedicated menu pages...")
                menu_links = self.find_menu_links(page)
                
                for menu_url in menu_links:
                    try:
                        logger.info(f"Trying menu page: {menu_url}")
                        page.goto(menu_url, wait_until='networkidle', timeout=15000)
                        time.sleep(1)
                        
                        result['menu_page_found'] = True
                        
                        # Try structured data on menu page
                        menu_structured = self.extract_structured_data(page)
                        if menu_structured:
                            all_items.extend(menu_structured)
                            if 'structured' not in extraction_methods:
                                extraction_methods.append('structured')
                                result['strategies_used'] += 1
                        
                        # Try visual extraction on menu page
                        menu_visual = self.extract_visual_menu_items(page)
                        if menu_visual:
                            all_items.extend(menu_visual)
                            if 'visual' not in extraction_methods:
                                extraction_methods.append('visual')
                                result['strategies_used'] += 1
                        
                        if len(all_items) >= 10:  # Stop if we have enough
                            break
                            
                    except Exception as e:
                        logger.warning(f"Error accessing menu page {menu_url}: {e}")
                        continue
            
            # Remove duplicates and filter
            unique_items = []
            seen_names = set()
            
            for item in all_items:
                name = item.get('name', '').strip().lower()
                if name and name not in seen_names and self._is_valid_menu_item(item):
                    seen_names.add(name)
                    unique_items.append(item)
            
            result['menu_items'] = unique_items
            result['total_items'] = len(unique_items)
            result['raw_candidates'] = len(all_items)
            result['extraction_methods'] = extraction_methods
            
            # Determine success
            result['scraping_success'] = len(unique_items) >= 3
            
            # Calculate quality score
            if unique_items:
                avg_confidence = sum(item.get('confidence', 0) for item in unique_items) / len(unique_items)
                has_prices = sum(1 for item in unique_items if item.get('price')) / len(unique_items)
                has_descriptions = sum(1 for item in unique_items if item.get('description')) / len(unique_items)
                
                result['quality_score'] = round((avg_confidence + has_prices + has_descriptions) / 3, 3)
            
            result['processing_time'] = round(time.time() - start_time, 2)
            
            logger.info(f"Ultimate detection completed: {len(unique_items)} items found")
            return result
            
        except Exception as e:
            result['error'] = str(e)
            result['processing_time'] = round(time.time() - start_time, 2)
            logger.error(f"Ultimate detection failed: {e}")
            return result

if __name__ == "__main__":
    # Test the scraper
    from playwright.sync_api import sync_playwright
    
    scraper = UltimateMenuScraper()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        test_url = "https://www.yelp.com/biz/alinea-chicago"
        result = scraper.ultimate_menu_detection(page, test_url)
        
        print(f"Success: {result['scraping_success']}")
        print(f"Items found: {result['total_items']}")
        print(f"Quality score: {result['quality_score']}")
        
        for item in result['menu_items'][:5]:
            print(f"- {item['name']}: {item.get('price', 'No price')}")
        
        browser.close()