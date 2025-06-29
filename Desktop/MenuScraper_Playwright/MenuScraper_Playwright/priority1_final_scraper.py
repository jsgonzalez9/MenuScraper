import asyncio
import re
import time
from typing import Dict, List, Any, Optional, Tuple
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
import json

class Priority1FinalScraper:
    """Priority 1 Final Scraper - Optimized for actual menu content extraction"""
    
    def __init__(self, headless: bool = True, timeout: int = 30000):
        self.headless = headless
        self.timeout = timeout
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        
        # Highly targeted menu selectors
        self.menu_selectors = [
            # Menu-specific containers
            '[class*="menu"] [class*="item"]:has-text("$")',
            '[class*="food"] [class*="item"]:has-text("$")',
            '[id*="menu"] [class*="item"]:has-text("$")',
            
            # Menu items with prices
            '[data-testid*="menu-item"]',
            '[data-testid*="food-item"]',
            '[class*="MenuItem"]',
            '[class*="FoodItem"]',
            '[class*="DishItem"]',
            
            # Price-containing elements in menu contexts
            '[class*="menu"] *:has-text("$")',
            '[class*="food"] *:has-text("$")',
            '[class*="dish"] *:has-text("$")',
            '[class*="item"] *:has-text("$")',
            
            # Table rows with prices (common for menus)
            'table tr:has-text("$")',
            'tbody tr:has-text("$")',
            
            # List items with prices (excluding navigation)
             'ul:not([class*="nav"]):not([class*="header"]):not([class*="footer"]) li:has-text("$")',
            'ol li:has-text("$")',
            
            # Div elements with prices (excluding navigation areas)
            'div:has-text("$"):not([class*="nav"]):not([class*="header"]):not([class*="footer"]):not([class*="sidebar"])',
        ]
        
        # Enhanced price patterns
        self.price_patterns = [
            r'\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # $12.99, $1,234.56
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*\$',  # 12.99$
            r'USD\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # USD 12.99
            r'Price[:\s]*\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # Price: $12.99
            r'\$(\d{1,2})(?:\.(\d{2}))?\b',  # $12 or $12.99
            r'\b(\d{1,2})\.(\d{2})\s*\$',   # 12.99$
        ]
        
        # Strong food indicators
        self.food_keywords = [
            'burger', 'pizza', 'pasta', 'salad', 'sandwich', 'steak', 'chicken', 'fish',
            'soup', 'appetizer', 'dessert', 'entree', 'wings', 'ribs', 'tacos', 'sushi',
            'ramen', 'curry', 'rice', 'noodles', 'bread', 'cheese', 'bacon', 'shrimp',
            'grilled', 'fried', 'baked', 'roasted', 'fresh', 'homemade', 'specialty'
        ]
        
        # Strong exclusion patterns for navigation/UI elements
        self.strong_exclusions = [
            # Navigation elements
            r'\b(home|about|contact|location|hours|phone|email)\b',
            r'\b(login|register|sign in|sign up|my profile|account)\b',
            r'\b(write a review|reviews|rating|stars)\b',
            r'\b(facebook|twitter|instagram|social|follow)\b',
            r'\b(privacy|terms|conditions|policy|copyright)\b',
            r'\b(yelp|google|tripadvisor|foursquare)\b',
            r'\b(search|filter|sort|view|show|hide)\b',
            r'\b(collections|guides|blog|news|events)\b',
            r'\b(delivery|pickup|order online|reservations)\b',
            r'\b(map|directions|address|zip code)\b',
            
            # UI elements
            r'^(\s*|\.|\-|\*|•|\d+\s*)$',  # Empty or just punctuation
            r'^[A-Z]{2,}$',  # All caps abbreviations
            r'^\d+$',  # Just numbers
            r'\b(click|tap|select|choose|browse)\b',
            r'\b(more|less|expand|collapse|toggle)\b'
        ]
        
        # Menu link patterns
        self.menu_link_patterns = [
            r'\bmenu\b', r'\bfood\b', r'\border\b', r'\bdine\b', r'\beat\b',
            r'\bcuisine\b', r'\bdelivery\b', r'\btakeout\b', r'\bdining\b'
        ]
    
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
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            return True
            
        except Exception as e:
            print(f"❌ Browser setup failed: {e}")
            return False
    
    async def smart_navigate(self, page: Page, url: str) -> bool:
        """Enhanced navigation with menu detection"""
        try:
            # Navigate with network idle wait
            await page.goto(url, wait_until='networkidle', timeout=self.timeout)
            
            # Wait for content
            await self._wait_for_content(page)
            
            # Check if current page has menu content
            if await self._has_menu_content(page):
                return True
            
            # Look for menu links
            menu_links = await self._find_menu_links(page)
            
            if menu_links:
                for link, score, text in menu_links[:2]:  # Try top 2 links
                    try:
                        await link.click(timeout=5000)
                        await page.wait_for_load_state('networkidle', timeout=15000)
                        await self._wait_for_content(page)
                        
                        if await self._has_menu_content(page):
                            return True
                            
                    except Exception as e:
                        print(f"Menu link click failed: {e}")
                        continue
            
            return True  # Continue even if no menu links found
            
        except Exception as e:
            print(f"Navigation error: {e}")
            return False
    
    async def _wait_for_content(self, page: Page) -> None:
        """Wait for dynamic content to load"""
        try:
            # Wait for basic content
            await page.wait_for_function(
                "document.querySelectorAll('*').length > 30",
                timeout=10000
            )
            
            # Additional wait for JavaScript
            await asyncio.sleep(2)
            
            # Scroll to trigger lazy loading
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
            await asyncio.sleep(1)
            await page.evaluate("window.scrollTo(0, 0)")
            
        except Exception as e:
            print(f"Content wait failed: {e}")
    
    async def _has_menu_content(self, page: Page) -> bool:
        """Detect if page has menu content with price emphasis"""
        try:
            text_content = await page.evaluate("document.body.innerText")
            
            # Count price patterns (high priority)
            price_count = 0
            for pattern in self.price_patterns:
                price_count += len(re.findall(pattern, text_content))
            
            # Count food keywords
            food_count = 0
            text_lower = text_content.lower()
            for keyword in self.food_keywords:
                if keyword in text_lower:
                    food_count += 1
            
            # Enhanced scoring with price emphasis
            total_score = (price_count * 2) + food_count
            
            print(f"Menu detection - Price count: {price_count}, Food count: {food_count}, Total: {total_score}")
            
            return total_score >= 3
            
        except Exception as e:
            print(f"Menu content detection error: {e}")
            return True  # Default to true to continue extraction
    
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
        """Extract menu with focus on price-containing elements"""
        try:
            all_items = []
            
            # Strategy 1: Price-focused extraction (highest priority)
            price_items = await self._extract_price_focused(page)
            if price_items:
                all_items.extend(price_items)
                print(f"Price-focused extraction: {len(price_items)} items")
            
            # Strategy 2: CSS selectors (only if price extraction didn't find enough)
            if len(price_items) < 5:
                css_items = await self._extract_with_css_selectors(page)
                if css_items:
                    all_items.extend(css_items)
                    print(f"CSS selector extraction: {len(css_items)} items")
            
            # Strategy 3: Text analysis (fallback)
            if len(all_items) < 5:
                text_items = await self._extract_with_text_analysis(page)
                if text_items:
                    all_items.extend(text_items)
                    print(f"Text analysis extraction: {len(text_items)} items")
            
            # Process and filter
            unique_items = self._remove_duplicates(all_items)
            filtered_items = self._strict_filter(unique_items)
            enhanced_items = [self._enhance_item(item) for item in filtered_items]
            
            print(f"Final items after strict filtering: {len(enhanced_items)}")
            
            return enhanced_items
            
        except Exception as e:
            print(f"Menu extraction error: {e}")
            return []
    
    async def _extract_price_focused(self, page: Page) -> List[Dict[str, Any]]:
        """Extract elements that contain prices"""
        items = []
        
        try:
            # Find all elements containing dollar signs
            elements_with_prices = await page.query_selector_all('*:has-text("$")')
            
            for element in elements_with_prices:
                try:
                    element_text = await element.inner_text()
                    if not element_text or len(element_text) > 300:
                        continue
                    
                    # Check if it contains a price pattern
                    has_price = any(re.search(pattern, element_text) for pattern in self.price_patterns)
                    
                    if has_price and self._is_valid_menu_item(element_text):
                        item = self._parse_item_text(element_text.strip())
                        if item and item.get('price') is not None:
                            item['extraction_method'] = 'price_focused'
                            items.append(item)
                            
                except:
                    continue
            
            return items[:15]  # Limit to prevent too many items
            
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
                
                # Prioritize selectors that find items with prices
                items_with_prices = [item for item in items if item.get('price') is not None]
                if len(items_with_prices) >= 5:
                    return items_with_prices[:15]
                
                if len(items) >= 10:
                    break
                    
            except:
                continue
        
        return items[:20]
    
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
            
            return items[:15]
            
        except Exception as e:
            print(f"Text analysis error: {e}")
            return []
    
    def _is_valid_menu_item(self, text: str) -> bool:
        """Strict validation for menu items"""
        if not text or len(text.strip()) < 3:
            return False
        
        text_clean = text.strip()
        text_lower = text_clean.lower()
        
        # Strong exclusion check
        for pattern in self.strong_exclusions:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return False
        
        # Must have price OR strong food indicator
        has_price = any(re.search(pattern, text_clean) for pattern in self.price_patterns)
        has_strong_food = any(keyword in text_lower for keyword in self.food_keywords)
        
        # Length check
        reasonable_length = 5 <= len(text_clean) <= 200
        
        return (has_price or has_strong_food) and reasonable_length
    
    def _parse_item_text(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse text to extract menu item information"""
        try:
            # Extract price with enhanced patterns
            price = None
            price_match = None
            
            for pattern in self.price_patterns:
                match = re.search(pattern, text)
                if match:
                    try:
                        if match.groups():
                            price_str = match.group(1)
                            if len(match.groups()) > 1 and match.group(2):
                                price_str = f"{match.group(1)}.{match.group(2)}"
                        else:
                            price_str = match.group(0)
                        
                        price_str = re.sub(r'[^\d.,]', '', price_str)
                        price = float(price_str.replace(',', ''))
                        price_match = match
                        break
                    except:
                        continue
            
            # Extract name
            name = text
            if price_match:
                name = text.replace(price_match.group(0), '').strip()
            
            # Clean name
            name = re.sub(r'\s+', ' ', name).strip()
            name = re.sub(r'^[\-•*\d\.\s]+', '', name)
            name = re.sub(r'[\-•*]+$', '', name)
            
            if len(name) < 2:
                return None
            
            # Extract description
            description = None
            if ' - ' in name:
                parts = name.split(' - ', 1)
                name = parts[0].strip()
                description = parts[1].strip()
            elif '. ' in name and len(name) > 25:
                parts = name.split('. ', 1)
                if len(parts[0]) < 40:
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
        """Categorize menu item"""
        text_lower = text.lower()
        
        categories = {
            'appetizer': ['appetizer', 'starter', 'small plate', 'wings', 'nachos'],
            'salad': ['salad', 'greens', 'caesar', 'garden'],
            'soup': ['soup', 'bisque', 'chowder', 'broth'],
            'sandwich': ['sandwich', 'burger', 'wrap', 'panini'],
            'pasta': ['pasta', 'spaghetti', 'linguine', 'ravioli'],
            'pizza': ['pizza', 'flatbread'],
            'seafood': ['fish', 'salmon', 'shrimp', 'crab'],
            'meat': ['steak', 'beef', 'chicken', 'pork'],
            'dessert': ['dessert', 'cake', 'ice cream'],
            'beverage': ['coffee', 'tea', 'beer', 'wine']
        }
        
        for category, keywords in categories.items():
            if any(keyword in text_lower for keyword in keywords):
                return category
        
        return 'other'
    
    def _strict_filter(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply strict filtering to remove non-menu items"""
        valid_items = []
        
        for item in items:
            name = item.get('name', '').strip()
            
            # Basic validation
            if len(name) < 2 or len(name) > 100:
                continue
            
            # Strong exclusion check
            name_lower = name.lower()
            exclude = False
            for pattern in self.strong_exclusions:
                if re.search(pattern, name_lower, re.IGNORECASE):
                    exclude = True
                    break
            
            if exclude:
                continue
            
            # Prefer items with prices or strong food indicators
            has_price = item.get('price') is not None
            has_food_keyword = any(keyword in name_lower for keyword in self.food_keywords)
            
            if has_price or has_food_keyword:
                valid_items.append(item)
        
        return valid_items
    
    def _enhance_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance item with metadata"""
        # Calculate confidence with price emphasis
        confidence = 0.3  # Base confidence
        if item.get('price') is not None: confidence += 0.4  # High price bonus
        if item.get('description'): confidence += 0.1
        if item.get('category') != 'other': confidence += 0.1
        
        text_for_analysis = f"{item.get('name', '')} {item.get('description', '')}".lower()
        if any(keyword in text_for_analysis for keyword in self.food_keywords): confidence += 0.1
        
        item.update({
            'confidence_score': min(confidence, 1.0),
            'has_price': item.get('price') is not None,
            'has_description': item.get('description') is not None,
            'allergens': [],
            'dietary_tags': []
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
                result['error'] = 'No valid menu items found with final strategies'
            
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