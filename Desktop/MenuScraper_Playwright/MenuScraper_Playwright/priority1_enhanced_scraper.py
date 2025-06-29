import asyncio
import re
import time
from typing import Dict, List, Any, Optional, Tuple
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
import json

class Priority1EnhancedScraper:
    """Priority 1 Enhanced Scraper - Focus on improved content detection and extraction"""
    
    def __init__(self, headless: bool = True, timeout: int = 30000):
        self.headless = headless
        self.timeout = timeout
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        
        # Enhanced CSS selectors with better specificity
        self.enhanced_selectors = [
            # High-priority menu item selectors
            '[data-testid*="menu-item"]',
            '[data-testid*="food-item"]',
            '[data-testid*="dish"]',
            '[class*="MenuItem"]',
            '[class*="FoodItem"]',
            '[class*="DishItem"]',
            '[class*="ProductCard"]',
            
            # Menu container with item patterns
            '[class*="menu"] [class*="item"]:not([class*="button"]):not([class*="link"])',
            '[class*="food"] [class*="item"]:not([class*="button"]):not([class*="link"])',
            '[class*="dish"] [class*="container"]',
            '[class*="product"] [class*="card"]',
            
            # Price-containing elements (high priority)
            '*:has-text("$") [class*="item"]',
            'div:has([class*="price"]) [class*="name"]',
            'li:has([class*="price"])',
            'tr:has([class*="price"])',
            
            # List patterns with better filtering
            'ul[class*="menu"] li:not([class*="nav"]):not([class*="link"])',
            'ol[class*="menu"] li:not([class*="nav"]):not([class*="link"])',
            'div[class*="menu-list"] > div',
            'div[class*="food-list"] > div',
            
            # Table patterns
            'table[class*="menu"] tr:has(td)',
            'tbody tr:has(td)',
            'table tr:has(td):not(:first-child)',
            
            # Card and tile patterns
            '[class*="menu-card"]',
            '[class*="food-card"]',
            '[class*="dish-card"]',
            '[class*="item-card"]',
            
            # Semantic patterns
            'article[class*="menu"]',
            'section[class*="food"] > div',
            'div[role="listitem"]',
            
            # Generic fallbacks with better filtering
            '.menu-item:not(.nav-item):not(.link)',
            '.food-item:not(.nav-item):not(.link)',
            '.dish-item:not(.nav-item):not(.link)',
            'li:not([class*="nav"]):not([class*="link"]):not([class*="button"])',
            'div:not([class*="nav"]):not([class*="header"]):not([class*="footer"])'
        ]
        
        # Enhanced price detection patterns
        self.price_patterns = [
            r'\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # $12.99, $1,234.56
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*\$',  # 12.99$
            r'USD\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # USD 12.99
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*USD',  # 12.99 USD
            r'Price:\s*\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # Price: $12.99
            r'Cost:\s*\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'   # Cost: $12.99
        ]
        
        # Enhanced food keywords for better detection
        self.food_keywords = [
            # Cooking methods
            'grilled', 'fried', 'baked', 'roasted', 'steamed', 'sauteed', 'braised',
            'smoked', 'barbecued', 'broiled', 'poached', 'pan-seared', 'slow-cooked',
            
            # Food types
            'chicken', 'beef', 'pork', 'lamb', 'fish', 'salmon', 'tuna', 'shrimp',
            'pasta', 'pizza', 'burger', 'sandwich', 'salad', 'soup', 'steak',
            'rice', 'noodles', 'bread', 'cheese', 'vegetables', 'mushrooms',
            
            # Descriptors
            'fresh', 'homemade', 'organic', 'local', 'seasonal', 'house-made',
            'artisan', 'premium', 'signature', 'specialty', 'traditional',
            
            # Meal categories
            'appetizer', 'starter', 'entree', 'main', 'dessert', 'side', 'beverage',
            'breakfast', 'lunch', 'dinner', 'brunch'
        ]
        
        # Menu link patterns
        self.menu_link_patterns = [
            r'\bmenu\b', r'\bfood\b', r'\border\b', r'\bdine\b', r'\beat\b',
            r'\bcuisine\b', r'\bdelivery\b', r'\btakeout\b', r'\bdining\b'
        ]
        
        # Allergen patterns
        self.allergen_patterns = {
            'nuts': [r'\b(nuts?|almond|walnut|pecan|cashew|pistachio|hazelnut)\b'],
            'dairy': [r'\b(milk|cheese|butter|cream|dairy|lactose)\b'],
            'gluten': [r'\b(gluten|wheat|flour|bread)\b'],
            'shellfish': [r'\b(shellfish|shrimp|crab|lobster|oyster|clam)\b'],
            'soy': [r'\b(soy|soybean|tofu)\b'],
            'eggs': [r'\b(egg|eggs)\b']
        }
        
        # Dietary patterns
        self.dietary_patterns = {
            'vegetarian': r'\b(vegetarian|veggie)\b',
            'vegan': r'\b(vegan)\b',
            'gluten_free': r'\b(gluten[\s-]?free|gf)\b',
            'dairy_free': r'\b(dairy[\s-]?free|lactose[\s-]?free)\b',
            'keto': r'\b(keto|ketogenic|low[\s-]?carb)\b',
            'spicy': r'\b(spicy|hot|jalapeño|habanero|ghost pepper)\b'
        }
    
    async def setup_browser(self) -> bool:
        """Setup browser with enhanced stealth features"""
        try:
            playwright = await async_playwright().start()
            
            self.browser = await playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--no-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--disable-extensions',
                    '--disable-gpu',
                    '--disable-web-security',
                    '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                ]
            )
            
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
    
    async def smart_navigate(self, page: Page, url: str) -> bool:
        """Enhanced navigation with better menu detection"""
        try:
            # Navigate with network idle wait
            await page.goto(url, wait_until='networkidle', timeout=self.timeout)
            
            # Wait for dynamic content
            await self._wait_for_content(page)
            
            # Check if current page has menu content
            if await self._has_menu_content(page):
                return True
            
            # Look for menu links
            menu_links = await self._find_menu_links(page)
            
            if menu_links:
                for link, score, text in menu_links[:3]:
                    try:
                        await link.click(timeout=5000)
                        await page.wait_for_load_state('networkidle', timeout=15000)
                        await self._wait_for_content(page)
                        
                        if await self._has_menu_content(page):
                            return True
                            
                    except Exception as e:
                        print(f"Menu link click failed: {e}")
                        continue
            
            return True
            
        except Exception as e:
            print(f"Navigation error: {e}")
            return False
    
    async def _wait_for_content(self, page: Page) -> None:
        """Wait for dynamic content to load"""
        try:
            # Wait for basic content
            await page.wait_for_function(
                "document.querySelectorAll('*').length > 50",
                timeout=10000
            )
            
            # Additional wait for JavaScript
            await asyncio.sleep(3)
            
            # Scroll to trigger lazy loading
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
            await asyncio.sleep(1)
            await page.evaluate("window.scrollTo(0, 0)")
            await asyncio.sleep(1)
            
        except Exception as e:
            print(f"Content wait failed: {e}")
    
    async def _has_menu_content(self, page: Page) -> bool:
        """Enhanced menu content detection"""
        try:
            text_content = await page.evaluate("document.body.innerText")
            content = await page.content()
            
            text_lower = text_content.lower()
            content_lower = content.lower()
            
            # Count food keywords
            food_score = sum(1 for keyword in self.food_keywords if keyword in text_lower)
            
            # Count price patterns
            price_score = 0
            for pattern in self.price_patterns:
                price_score += len(re.findall(pattern, text_content))
            
            # Count menu indicators
            menu_indicators = ['menu', 'food', 'dish', 'order', 'cuisine']
            menu_score = sum(1 for indicator in menu_indicators if indicator in text_lower)
            
            # Check for menu-like elements
            element_score = 0
            for selector in self.enhanced_selectors[:5]:
                try:
                    elements = await page.query_selector_all(selector)
                    element_score += len(elements)
                except:
                    continue
            
            total_score = food_score + (price_score * 2) + menu_score + (element_score * 0.5)
            return total_score >= 8
            
        except Exception as e:
            print(f"Menu content detection error: {e}")
            return False
    
    async def _find_menu_links(self, page: Page) -> List[Tuple]:
        """Find menu-related links"""
        menu_links = []
        
        try:
            links = await page.query_selector_all('a')
            
            for link in links:
                try:
                    text = await link.inner_text()
                    href = await link.get_attribute('href')
                    
                    if not text or not href:
                        continue
                    
                    text_lower = text.lower().strip()
                    href_lower = href.lower()
                    
                    score = 0
                    
                    # Exact matches
                    if text_lower in ['menu', 'food menu', 'our menu', 'view menu']:
                        score += 10
                    
                    # Pattern matches
                    for pattern in self.menu_link_patterns:
                        if re.search(pattern, text_lower):
                            score += 3
                        if re.search(pattern, href_lower):
                            score += 2
                    
                    if score > 0:
                        menu_links.append((link, score, text))
                        
                except:
                    continue
            
            return sorted(menu_links, key=lambda x: x[1], reverse=True)
            
        except Exception as e:
            print(f"Menu link detection error: {e}")
            return []
    
    async def extract_menu(self, page: Page) -> List[Dict[str, Any]]:
        """Enhanced menu extraction with multiple strategies"""
        try:
            all_items = []
            
            # Strategy 1: Enhanced CSS selectors
            css_items = await self._extract_with_css_selectors(page)
            if css_items:
                all_items.extend(css_items)
            
            # Strategy 2: Price-based extraction
            price_items = await self._extract_with_price_detection(page)
            if price_items:
                all_items.extend(price_items)
            
            # Strategy 3: Text analysis
            text_items = await self._extract_with_text_analysis(page)
            if text_items:
                all_items.extend(text_items)
            
            # Strategy 4: Table extraction
            table_items = await self._extract_from_tables(page)
            if table_items:
                all_items.extend(table_items)
            
            # Remove duplicates and enhance
            unique_items = self._remove_duplicates(all_items)
            enhanced_items = [self._enhance_item(item) for item in unique_items]
            
            return enhanced_items
            
        except Exception as e:
            print(f"Menu extraction error: {e}")
            return []
    
    async def _extract_with_css_selectors(self, page: Page) -> List[Dict[str, Any]]:
        """Extract using enhanced CSS selectors"""
        items = []
        
        for selector in self.enhanced_selectors:
            try:
                elements = await page.query_selector_all(selector)
                
                for element in elements:
                    try:
                        text = await element.inner_text()
                        if text and len(text.strip()) > 5:
                            item = self._parse_item_text(text.strip())
                            if item:
                                item['extraction_method'] = 'enhanced_css_selectors'
                                item['selector_used'] = selector
                                items.append(item)
                    except:
                        continue
                
                if len(items) >= 5:  # If we found good items, use them
                    break
                    
            except:
                continue
        
        return items
    
    async def _extract_with_price_detection(self, page: Page) -> List[Dict[str, Any]]:
        """Extract by finding elements with prices"""
        items = []
        
        try:
            # Get all text content
            text_content = await page.evaluate("document.body.innerText")
            
            # Find all elements that might contain prices
            price_elements = await page.query_selector_all('*')
            
            for element in price_elements:
                try:
                    element_text = await element.inner_text()
                    if not element_text or len(element_text) > 500:
                        continue
                    
                    # Check if element contains price
                    has_price = any(re.search(pattern, element_text) for pattern in self.price_patterns)
                    
                    if has_price and self._is_likely_menu_item(element_text):
                        item = self._parse_item_text(element_text.strip())
                        if item:
                            item['extraction_method'] = 'price_detection'
                            items.append(item)
                            
                except:
                    continue
            
            return items[:20]  # Limit to prevent too many items
            
        except Exception as e:
            print(f"Price detection error: {e}")
            return []
    
    async def _extract_with_text_analysis(self, page: Page) -> List[Dict[str, Any]]:
        """Extract using text analysis"""
        try:
            text_content = await page.evaluate("document.body.innerText")
            items = []
            
            lines = text_content.split('\n')
            
            for line in lines:
                line = line.strip()
                if 10 <= len(line) <= 300 and self._is_likely_menu_item(line):
                    item = self._parse_item_text(line)
                    if item:
                        item['extraction_method'] = 'text_analysis'
                        items.append(item)
            
            return items[:15]  # Limit results
            
        except Exception as e:
            print(f"Text analysis error: {e}")
            return []
    
    async def _extract_from_tables(self, page: Page) -> List[Dict[str, Any]]:
        """Extract from table structures"""
        items = []
        
        try:
            tables = await page.query_selector_all('table')
            
            for table in tables:
                rows = await table.query_selector_all('tr')
                
                for row in rows:
                    try:
                        row_text = await row.inner_text()
                        if row_text and self._is_likely_menu_item(row_text):
                            item = self._parse_item_text(row_text.strip())
                            if item:
                                item['extraction_method'] = 'table_extraction'
                                items.append(item)
                    except:
                        continue
            
            return items
            
        except Exception as e:
            print(f"Table extraction error: {e}")
            return []
    
    def _is_likely_menu_item(self, text: str) -> bool:
        """Enhanced menu item detection"""
        text_lower = text.lower()
        
        # Check for food keywords
        food_score = sum(1 for keyword in self.food_keywords if keyword in text_lower)
        
        # Check for price
        has_price = any(re.search(pattern, text) for pattern in self.price_patterns)
        
        # Check length
        reasonable_length = 10 <= len(text) <= 300
        
        # Exclude navigation and non-food items
        exclude_patterns = [
            'home', 'about', 'contact', 'location', 'hours', 'phone',
            'address', 'email', 'website', 'facebook', 'twitter',
            'copyright', 'privacy', 'terms', 'login', 'register'
        ]
        
        has_exclude = any(pattern in text_lower for pattern in exclude_patterns)
        
        # Scoring
        score = 0
        if food_score >= 1: score += 3
        if has_price: score += 4
        if reasonable_length: score += 1
        if has_exclude: score -= 5
        
        return score >= 4
    
    def _parse_item_text(self, text: str) -> Optional[Dict[str, Any]]:
        """Enhanced text parsing for menu items"""
        try:
            # Extract price with enhanced patterns
            price = None
            price_match = None
            
            for pattern in self.price_patterns:
                match = re.search(pattern, text)
                if match:
                    price_str = match.group(1) if match.groups() else match.group(0)
                    price_str = re.sub(r'[^\d.,]', '', price_str)
                    try:
                        price = float(price_str.replace(',', ''))
                        price_match = match
                        break
                    except:
                        continue
            
            # Extract name (remove price and clean up)
            name = text
            if price_match:
                name = text.replace(price_match.group(0), '').strip()
            
            # Clean name
            name = re.sub(r'\s+', ' ', name).strip()
            name = re.sub(r'^[\-•*]+\s*', '', name)  # Remove bullet points
            name = re.sub(r'\s*[\-•*]+$', '', name)  # Remove trailing bullets
            
            if len(name) < 3:
                return None
            
            # Extract description (look for patterns)
            description = None
            
            # Try to split name and description
            if ' - ' in name:
                parts = name.split(' - ', 1)
                name = parts[0].strip()
                description = parts[1].strip()
            elif '. ' in name and len(name) > 30:
                parts = name.split('. ', 1)
                if len(parts[0]) < 50:  # Reasonable name length
                    name = parts[0].strip()
                    description = parts[1].strip()
            
            # Categorize
            category = self._categorize_item(name + ' ' + (description or ''))
            
            return {
                'name': name,
                'price': price,
                'description': description,
                'category': category,
                'raw_text': text
            }
            
        except Exception as e:
            return None
    
    def _categorize_item(self, text: str) -> str:
        """Enhanced categorization"""
        text_lower = text.lower()
        
        categories = {
            'appetizer': ['appetizer', 'starter', 'small plate', 'sharing', 'wings', 'nachos', 'dip'],
            'salad': ['salad', 'greens', 'caesar', 'garden', 'spinach', 'arugula'],
            'soup': ['soup', 'bisque', 'chowder', 'broth', 'stew', 'gazpacho'],
            'sandwich': ['sandwich', 'burger', 'wrap', 'panini', 'sub', 'hoagie', 'club'],
            'pasta': ['pasta', 'spaghetti', 'linguine', 'ravioli', 'lasagna', 'fettuccine', 'penne'],
            'pizza': ['pizza', 'flatbread', 'pie', 'calzone'],
            'seafood': ['fish', 'salmon', 'tuna', 'shrimp', 'crab', 'lobster', 'scallops', 'mussels'],
            'meat': ['steak', 'beef', 'chicken', 'pork', 'lamb', 'ribs', 'turkey', 'duck'],
            'dessert': ['dessert', 'cake', 'pie', 'ice cream', 'chocolate', 'cookie', 'brownie', 'cheesecake'],
            'beverage': ['drink', 'soda', 'juice', 'coffee', 'tea', 'beer', 'wine', 'cocktail', 'smoothie']
        }
        
        for category, keywords in categories.items():
            if any(keyword in text_lower for keyword in keywords):
                return category
        
        return 'other'
    
    def _enhance_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance item with additional data"""
        text_for_analysis = f"{item.get('name', '')} {item.get('description', '')}".lower()
        
        # Detect allergens
        allergens = []
        for allergen, patterns in self.allergen_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_for_analysis, re.IGNORECASE):
                    allergens.append(allergen)
                    break
        
        # Detect dietary tags
        dietary_tags = []
        for tag, pattern in self.dietary_patterns.items():
            if re.search(pattern, text_for_analysis, re.IGNORECASE):
                dietary_tags.append(tag)
        
        # Calculate confidence
        confidence = 0.5
        if item.get('price'): confidence += 0.3
        if item.get('description'): confidence += 0.1
        if item.get('category') != 'other': confidence += 0.1
        
        item.update({
            'allergens': allergens,
            'dietary_tags': dietary_tags,
            'confidence_score': min(confidence, 1.0),
            'has_price': item.get('price') is not None,
            'has_description': item.get('description') is not None
        })
        
        return item
    
    def _remove_duplicates(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate items"""
        seen = set()
        unique_items = []
        
        for item in items:
            key = (item.get('name', '').lower().strip(), item.get('price'))
            if key not in seen:
                seen.add(key)
                unique_items.append(item)
        
        return unique_items
    
    async def scrape_restaurant(self, restaurant_data: Dict[str, Any]) -> Dict[str, Any]:
        """Scrape a single restaurant"""
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
            
            # Navigate
            navigation_success = await self.smart_navigate(page, restaurant_data['url'])
            
            if not navigation_success:
                result['error'] = 'Navigation failed'
                return result
            
            # Extract menu
            menu_items = await self.extract_menu(page)
            
            if menu_items:
                result['scraping_success'] = True
                result['total_items'] = len(menu_items)
                result['items'] = menu_items
                result['extraction_method'] = menu_items[0].get('extraction_method', 'unknown')
            else:
                result['error'] = 'No menu items found with priority 1 strategies'
            
            await page.close()
            
        except Exception as e:
            result['error'] = f'Scraping error: {str(e)}'
        
        finally:
            result['processing_time'] = time.time() - start_time
        
        return result
    
    async def close(self):
        """Close browser resources"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()