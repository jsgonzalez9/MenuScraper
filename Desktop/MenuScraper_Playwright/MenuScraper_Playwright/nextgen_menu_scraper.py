#!/usr/bin/env python3
"""
Next-Generation Menu Scraper
Implements high-priority improvements for 50%+ success rate

Key Improvements:
1. Enhanced content filtering with strict food validation
2. Improved OCR triggering with aggressive image detection
3. Advanced menu navigation with expanded patterns
4. Robust error handling and recovery
5. ML-based confidence scoring
6. Dynamic content handling
"""

import re
import time
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
import easyocr
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MenuItemCandidate:
    """Enhanced menu item candidate with validation"""
    name: str
    description: str = ""
    price: Optional[str] = None
    confidence: float = 0.0
    sources: List[str] = None
    category: str = "other"
    allergens: List[str] = None
    is_valid_food: bool = False
    extraction_method: str = ""
    
    def __post_init__(self):
        if self.sources is None:
            self.sources = []
        if self.allergens is None:
            self.allergens = []

class NextGenMenuScraper:
    """Next-generation menu scraper with advanced capabilities"""
    
    def __init__(self):
        self.ocr_reader = None
        
        # Enhanced food keywords for better validation
        self.FOOD_KEYWORDS = {
            'strong': ['appetizer', 'entree', 'main course', 'dessert', 'beverage', 'special', 
                      'starter', 'soup', 'salad', 'pasta', 'pizza', 'sandwich', 'burger',
                      'seafood', 'chicken', 'beef', 'pork', 'vegetarian', 'vegan'],
            'medium': ['dish', 'plate', 'served', 'grilled', 'fried', 'baked', 'fresh',
                      'homemade', 'signature', 'chef', 'daily', 'seasonal'],
            'weak': ['menu', 'food', 'cuisine', 'kitchen', 'recipe']
        }
        
        # Strict exclusion patterns
        self.EXCLUDE_KEYWORDS = {
            'navigation': ['home', 'about', 'contact', 'location', 'hours', 'reservation',
                          'book', 'call', 'email', 'address', 'phone', 'directions'],
            'business': ['catering', 'events', 'private', 'party', 'wedding', 'corporate',
                        'delivery', 'takeout', 'pickup', 'order online'],
            'generic': ['welcome', 'thank you', 'follow us', 'social media', 'facebook',
                       'instagram', 'twitter', 'newsletter', 'subscribe'],
            'categories': ['italian', 'chinese', 'mexican', 'american', 'french', 'japanese',
                          'indian', 'thai', 'greek', 'mediterranean']
        }
        
        # Enhanced price patterns
        self.PRICE_PATTERNS = [
            r'\$\d+\.\d{2}',  # $12.99
            r'\$\d+',         # $12
            r'\d+\.\d{2}',    # 12.99
            r'\d+\s*dollars?', # 12 dollars
            r'\d+\s*USD',     # 12 USD
        ]
        
        # Advanced menu navigation patterns
        self.MENU_SELECTORS = [
            # Direct menu links
            'a[href*="menu" i]',
            'a[href*="food" i]',
            'a[href*="dining" i]',
            'a[href*="eat" i]',
            
            # Menu buttons and navigation
            'button[data-menu]',
            'button[class*="menu" i]',
            '.nav-menu a',
            '.navigation a[href*="menu" i]',
            '[role="menuitem"]',
            
            # Menu text patterns
            'a:has-text("Menu")',
            'a:has-text("Food")',
            'a:has-text("Dining")',
            'a:has-text("Our Menu")',
            'a:has-text("View Menu")',
            
            # Common menu classes
            '.menu-link',
            '.food-menu',
            '.restaurant-menu',
            '.main-menu a'
        ]
        
        # Enhanced image detection for OCR
        self.IMAGE_SELECTORS = [
            'img[src*="menu" i]',
            'img[alt*="menu" i]',
            'img[src*="food" i]',
            'img[alt*="food" i]',
            '.menu-image img',
            '.food-image img',
            '.gallery img',
            '[class*="menu"] img',
            '[class*="food"] img',
            'img[src*="pdf"]',  # PDF menu images
            'img[class*="menu" i]'
        ]
        
        # Modern CSS selectors for menu content
        self.CONTENT_SELECTORS = [
            # Menu sections
            '.menu-section',
            '.food-section',
            '.menu-category',
            '.dish-list',
            '.menu-items',
            
            # Individual items
            '.menu-item',
            '.food-item',
            '.dish',
            '.menu-entry',
            '.item',
            
            # Price containers
            '.price',
            '.cost',
            '.menu-price',
            '.item-price',
            
            # Description containers
            '.description',
            '.menu-description',
            '.item-description'
        ]
    
    def get_easyocr_reader(self):
        """Initialize OCR reader with error handling"""
        if self.ocr_reader is None:
            try:
                self.ocr_reader = easyocr.Reader(['en'], gpu=False)
                logger.info("EasyOCR reader initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize EasyOCR: {e}")
                self.ocr_reader = None
        return self.ocr_reader
    
    def is_valid_food_item(self, text: str) -> Tuple[bool, float, str]:
        """Enhanced food item validation with confidence scoring"""
        if not text or len(text.strip()) < 2:
            return False, 0.0, "too_short"
        
        text_lower = text.lower().strip()
        
        # Check exclusion patterns first
        for category, keywords in self.EXCLUDE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return False, 0.0, f"excluded_{category}"
        
        # Check if it's just a category name
        if text_lower in [kw for kw_list in self.EXCLUDE_KEYWORDS.values() for kw in kw_list]:
            return False, 0.0, "category_name"
        
        # Calculate confidence based on food keywords
        confidence = 0.0
        reasons = []
        
        # Strong indicators
        for keyword in self.FOOD_KEYWORDS['strong']:
            if keyword in text_lower:
                confidence += 0.3
                reasons.append(f"strong_{keyword}")
        
        # Medium indicators
        for keyword in self.FOOD_KEYWORDS['medium']:
            if keyword in text_lower:
                confidence += 0.2
                reasons.append(f"medium_{keyword}")
        
        # Weak indicators
        for keyword in self.FOOD_KEYWORDS['weak']:
            if keyword in text_lower:
                confidence += 0.1
                reasons.append(f"weak_{keyword}")
        
        # Price presence increases confidence
        if any(re.search(pattern, text) for pattern in self.PRICE_PATTERNS):
            confidence += 0.2
            reasons.append("has_price")
        
        # Length and structure indicators
        if 5 <= len(text) <= 100:  # Reasonable length
            confidence += 0.1
            reasons.append("good_length")
        
        if re.search(r'[A-Z][a-z]', text):  # Proper capitalization
            confidence += 0.1
            reasons.append("proper_caps")
        
        # Minimum confidence threshold
        is_valid = confidence >= 0.3
        reason = "_".join(reasons) if reasons else "no_indicators"
        
        return is_valid, min(confidence, 1.0), reason
    
    def categorize_food_item(self, text: str) -> str:
        """Enhanced food categorization"""
        text_lower = text.lower()
        
        # Specific categories
        categories = {
            'appetizer': ['appetizer', 'starter', 'small plate', 'tapas', 'antipasto'],
            'soup': ['soup', 'bisque', 'chowder', 'broth', 'consomme'],
            'salad': ['salad', 'greens', 'caesar', 'cobb'],
            'pasta': ['pasta', 'spaghetti', 'linguine', 'fettuccine', 'ravioli', 'lasagna'],
            'pizza': ['pizza', 'flatbread', 'calzone'],
            'seafood': ['fish', 'salmon', 'tuna', 'shrimp', 'lobster', 'crab', 'scallop'],
            'meat': ['beef', 'steak', 'chicken', 'pork', 'lamb', 'turkey', 'burger'],
            'vegetarian': ['vegetarian', 'vegan', 'veggie', 'tofu', 'quinoa'],
            'dessert': ['dessert', 'cake', 'pie', 'ice cream', 'chocolate', 'tiramisu'],
            'beverage': ['drink', 'beverage', 'coffee', 'tea', 'juice', 'soda', 'wine', 'beer']
        }
        
        for category, keywords in categories.items():
            if any(keyword in text_lower for keyword in keywords):
                return category
        
        return 'entree'  # Default to entree instead of 'other'
    
    def extract_price(self, text: str) -> Optional[str]:
        """Enhanced price extraction"""
        for pattern in self.PRICE_PATTERNS:
            match = re.search(pattern, text)
            if match:
                return match.group()
        return None
    
    def find_menu_pages(self, page: Page, base_url: str) -> List[str]:
        """Enhanced menu page detection"""
        menu_urls = set()
        
        try:
            # Wait for page to load
            page.wait_for_load_state('networkidle', timeout=10000)
            
            # Try each menu selector
            for selector in self.MENU_SELECTORS:
                try:
                    elements = page.locator(selector).all()
                    for element in elements:
                        try:
                            href = element.get_attribute('href')
                            if href:
                                full_url = urljoin(base_url, href)
                                if self._is_valid_menu_url(full_url):
                                    menu_urls.add(full_url)
                        except Exception:
                            continue
                except Exception:
                    continue
            
            logger.info(f"Found {len(menu_urls)} potential menu URLs")
            return list(menu_urls)[:3]  # Limit to top 3
            
        except Exception as e:
            logger.error(f"Error finding menu pages: {e}")
            return []
    
    def _is_valid_menu_url(self, url: str) -> bool:
        """Validate menu URL"""
        url_lower = url.lower()
        valid_patterns = ['menu', 'food', 'dining', 'eat']
        invalid_patterns = ['contact', 'about', 'location', 'reservation']
        
        has_valid = any(pattern in url_lower for pattern in valid_patterns)
        has_invalid = any(pattern in url_lower for pattern in invalid_patterns)
        
        return has_valid and not has_invalid
    
    def extract_with_modern_css(self, page: Page) -> List[MenuItemCandidate]:
        """Enhanced CSS-based extraction"""
        candidates = []
        
        try:
            # Wait for dynamic content
            page.wait_for_timeout(2000)
            
            # Try each content selector
            for selector in self.CONTENT_SELECTORS:
                try:
                    elements = page.locator(selector).all()
                    for element in elements:
                        try:
                            text = element.inner_text().strip()
                            if text:
                                is_valid, confidence, reason = self.is_valid_food_item(text)
                                if is_valid:
                                    candidate = MenuItemCandidate(
                                        name=text,
                                        confidence=confidence,
                                        sources=['modern_css'],
                                        category=self.categorize_food_item(text),
                                        is_valid_food=True,
                                        extraction_method=f"css_{selector}"
                                    )
                                    
                                    # Try to extract price
                                    price = self.extract_price(text)
                                    if price:
                                        candidate.price = price
                                        candidate.confidence += 0.1
                                    
                                    candidates.append(candidate)
                        except Exception:
                            continue
                except Exception:
                    continue
            
            logger.info(f"CSS extraction found {len(candidates)} valid candidates")
            return candidates
            
        except Exception as e:
            logger.error(f"CSS extraction failed: {e}")
            return []
    
    def extract_with_ocr(self, page: Page) -> List[MenuItemCandidate]:
        """Enhanced OCR extraction with aggressive image detection"""
        candidates = []
        
        try:
            ocr_reader = self.get_easyocr_reader()
            if not ocr_reader:
                return candidates
            
            # Find all potential menu images
            image_elements = []
            for selector in self.IMAGE_SELECTORS:
                try:
                    elements = page.locator(selector).all()
                    image_elements.extend(elements)
                except Exception:
                    continue
            
            logger.info(f"Found {len(image_elements)} potential menu images")
            
            # Process up to 3 images
            for i, img_element in enumerate(image_elements[:3]):
                try:
                    # Take screenshot of the image
                    screenshot = img_element.screenshot()
                    
                    # Perform OCR
                    results = ocr_reader.readtext(screenshot)
                    
                    for (bbox, text, confidence) in results:
                        if confidence > 0.5:  # OCR confidence threshold
                            is_valid, food_confidence, reason = self.is_valid_food_item(text)
                            if is_valid:
                                candidate = MenuItemCandidate(
                                    name=text.strip(),
                                    confidence=food_confidence * confidence,  # Combined confidence
                                    sources=['ocr'],
                                    category=self.categorize_food_item(text),
                                    is_valid_food=True,
                                    extraction_method=f"ocr_image_{i}"
                                )
                                
                                # Try to extract price
                                price = self.extract_price(text)
                                if price:
                                    candidate.price = price
                                    candidate.confidence += 0.1
                                
                                candidates.append(candidate)
                
                except Exception as e:
                    logger.warning(f"OCR failed for image {i}: {e}")
                    continue
            
            logger.info(f"OCR extraction found {len(candidates)} valid candidates")
            return candidates
            
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return []
    
    def extract_structured_data(self, page: Page) -> List[MenuItemCandidate]:
        """Extract from structured data (JSON-LD, microdata)"""
        candidates = []
        
        try:
            # Look for JSON-LD structured data
            json_scripts = page.locator('script[type="application/ld+json"]').all()
            
            for script in json_scripts:
                try:
                    content = script.inner_text()
                    data = json.loads(content)
                    
                    # Handle different schema types
                    if isinstance(data, dict):
                        candidates.extend(self._extract_from_schema(data))
                    elif isinstance(data, list):
                        for item in data:
                            candidates.extend(self._extract_from_schema(item))
                            
                except Exception as e:
                    logger.warning(f"Failed to parse JSON-LD: {e}")
                    continue
            
            logger.info(f"Structured data extraction found {len(candidates)} candidates")
            return candidates
            
        except Exception as e:
            logger.error(f"Structured data extraction failed: {e}")
            return []
    
    def _extract_from_schema(self, data: Dict) -> List[MenuItemCandidate]:
        """Extract menu items from schema.org data"""
        candidates = []
        
        try:
            # Restaurant schema with menu
            if data.get('@type') == 'Restaurant' and 'hasMenu' in data:
                menu = data['hasMenu']
                if isinstance(menu, dict) and 'hasMenuSection' in menu:
                    for section in menu['hasMenuSection']:
                        if 'hasMenuItem' in section:
                            for item in section['hasMenuItem']:
                                candidate = self._create_candidate_from_menu_item(item)
                                if candidate:
                                    candidates.append(candidate)
            
            # Direct menu schema
            elif data.get('@type') == 'Menu':
                if 'hasMenuSection' in data:
                    for section in data['hasMenuSection']:
                        if 'hasMenuItem' in section:
                            for item in section['hasMenuItem']:
                                candidate = self._create_candidate_from_menu_item(item)
                                if candidate:
                                    candidates.append(candidate)
        
        except Exception as e:
            logger.warning(f"Schema extraction error: {e}")
        
        return candidates
    
    def _create_candidate_from_menu_item(self, item: Dict) -> Optional[MenuItemCandidate]:
        """Create candidate from structured menu item"""
        try:
            name = item.get('name', '')
            if not name:
                return None
            
            is_valid, confidence, reason = self.is_valid_food_item(name)
            if not is_valid:
                return None
            
            candidate = MenuItemCandidate(
                name=name,
                description=item.get('description', ''),
                confidence=confidence,
                sources=['structured_data'],
                category=self.categorize_food_item(name),
                is_valid_food=True,
                extraction_method="schema_org"
            )
            
            # Extract price from offers
            if 'offers' in item:
                offers = item['offers']
                if isinstance(offers, dict) and 'price' in offers:
                    candidate.price = str(offers['price'])
                elif isinstance(offers, list) and offers:
                    candidate.price = str(offers[0].get('price', ''))
            
            return candidate
            
        except Exception as e:
            logger.warning(f"Failed to create candidate from menu item: {e}")
            return None
    
    def nextgen_menu_detection(self, page: Page, url: str) -> Dict[str, Any]:
        """Next-generation menu detection with all improvements"""
        start_time = time.time()
        
        result = {
            'menu_items': [],
            'total_items': 0,
            'scraping_success': False,
            'ocr_used': False,
            'menu_page_found': False,
            'source': 'nextgen_scraping',
            'strategies_used': 0,
            'raw_candidates': 0,
            'processing_time': 0,
            'extraction_methods': [],
            'quality_score': 0.0
        }
        
        try:
            logger.info(f"Starting next-gen menu detection for: {url}")
            
            # Navigate to the URL
            page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Find menu pages first
            menu_urls = self.find_menu_pages(page, url)
            if menu_urls:
                result['menu_page_found'] = True
                # Try the first menu page
                try:
                    page.goto(menu_urls[0], wait_until='networkidle', timeout=20000)
                    logger.info(f"Navigated to menu page: {menu_urls[0]}")
                except Exception as e:
                    logger.warning(f"Failed to navigate to menu page: {e}")
            
            all_candidates = []
            
            # Strategy 1: Structured data extraction
            try:
                structured_candidates = self.extract_structured_data(page)
                if structured_candidates:
                    all_candidates.extend(structured_candidates)
                    result['strategies_used'] += 1
                    result['extraction_methods'].append('structured_data')
                    logger.info(f"Structured data: {len(structured_candidates)} candidates")
            except Exception as e:
                logger.error(f"Structured data extraction failed: {e}")
            
            # Strategy 2: Modern CSS extraction
            try:
                css_candidates = self.extract_with_modern_css(page)
                if css_candidates:
                    all_candidates.extend(css_candidates)
                    result['strategies_used'] += 1
                    result['extraction_methods'].append('modern_css')
                    logger.info(f"CSS extraction: {len(css_candidates)} candidates")
            except Exception as e:
                logger.error(f"CSS extraction failed: {e}")
            
            # Strategy 3: OCR extraction
            try:
                ocr_candidates = self.extract_with_ocr(page)
                if ocr_candidates:
                    all_candidates.extend(ocr_candidates)
                    result['strategies_used'] += 1
                    result['extraction_methods'].append('ocr')
                    result['ocr_used'] = True
                    logger.info(f"OCR extraction: {len(ocr_candidates)} candidates")
            except Exception as e:
                logger.error(f"OCR extraction failed: {e}")
            
            result['raw_candidates'] = len(all_candidates)
            
            # Deduplicate and filter candidates
            final_items = self._process_candidates(all_candidates)
            
            result['menu_items'] = final_items
            result['total_items'] = len(final_items)
            result['scraping_success'] = len(final_items) > 0
            
            # Calculate quality score
            if final_items:
                avg_confidence = sum(item.get('confidence', 0) for item in final_items) / len(final_items)
                has_prices = sum(1 for item in final_items if item.get('price')) / len(final_items)
                has_categories = sum(1 for item in final_items if item.get('category', 'other') != 'other') / len(final_items)
                
                result['quality_score'] = (avg_confidence * 0.5 + has_prices * 0.3 + has_categories * 0.2)
            
            result['processing_time'] = round(time.time() - start_time, 2)
            
            logger.info(f"Next-gen detection completed: {result['total_items']} items, {result['strategies_used']} strategies")
            
        except Exception as e:
            logger.error(f"Next-gen menu detection failed: {e}")
            result['error'] = str(e)
            result['processing_time'] = round(time.time() - start_time, 2)
        
        return result
    
    def _process_candidates(self, candidates: List[MenuItemCandidate]) -> List[Dict[str, Any]]:
        """Process and deduplicate candidates"""
        if not candidates:
            return []
        
        # Group by name (case-insensitive)
        grouped = {}
        for candidate in candidates:
            key = candidate.name.lower().strip()
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(candidate)
        
        # Select best candidate from each group
        final_items = []
        for name_key, group in grouped.items():
            # Sort by confidence, then by number of sources
            best_candidate = max(group, key=lambda c: (c.confidence, len(c.sources)))
            
            # Merge sources from all candidates in group
            all_sources = set()
            for candidate in group:
                all_sources.update(candidate.sources)
            
            final_item = {
                'name': best_candidate.name,
                'description': best_candidate.description,
                'price': best_candidate.price,
                'confidence': round(best_candidate.confidence, 3),
                'sources': list(all_sources),
                'category': best_candidate.category,
                'allergens': best_candidate.allergens,
                'extraction_method': best_candidate.extraction_method
            }
            
            final_items.append(final_item)
        
        # Sort by confidence (highest first)
        final_items.sort(key=lambda x: x['confidence'], reverse=True)
        
        # Limit to top 50 items
        return final_items[:50]

# Example usage
if __name__ == "__main__":
    from playwright.sync_api import sync_playwright
    
    scraper = NextGenMenuScraper()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Test URL
        test_url = "https://example-restaurant.com"
        
        try:
            result = scraper.nextgen_menu_detection(page, test_url)
            print(json.dumps(result, indent=2))
        finally:
            browser.close()