#!/usr/bin/env python3
"""
Enhanced Dynamic Menu Scraper
Focuses on improved CSS selectors and dynamic content handling
Addresses the primary failure mode: "No menu items found with any strategy"

Key Improvements:
1. Enhanced CSS selectors for modern websites
2. Dynamic content waiting strategies
3. Multiple extraction fallback methods
4. Better text pattern recognition
5. Improved allergen detection
"""

import asyncio
import json
import re
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urljoin, urlparse
import random

try:
    from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeoutError
except ImportError:
    print("❌ Playwright not installed. Run: pip install playwright")
    exit(1)

class EnhancedDynamicScraper:
    """Enhanced menu scraper with dynamic content handling and improved selectors"""
    
    def __init__(self, headless: bool = True, timeout: int = 30000):
        self.headless = headless
        self.timeout = timeout
        self.browser = None
        self.context = None
        
        # Enhanced allergen detection patterns
        self.allergen_patterns = {
            'gluten': [
                r'\b(?:gluten|wheat|flour|bread|pasta|noodle|cereal|barley|rye|oat|malt)\b',
                r'\b(?:contains?\s+gluten|gluten[\s-]?free|wheat[\s-]?free|gf\b)\b',
                r'\b(?:celiac|coeliac)[\s-]?(?:safe|friendly)\b'
            ],
            'dairy': [
                r'\b(?:milk|cheese|cream|butter|yogurt|dairy|lactose|casein|whey|mozzarella|cheddar|parmesan)\b',
                r'\b(?:contains?\s+dairy|dairy[\s-]?free|lactose[\s-]?free|non[\s-]?dairy)\b'
            ],
            'nuts': [
                r'\b(?:nuts?|almond|walnut|pecan|cashew|pistachio|hazelnut|macadamia|brazil\s+nut)\b',
                r'\b(?:peanut|tree\s+nuts?|nut[\s-]?free|contains?\s+nuts?|mixed\s+nuts)\b'
            ],
            'eggs': [
                r'\b(?:eggs?|egg\s+white|egg\s+yolk|mayonnaise|mayo|hollandaise)\b',
                r'\b(?:contains?\s+eggs?|egg[\s-]?free)\b'
            ],
            'soy': [
                r'\b(?:soy|soya|tofu|tempeh|miso|soy\s+sauce|edamame|tamari)\b',
                r'\b(?:contains?\s+soy|soy[\s-]?free)\b'
            ],
            'fish': [
                r'\b(?:fish|salmon|tuna|cod|halibut|anchovy|sardine|bass|trout|mackerel)\b',
                r'\b(?:contains?\s+fish|fish[\s-]?free)\b'
            ],
            'shellfish': [
                r'\b(?:shellfish|shrimp|crab|lobster|oyster|mussel|clam|scallop|prawns?)\b',
                r'\b(?:contains?\s+shellfish|shellfish[\s-]?free)\b'
            ],
            'sesame': [
                r'\b(?:sesame|tahini|sesame\s+oil|sesame\s+seed)\b',
                r'\b(?:contains?\s+sesame|sesame[\s-]?free)\b'
            ]
        }
        
        # Enhanced dietary tag patterns
        self.dietary_patterns = {
            'vegetarian': r'\b(?:vegetarian|veggie|plant[\s-]?based|meat[\s-]?free)\b',
            'vegan': r'\b(?:vegan|plant[\s-]?based|dairy[\s-]?free|100%\s+plant)\b',
            'gluten_free': r'\b(?:gluten[\s-]?free|gf\b|celiac[\s-]?friendly)\b',
            'keto': r'\b(?:keto|ketogenic|low[\s-]?carb|high[\s-]?fat)\b',
            'paleo': r'\b(?:paleo|paleolithic|caveman\s+diet)\b',
            'organic': r'\b(?:organic|natural|farm[\s-]?fresh|locally\s+sourced)\b',
            'spicy': r'\b(?:spicy|hot|jalapeño|habanero|sriracha|chili|ghost\s+pepper)\b',
            'healthy': r'\b(?:healthy|light|low[\s-]?cal|nutritious|superfood)\b'
        }
        
        # Comprehensive CSS selectors for modern websites
        self.enhanced_selectors = [
            # Modern React/Vue component patterns
            '[data-testid*="menu-item"]',
            '[data-testid*="food-item"]',
            '[data-testid*="dish"]',
            '[data-testid*="product"]',
            '[data-cy*="menu"]',
            '[data-cy*="item"]',
            
            # Class-based patterns (common naming conventions)
            '[class*="MenuItem"]',
            '[class*="FoodItem"]',
            '[class*="DishItem"]',
            '[class*="ProductCard"]',
            '[class*="menu-item"]',
            '[class*="food-item"]',
            '[class*="dish-item"]',
            '[class*="product-item"]',
            
            # Menu container patterns
            '[class*="menu"] [class*="item"]',
            '[class*="food"] [class*="item"]',
            '[class*="dish"] [class*="container"]',
            '[class*="product"] [class*="card"]',
            
            # Price-based detection (enhanced) - using text content instead of has-text
            '[class*="price"]',
            '[data-testid*="price"]',
            '.price, .cost, .amount',
            'span[class*="dollar"]',
            'div[class*="pricing"]',
            
            # List and grid patterns
            'ul[class*="menu"] li',
            'ol[class*="menu"] li',
            'div[class*="grid"] > div',
            'div[class*="list"] > div',
            
            # Table patterns
            'table[class*="menu"] tr',
            'tbody tr',
            'table tr',
            
            # Card patterns
            '[class*="card"]',
            '[class*="tile"]',
            '[class*="panel"]',
            
            # Semantic HTML patterns
            'article[class*="menu"]',
            'section[class*="food"]',
            'div[role="listitem"]',
            
            # Generic fallbacks
            '.menu-item, .food-item, .dish-item, .product-item',
            '.item, .dish, .product',
            'li',
            'div:not([class*="price"]):not([class*="total"])'
        ]
        
        # Dynamic content waiting strategies
        self.wait_strategies = [
            # Wait for menu containers
            "document.querySelectorAll('[class*=\"menu\"]').length > 0",
            "document.querySelectorAll('[data-testid*=\"menu\"]').length > 0",
            "document.querySelectorAll('*').length > 100",  # General content load
            
            # Wait for price elements
            "document.body.innerText.includes('$')",
            "document.querySelectorAll('*').length > 50 && document.body.innerText.length > 1000"
        ]
        
        # Menu link detection patterns
        self.menu_link_patterns = [
            r'\bmenu\b',
            r'\bfood\b',
            r'\border\b',
            r'\bdine\b',
            r'\beat\b',
            r'\bcuisine\b',
            r'\bdelivery\b',
            r'\btakeout\b'
        ]
    
    async def setup_browser(self) -> bool:
        """Setup browser with enhanced stealth and performance features"""
        try:
            playwright = await async_playwright().start()
            
            # Enhanced browser launch with stealth settings
            self.browser = await playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--no-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--disable-extensions',
                    '--disable-gpu',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                ]
            )
            
            # Create context with realistic settings
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='en-US',
                timezone_id='America/New_York',
                extra_http_headers={
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
                }
            )
            
            return True
            
        except Exception as e:
            print(f"❌ Browser setup failed: {e}")
            return False
    
    async def smart_navigate_enhanced(self, page: Page, url: str) -> bool:
        """Enhanced navigation with better dynamic content handling"""
        try:
            # Navigate to main page with network idle wait
            await page.goto(url, wait_until='networkidle', timeout=self.timeout)
            
            # Wait for initial content load
            await self._wait_for_dynamic_content(page)
            
            # Check if we're already on a menu page
            if await self._has_menu_content_enhanced(page):
                return True
            
            # Look for menu links with enhanced detection
            menu_links = await self._find_menu_links_enhanced(page)
            
            if menu_links:
                # Try the most promising menu links
                for link, score, text in menu_links[:3]:
                    try:
                        await link.click(timeout=5000)
                        await page.wait_for_load_state('networkidle', timeout=15000)
                        
                        # Wait for dynamic content after navigation
                        await self._wait_for_dynamic_content(page)
                        
                        # Check if we found menu content
                        if await self._has_menu_content_enhanced(page):
                            return True
                            
                    except Exception as e:
                        print(f"Menu link click failed: {e}")
                        continue
            
            # If no menu links worked, stay on current page
            return True
            
        except Exception as e:
            print(f"Enhanced navigation error: {e}")
            return False
    
    async def _wait_for_dynamic_content(self, page: Page) -> None:
        """Wait for dynamic content to load using multiple strategies"""
        try:
            # Try multiple wait strategies
            for strategy in self.wait_strategies:
                try:
                    await page.wait_for_function(
                        strategy,
                        timeout=10000
                    )
                    break  # If one succeeds, we're good
                except:
                    continue
            
            # Additional wait for JavaScript execution
            await asyncio.sleep(3)
            
            # Scroll to trigger lazy loading
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
            await asyncio.sleep(1)
            await page.evaluate("window.scrollTo(0, 0)")
            await asyncio.sleep(1)
            
        except Exception as e:
            print(f"Dynamic content wait failed: {e}")
    
    async def _has_menu_content_enhanced(self, page: Page) -> bool:
        """Enhanced menu content detection"""
        try:
            # Get page content
            content = await page.content()
            text_content = await page.evaluate("document.body.innerText")
            
            content_lower = content.lower()
            text_lower = text_content.lower()
            
            # Enhanced menu indicators
            menu_indicators = [
                'menu', 'food', 'dish', 'appetizer', 'entree', 'dessert',
                'price', '$', 'order', 'cuisine', 'restaurant', 'delivery',
                'takeout', 'dine', 'eat', 'meal', 'lunch', 'dinner', 'breakfast'
            ]
            
            # Count indicators in both HTML and text
            html_score = sum(1 for indicator in menu_indicators if indicator in content_lower)
            text_score = sum(1 for indicator in menu_indicators if indicator in text_lower)
            
            # Price pattern detection (enhanced)
            price_patterns = len(re.findall(r'\$\d+(?:\.\d{2})?', text_content))
            
            # Menu-specific element detection
            menu_elements = 0
            for selector in self.enhanced_selectors[:10]:  # Check first 10 selectors
                try:
                    elements = await page.query_selector_all(selector)
                    menu_elements += len(elements)
                except:
                    continue
            
            # Enhanced scoring algorithm
            total_score = html_score + text_score + (price_patterns * 3) + (menu_elements * 2)
            
            return total_score >= 10
            
        except Exception as e:
            print(f"Menu content detection error: {e}")
            return False
    
    async def _find_menu_links_enhanced(self, page: Page) -> List[Tuple]:
        """Enhanced menu link detection with better scoring"""
        menu_links = []
        
        try:
            # Get all links
            links = await page.query_selector_all('a')
            
            for link in links:
                try:
                    # Get link text and href
                    text = await link.inner_text()
                    href = await link.get_attribute('href')
                    
                    if not text or not href:
                        continue
                    
                    text_lower = text.lower().strip()
                    href_lower = href.lower()
                    
                    # Enhanced relevance scoring
                    relevance_score = 0
                    
                    # Exact matches get highest scores
                    exact_matches = ['menu', 'food menu', 'our menu', 'view menu', 'order online']
                    if text_lower in exact_matches:
                        relevance_score += 10
                    
                    # Pattern-based scoring
                    for pattern in self.menu_link_patterns:
                        if re.search(pattern, text_lower):
                            relevance_score += 3
                        if re.search(pattern, href_lower):
                            relevance_score += 2
                    
                    # Bonus for common menu URL patterns
                    menu_url_patterns = ['/menu', '/food', '/order', '/delivery']
                    for url_pattern in menu_url_patterns:
                        if url_pattern in href_lower:
                            relevance_score += 4
                    
                    # Add to candidates if relevant
                    if relevance_score >= 3:
                        menu_links.append((link, relevance_score, text))
                        
                except Exception:
                    continue
            
            # Sort by relevance score
            menu_links.sort(key=lambda x: x[1], reverse=True)
            return menu_links
            
        except Exception:
            return []
    
    async def extract_menu_enhanced(self, page: Page) -> List[Dict[str, Any]]:
        """Enhanced menu extraction with multiple strategies"""
        all_items = []
        
        try:
            # Strategy 1: Enhanced CSS selectors
            items = await self._extract_with_enhanced_selectors(page)
            if items:
                all_items.extend(items)
                print(f"✅ Enhanced selectors found {len(items)} items")
            
            # Strategy 2: Text-based extraction
            if len(all_items) < 5:
                text_items = await self._extract_with_text_analysis(page)
                if text_items:
                    all_items.extend(text_items)
                    print(f"✅ Text analysis found {len(text_items)} items")
            
            # Strategy 3: Price-based extraction
            if len(all_items) < 3:
                price_items = await self._extract_with_price_detection(page)
                if price_items:
                    all_items.extend(price_items)
                    print(f"✅ Price detection found {len(price_items)} items")
            
            # Remove duplicates and enhance items
            unique_items = self._remove_duplicates(all_items)
            enhanced_items = [self._enhance_menu_item(item) for item in unique_items]
            
            return enhanced_items
            
        except Exception as e:
            print(f"Menu extraction error: {e}")
            return []
    
    async def _extract_with_enhanced_selectors(self, page: Page) -> List[Dict[str, Any]]:
        """Extract menu items using enhanced CSS selectors"""
        items = []
        
        for selector in self.enhanced_selectors:
            try:
                elements = await page.query_selector_all(selector)
                
                for element in elements:
                    try:
                        text = await element.inner_text()
                        if text and len(text.strip()) > 3:
                            item = self._parse_menu_item_text(text.strip())
                            if item:
                                item['extraction_method'] = 'enhanced_css_selectors'
                                item['selector_used'] = selector
                                items.append(item)
                    except:
                        continue
                        
                if items:
                    break  # If we found items with this selector, use them
                    
            except Exception as e:
                continue
        
        return items
    
    async def _extract_with_text_analysis(self, page: Page) -> List[Dict[str, Any]]:
        """Extract menu items using enhanced text analysis"""
        try:
            # Get all text content
            text_content = await page.evaluate("document.body.innerText")
            
            items = []
            lines = text_content.split('\n')
            
            for line in lines:
                line = line.strip()
                if len(line) < 5 or len(line) > 300:
                    continue
                
                # Enhanced item scoring
                if self._is_likely_menu_item(line):
                    item = self._parse_menu_item_text(line)
                    if item:
                        item['extraction_method'] = 'text_analysis'
                        items.append(item)
            
            return items
            
        except Exception as e:
            print(f"Text analysis error: {e}")
            return []
    
    async def _extract_with_price_detection(self, page: Page) -> List[Dict[str, Any]]:
        """Extract menu items by detecting price patterns"""
        try:
            # Get all text content and find elements with price patterns
            text_content = await page.evaluate("document.body.innerText")
            
            # Find all elements that might contain prices
            price_selectors = [
                '[class*="price"]',
                '[class*="cost"]', 
                '[class*="amount"]',
                '[data-testid*="price"]',
                'span',
                'div',
                'p'
            ]
            
            items = []
            for selector in price_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    for element in elements:
                        try:
                            text = await element.inner_text()
                            if text and '$' in text and len(text.strip()) > 3:
                                item = self._parse_menu_item_text(text.strip())
                                if item:
                                    item['extraction_method'] = 'price_detection'
                                    items.append(item)
                        except:
                            continue
                except:
                    continue
            
            return items
            
        except Exception as e:
            print(f"Price detection error: {e}")
            return []
    
    def _is_likely_menu_item(self, text: str) -> bool:
        """Enhanced menu item likelihood detection"""
        text_lower = text.lower()
        
        # Must have some food-related content
        food_indicators = [
            'served', 'grilled', 'fried', 'baked', 'fresh', 'homemade',
            'sauce', 'cheese', 'chicken', 'beef', 'fish', 'pasta',
            'salad', 'soup', 'sandwich', 'burger', 'pizza', 'rice',
            'vegetables', 'meat', 'seafood', 'dessert', 'appetizer'
        ]
        
        has_food_indicator = any(indicator in text_lower for indicator in food_indicators)
        has_price = bool(re.search(r'\$\d+', text))
        reasonable_length = 10 <= len(text) <= 200
        
        # Score-based decision
        score = 0
        if has_food_indicator: score += 3
        if has_price: score += 4
        if reasonable_length: score += 1
        
        return score >= 4
    
    def _parse_menu_item_text(self, text: str) -> Optional[Dict[str, Any]]:
        """Enhanced menu item text parsing"""
        try:
            # Extract price
            price_match = re.search(r'\$([\d,]+(?:\.\d{2})?)', text)
            price = float(price_match.group(1).replace(',', '')) if price_match else None
            
            # Clean item name (remove price and common suffixes)
            name = re.sub(r'\$[\d,]+(?:\.\d{2})?', '', text).strip()
            name = re.sub(r'\s*\([^)]*\)\s*$', '', name).strip()  # Remove trailing parentheses
            
            if len(name) < 3:
                return None
            
            # Extract description (text after name, before price)
            description_match = re.search(r'^([^$]+?)\s*\$', text)
            description = description_match.group(1).strip() if description_match else name
            
            # Basic categorization
            category = self._categorize_item(name + ' ' + description)
            
            return {
                'name': name,
                'price': price,
                'description': description if description != name else None,
                'category': category,
                'raw_text': text
            }
            
        except Exception as e:
            return None
    
    def _categorize_item(self, text: str) -> str:
        """Enhanced item categorization"""
        text_lower = text.lower()
        
        categories = {
            'appetizer': ['appetizer', 'starter', 'small plate', 'sharing', 'wings', 'nachos'],
            'salad': ['salad', 'greens', 'caesar', 'garden'],
            'soup': ['soup', 'bisque', 'chowder', 'broth'],
            'sandwich': ['sandwich', 'burger', 'wrap', 'panini', 'sub'],
            'pasta': ['pasta', 'spaghetti', 'linguine', 'ravioli', 'lasagna'],
            'pizza': ['pizza', 'flatbread', 'pie'],
            'seafood': ['fish', 'salmon', 'tuna', 'shrimp', 'crab', 'lobster'],
            'meat': ['steak', 'beef', 'chicken', 'pork', 'lamb', 'ribs'],
            'dessert': ['dessert', 'cake', 'pie', 'ice cream', 'chocolate', 'cookie'],
            'beverage': ['drink', 'soda', 'juice', 'coffee', 'tea', 'beer', 'wine']
        }
        
        for category, keywords in categories.items():
            if any(keyword in text_lower for keyword in keywords):
                return category
        
        return 'other'
    
    def _enhance_menu_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance menu item with allergen detection and confidence scoring"""
        text_for_analysis = f"{item.get('name', '')} {item.get('description', '')}".lower()
        
        # Detect allergens
        allergens = self._detect_allergens(text_for_analysis)
        
        # Detect dietary tags
        dietary_tags = self._detect_dietary_tags(text_for_analysis)
        
        # Calculate confidence score
        confidence = self._calculate_confidence_score(item)
        
        # Enhance the item
        item.update({
            'allergens': allergens,
            'dietary_tags': dietary_tags,
            'confidence_score': confidence,
            'has_price': item.get('price') is not None,
            'has_description': item.get('description') is not None
        })
        
        return item
    
    def _detect_allergens(self, text: str) -> List[str]:
        """Enhanced allergen detection"""
        detected = []
        
        for allergen, patterns in self.allergen_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    detected.append(allergen)
                    break
        
        return list(set(detected))
    
    def _detect_dietary_tags(self, text: str) -> List[str]:
        """Enhanced dietary tag detection"""
        detected = []
        
        for tag, pattern in self.dietary_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                detected.append(tag)
        
        return detected
    
    def _calculate_confidence_score(self, item: Dict[str, Any]) -> float:
        """Enhanced confidence scoring"""
        score = 0.5  # Base score
        
        # Price presence
        if item.get('price'):
            score += 0.2
        
        # Description presence
        if item.get('description'):
            score += 0.1
        
        # Category detection
        if item.get('category') != 'other':
            score += 0.1
        
        # Allergen detection
        if item.get('allergens'):
            score += 0.05
        
        # Name quality
        name_length = len(item.get('name', ''))
        if 5 <= name_length <= 50:
            score += 0.05
        
        return min(score, 1.0)
    
    def _remove_duplicates(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate menu items"""
        seen = set()
        unique_items = []
        
        for item in items:
            # Create a key based on name and price
            key = (item.get('name', '').lower().strip(), item.get('price'))
            
            if key not in seen:
                seen.add(key)
                unique_items.append(item)
        
        return unique_items
    
    async def scrape_restaurant_enhanced(self, restaurant_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced restaurant scraping with comprehensive error handling"""
        start_time = time.time()
        
        result = {
            'restaurant_name': restaurant_data.get('name', 'Unknown'),
            'url': restaurant_data.get('url', ''),
            'scraping_success': False,
            'total_items': 0,
            'processing_time': 0,
            'extraction_method': None,
            'items': [],
            'error': None
        }
        
        try:
            page = await self.context.new_page()
            
            # Enhanced navigation
            navigation_success = await self.smart_navigate_enhanced(page, restaurant_data['url'])
            
            if not navigation_success:
                result['error'] = 'Enhanced navigation failed'
                return result
            
            # Enhanced menu extraction
            menu_items = await self.extract_menu_enhanced(page)
            
            if menu_items:
                result.update({
                    'scraping_success': True,
                    'total_items': len(menu_items),
                    'items': menu_items,
                    'extraction_method': menu_items[0].get('extraction_method', 'unknown')
                })
            else:
                result['error'] = 'No menu items found with enhanced strategies'
            
            await page.close()
            
        except Exception as e:
            result['error'] = f'Enhanced scraping error: {str(e)}'
        
        finally:
            result['processing_time'] = round(time.time() - start_time, 2)
        
        return result
    
    async def cleanup(self):
        """Cleanup browser resources"""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
        except Exception as e:
            print(f"Cleanup error: {e}")

# Example usage
if __name__ == "__main__":
    async def test_enhanced_scraper():
        scraper = EnhancedDynamicScraper(headless=True)
        
        if await scraper.setup_browser():
            test_restaurant = {
                'name': 'Test Restaurant',
                'url': 'https://example-restaurant.com'
            }
            
            result = await scraper.scrape_restaurant_enhanced(test_restaurant)
            print(json.dumps(result, indent=2))
            
            await scraper.cleanup()
    
    # Run test
    # asyncio.run(test_enhanced_scraper())