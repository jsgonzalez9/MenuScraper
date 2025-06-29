import asyncio
import re
import time
from typing import Dict, List, Any, Optional, Tuple
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
import json

class Priority1ImprovedScraper:
    """Priority 1 Improved Scraper - Focus on better content filtering and price detection"""
    
    def __init__(self, headless: bool = True, timeout: int = 30000):
        self.headless = headless
        self.timeout = timeout
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        
        # Highly targeted CSS selectors for menu items
        self.menu_selectors = [
            # High-confidence menu item selectors
            '[data-testid*="menu-item"]',
            '[data-testid*="food-item"]',
            '[data-testid*="dish"]',
            '[class*="MenuItem"][class*="price"]',
            '[class*="FoodItem"][class*="price"]',
            '[class*="DishItem"][class*="price"]',
            
            # Menu containers with price indicators
            '[class*="menu"] *:has-text("$")',
            '[class*="food"] *:has-text("$")',
            '[id*="menu"] *:has-text("$")',
            
            # Price-containing list items
            'li:has-text("$"):not([class*="nav"]):not([class*="link"]):not([class*="button"])',
            'div:has-text("$"):not([class*="nav"]):not([class*="header"]):not([class*="footer"])',
            
            # Table rows with prices
            'tr:has-text("$")',
            'tbody tr:has(td):has-text("$")',
            
            # Specific menu patterns
            '[class*="menu-list"] [class*="item"]:has-text("$")',
            '[class*="food-list"] [class*="item"]:has-text("$")',
            '[class*="dish-list"] [class*="item"]:has-text("$")',
        ]
        
        # Enhanced price patterns with more variations
        self.price_patterns = [
            r'\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # $12.99, $1,234.56
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*\$',  # 12.99$
            r'USD\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # USD 12.99
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*USD',  # 12.99 USD
            r'Price[:\s]*\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # Price: $12.99
            r'Cost[:\s]*\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',   # Cost: $12.99
            r'\$(\d{1,2})(?:\.(\d{2}))?',  # Simple $12 or $12.99
            r'(\d{1,2})\.(\d{2})\s*\$',   # 12.99$
        ]
        
        # Strong food indicators
        self.strong_food_keywords = [
            # Specific food items
            'burger', 'pizza', 'pasta', 'salad', 'sandwich', 'steak', 'chicken', 'fish',
            'soup', 'appetizer', 'dessert', 'entree', 'main course', 'side dish',
            
            # Cooking methods
            'grilled', 'fried', 'baked', 'roasted', 'sauteed', 'braised', 'steamed',
            
            # Food descriptors
            'served with', 'topped with', 'includes', 'comes with', 'choice of',
            'fresh', 'homemade', 'house-made', 'signature', 'specialty'
        ]
        
        # Exclusion patterns for non-menu content
        self.exclusion_patterns = [
            # Navigation and UI elements
            r'\b(home|about|contact|location|hours|phone|email|login|register|sign in|sign up)\b',
            r'\b(my profile|account|settings|preferences|cart|checkout|order history)\b',
            r'\b(facebook|twitter|instagram|social|follow|like|share)\b',
            r'\b(privacy|terms|conditions|policy|copyright|reserved)\b',
            r'\b(search|filter|sort|view|show|hide|toggle|menu|navigation)\b',
            r'\b(delivery|pickup|takeout|catering|reservations|book|table)\b',
            r'\b(reviews|rating|stars|testimonials|feedback)\b',
            
            # Common non-food text
            r'^(\s*|\.|\-|\*|•)+$',  # Empty or just punctuation
            r'^\d+$',  # Just numbers
            r'^[A-Z]{2,}$',  # All caps abbreviations
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
        """Enhanced menu content detection with price focus"""
        try:
            text_content = await page.evaluate("document.body.innerText")
            
            # Count price patterns (high priority)
            price_count = 0
            for pattern in self.price_patterns:
                price_count += len(re.findall(pattern, text_content))
            
            # Count strong food keywords
            food_count = 0
            text_lower = text_content.lower()
            for keyword in self.strong_food_keywords:
                if keyword in text_lower:
                    food_count += 1
            
            # Check for menu-like structure with prices
            menu_structure_score = 0
            try:
                # Look for elements that contain both food terms and prices
                elements_with_prices = await page.query_selector_all('*')
                for element in elements_with_prices[:50]:  # Limit to avoid timeout
                    try:
                        element_text = await element.inner_text()
                        if element_text and len(element_text) < 200:
                            has_price = any(re.search(pattern, element_text) for pattern in self.price_patterns)
                            has_food = any(keyword in element_text.lower() for keyword in self.strong_food_keywords[:10])
                            if has_price and has_food:
                                menu_structure_score += 1
                    except:
                        continue
            except:
                pass
            
            # Enhanced scoring with price emphasis
            total_score = (price_count * 3) + food_count + (menu_structure_score * 2)
            
            print(f"Menu detection - Price count: {price_count}, Food count: {food_count}, Structure: {menu_structure_score}, Total: {total_score}")
            
            return total_score >= 5
            
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
        """Enhanced menu extraction with strict filtering"""
        try:
            all_items = []
            
            # Strategy 1: Price-focused extraction
            price_items = await self._extract_with_price_focus(page)
            if price_items:
                all_items.extend(price_items)
                print(f"Price-focused extraction: {len(price_items)} items")
            
            # Strategy 2: Enhanced CSS selectors (only if price extraction didn't work well)
            if len(price_items) < 5:
                css_items = await self._extract_with_css_selectors(page)
                if css_items:
                    all_items.extend(css_items)
                    print(f"CSS selector extraction: {len(css_items)} items")
            
            # Strategy 3: Text analysis with strict filtering
            if len(all_items) < 5:
                text_items = await self._extract_with_text_analysis(page)
                if text_items:
                    all_items.extend(text_items)
                    print(f"Text analysis extraction: {len(text_items)} items")
            
            # Remove duplicates and filter
            unique_items = self._remove_duplicates(all_items)
            filtered_items = self._filter_valid_items(unique_items)
            enhanced_items = [self._enhance_item(item) for item in filtered_items]
            
            print(f"Final items after filtering: {len(enhanced_items)}")
            
            return enhanced_items
            
        except Exception as e:
            print(f"Menu extraction error: {e}")
            return []
    
    async def _extract_with_price_focus(self, page: Page) -> List[Dict[str, Any]]:
        """Extract items by focusing on price-containing elements"""
        items = []
        
        try:
            # Get all elements that contain price patterns
            all_elements = await page.query_selector_all('*')
            
            for element in all_elements:
                try:
                    element_text = await element.inner_text()
                    if not element_text or len(element_text) > 500:
                        continue
                    
                    # Check if element contains price
                    has_price = any(re.search(pattern, element_text) for pattern in self.price_patterns)
                    
                    if has_price:
                        # Additional validation
                        if self._is_valid_menu_item(element_text):
                            item = self._parse_item_text(element_text.strip())
                            if item and item.get('price') is not None:
                                item['extraction_method'] = 'price_focused'
                                items.append(item)
                                
                except:
                    continue
            
            return items[:20]  # Limit to prevent too many items
            
        except Exception as e:
            print(f"Price-focused extraction error: {e}")
            return []
    
    async def _extract_with_css_selectors(self, page: Page) -> List[Dict[str, Any]]:
        """Extract using targeted CSS selectors"""
        items = []
        
        for selector in self.menu_selectors:
            try:
                elements = await page.query_selector_all(selector)
                
                for element in elements:
                    try:
                        text = await element.inner_text()
                        if text and self._is_valid_menu_item(text):
                            item = self._parse_item_text(text.strip())
                            if item:
                                item['extraction_method'] = 'css_selectors'
                                item['selector_used'] = selector
                                items.append(item)
                    except:
                        continue
                
                if len(items) >= 10:  # If we found good items, use them
                    break
                    
            except:
                continue
        
        return items
    
    async def _extract_with_text_analysis(self, page: Page) -> List[Dict[str, Any]]:
        """Extract using text analysis with strict filtering"""
        try:
            text_content = await page.evaluate("document.body.innerText")
            items = []
            
            lines = text_content.split('\n')
            
            for line in lines:
                line = line.strip()
                if self._is_valid_menu_item(line):
                    item = self._parse_item_text(line)
                    if item:
                        item['extraction_method'] = 'text_analysis'
                        items.append(item)
            
            return items[:15]  # Limit results
            
        except Exception as e:
            print(f"Text analysis error: {e}")
            return []
    
    def _is_valid_menu_item(self, text: str) -> bool:
        """Enhanced validation for menu items"""
        if not text or len(text.strip()) < 5:
            return False
        
        text_clean = text.strip()
        text_lower = text_clean.lower()
        
        # Check exclusion patterns first
        for pattern in self.exclusion_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return False
        
        # Must have either price OR strong food indicator
        has_price = any(re.search(pattern, text_clean) for pattern in self.price_patterns)
        has_strong_food = any(keyword in text_lower for keyword in self.strong_food_keywords)
        
        # Length check
        reasonable_length = 5 <= len(text_clean) <= 300
        
        # Must have price OR (strong food indicator AND reasonable length)
        return has_price or (has_strong_food and reasonable_length)
    
    def _parse_item_text(self, text: str) -> Optional[Dict[str, Any]]:
        """Enhanced text parsing with better price extraction"""
        try:
            # Extract price with enhanced patterns
            price = None
            price_match = None
            
            for pattern in self.price_patterns:
                match = re.search(pattern, text)
                if match:
                    # Handle different match group structures
                    if match.groups():
                        price_str = match.group(1)
                        # Handle patterns with two groups (dollars and cents)
                        if len(match.groups()) > 1 and match.group(2):
                            price_str = f"{match.group(1)}.{match.group(2)}"
                    else:
                        price_str = match.group(0)
                    
                    # Clean and convert price
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
            name = re.sub(r'^[\-•*\d\.\s]+', '', name)  # Remove leading bullets/numbers
            name = re.sub(r'[\-•*]+$', '', name)  # Remove trailing bullets
            
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
    
    def _filter_valid_items(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter out invalid items"""
        valid_items = []
        
        for item in items:
            name = item.get('name', '').strip()
            
            # Skip items with invalid names
            if len(name) < 3 or len(name) > 100:
                continue
            
            # Skip navigation-like items
            name_lower = name.lower()
            skip_patterns = [
                'profile', 'account', 'login', 'register', 'home', 'about',
                'contact', 'location', 'hours', 'phone', 'email', 'search',
                'filter', 'sort', 'view', 'show', 'hide', 'menu', 'navigation'
            ]
            
            if any(pattern in name_lower for pattern in skip_patterns):
                continue
            
            # Prefer items with prices
            if item.get('price') is not None or any(keyword in name_lower for keyword in self.strong_food_keywords):
                valid_items.append(item)
        
        return valid_items
    
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
        
        # Calculate confidence with price emphasis
        confidence = 0.3  # Lower base
        if item.get('price') is not None: confidence += 0.4  # Higher price bonus
        if item.get('description'): confidence += 0.1
        if item.get('category') != 'other': confidence += 0.1
        if allergens: confidence += 0.05
        if any(keyword in text_for_analysis for keyword in self.strong_food_keywords): confidence += 0.05
        
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
                result['error'] = 'No valid menu items found with improved strategies'
            
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