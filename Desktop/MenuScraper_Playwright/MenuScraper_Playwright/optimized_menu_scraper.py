#!/usr/bin/env python3
"""
Optimized Menu Scraper - Final Version
Combines best features from all previous iterations with key optimizations

Target: 50%+ success rate with high-quality extractions
Key Optimizations:
1. Balanced filtering (not overly strict)
2. Enhanced OCR integration
3. Improved menu navigation
4. Smart fallback strategies
5. Better error handling
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
    """Optimized menu item candidate"""
    name: str
    description: str = ""
    price: Optional[str] = None
    confidence: float = 0.0
    sources: List[str] = None
    category: str = "other"
    allergens: List[str] = None
    extraction_method: str = ""
    
    def __post_init__(self):
        if self.sources is None:
            self.sources = []
        if self.allergens is None:
            self.allergens = []

class OptimizedMenuScraper:
    """Optimized menu scraper with balanced approach"""
    
    def __init__(self):
        self.ocr_reader = None
        
        # Balanced food validation (less strict than next-gen)
        self.FOOD_INDICATORS = {
            'strong': ['appetizer', 'entree', 'main', 'dessert', 'soup', 'salad', 'pasta', 
                      'pizza', 'sandwich', 'burger', 'steak', 'chicken', 'fish', 'seafood'],
            'medium': ['grilled', 'fried', 'baked', 'roasted', 'fresh', 'homemade', 'special',
                      'served', 'topped', 'sauce', 'cheese', 'bread'],
            'weak': ['dish', 'plate', 'order', 'choice']
        }
        
        # Clear exclusions (avoid false positives)
        self.EXCLUDE_PATTERNS = [
            r'\b(home|about|contact|location|hours|reservation|book|call|email)\b',
            r'\b(delivery|takeout|pickup|catering|events|private)\b',
            r'\b(follow us|social|facebook|instagram|twitter)\b',
            r'\b(welcome|thank you|newsletter|subscribe)\b'
        ]
        
        # Enhanced price patterns
        self.PRICE_PATTERNS = [
            r'\$\d+\.\d{2}',  # $12.99
            r'\$\d+',         # $12
            r'\d+\.\d{2}',    # 12.99
            r'\d+\s*dollars?', # 12 dollars
        ]
        
        # Comprehensive menu selectors
        self.MENU_SELECTORS = [
            # Direct menu links
            'a[href*="menu" i]',
            'a[href*="food" i]',
            'a[href*="dining" i]',
            
            # Menu text
            'a:has-text("Menu")',
            'a:has-text("Food")',
            'a:has-text("Our Menu")',
            'a:has-text("View Menu")',
            
            # Navigation
            '.nav a[href*="menu" i]',
            '.navigation a[href*="menu" i]',
            '.menu-link',
            '.food-menu'
        ]
        
        # Enhanced content selectors
        self.CONTENT_SELECTORS = [
            # Menu containers
            '.menu',
            '.food-menu',
            '.menu-section',
            '.menu-category',
            '.menu-items',
            
            # Individual items
            '.menu-item',
            '.food-item',
            '.dish',
            '.item',
            
            # Text patterns
            'h3, h4, h5',  # Common for menu item names
            '.price-item',
            '.menu-entry'
        ]
        
        # OCR image selectors
        self.IMAGE_SELECTORS = [
            'img[src*="menu" i]',
            'img[alt*="menu" i]',
            'img[src*="food" i]',
            '.menu img',
            '.food img',
            '.gallery img'
        ]
    
    def get_easyocr_reader(self):
        """Initialize OCR reader"""
        if self.ocr_reader is None:
            try:
                self.ocr_reader = easyocr.Reader(['en'], gpu=False)
                logger.info("EasyOCR reader initialized")
            except Exception as e:
                logger.error(f"Failed to initialize EasyOCR: {e}")
                self.ocr_reader = None
        return self.ocr_reader
    
    def is_valid_food_item(self, text: str) -> Tuple[bool, float, str]:
        """Balanced food item validation"""
        if not text or len(text.strip()) < 3:
            return False, 0.0, "too_short"
        
        text_clean = text.strip()
        text_lower = text_clean.lower()
        
        # Check exclusions first
        for pattern in self.EXCLUDE_PATTERNS:
            if re.search(pattern, text_lower):
                return False, 0.0, "excluded"
        
        # Skip if it's just a single word that's likely a category
        if len(text_clean.split()) == 1 and text_lower in ['italian', 'chinese', 'mexican', 'american', 'french']:
            return False, 0.0, "category_name"
        
        confidence = 0.0
        reasons = []
        
        # Strong food indicators
        for indicator in self.FOOD_INDICATORS['strong']:
            if indicator in text_lower:
                confidence += 0.4
                reasons.append(f"strong_{indicator}")
                break  # Only count one strong indicator
        
        # Medium indicators
        for indicator in self.FOOD_INDICATORS['medium']:
            if indicator in text_lower:
                confidence += 0.2
                reasons.append(f"medium_{indicator}")
                break
        
        # Weak indicators
        for indicator in self.FOOD_INDICATORS['weak']:
            if indicator in text_lower:
                confidence += 0.1
                reasons.append(f"weak_{indicator}")
                break
        
        # Price presence
        if any(re.search(pattern, text) for pattern in self.PRICE_PATTERNS):
            confidence += 0.3
            reasons.append("has_price")
        
        # Length bonus (reasonable menu item length)
        if 5 <= len(text_clean) <= 80:
            confidence += 0.1
            reasons.append("good_length")
        
        # Capitalization pattern (proper menu item formatting)
        if re.search(r'[A-Z][a-z]', text_clean):
            confidence += 0.1
            reasons.append("proper_caps")
        
        # Lower threshold for acceptance (more permissive)
        is_valid = confidence >= 0.2  # Reduced from 0.3
        reason = "_".join(reasons) if reasons else "no_indicators"
        
        return is_valid, min(confidence, 1.0), reason
    
    def categorize_food_item(self, text: str) -> str:
        """Food categorization"""
        text_lower = text.lower()
        
        categories = {
            'appetizer': ['appetizer', 'starter', 'small plate'],
            'soup': ['soup', 'bisque', 'chowder'],
            'salad': ['salad', 'greens'],
            'pasta': ['pasta', 'spaghetti', 'linguine', 'ravioli'],
            'pizza': ['pizza', 'flatbread'],
            'seafood': ['fish', 'salmon', 'shrimp', 'lobster', 'crab'],
            'meat': ['beef', 'steak', 'chicken', 'pork', 'burger'],
            'dessert': ['dessert', 'cake', 'pie', 'ice cream'],
            'beverage': ['drink', 'coffee', 'tea', 'juice', 'wine', 'beer']
        }
        
        for category, keywords in categories.items():
            if any(keyword in text_lower for keyword in keywords):
                return category
        
        return 'entree'
    
    def extract_price(self, text: str) -> Optional[str]:
        """Extract price from text"""
        for pattern in self.PRICE_PATTERNS:
            match = re.search(pattern, text)
            if match:
                return match.group()
        return None
    
    def find_menu_pages(self, page: Page, base_url: str) -> List[str]:
        """Find menu pages with timeout handling"""
        menu_urls = set()
        
        try:
            # Wait for page load
            page.wait_for_load_state('networkidle', timeout=8000)
            
            for selector in self.MENU_SELECTORS:
                try:
                    elements = page.locator(selector).all()
                    for element in elements[:5]:  # Limit to avoid too many
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
            
            logger.info(f"Found {len(menu_urls)} menu URLs")
            return list(menu_urls)[:2]  # Limit to top 2
            
        except Exception as e:
            logger.warning(f"Menu page detection failed: {e}")
            return []
    
    def _is_valid_menu_url(self, url: str) -> bool:
        """Validate menu URL"""
        url_lower = url.lower()
        return ('menu' in url_lower or 'food' in url_lower) and 'contact' not in url_lower
    
    def extract_with_css(self, page: Page) -> List[MenuItemCandidate]:
        """CSS-based extraction with smart filtering"""
        candidates = []
        
        try:
            # Wait for content
            page.wait_for_timeout(1500)
            
            for selector in self.CONTENT_SELECTORS:
                try:
                    elements = page.locator(selector).all()
                    for element in elements[:20]:  # Reasonable limit
                        try:
                            text = element.inner_text().strip()
                            if text and len(text) > 2:
                                is_valid, confidence, reason = self.is_valid_food_item(text)
                                if is_valid:
                                    candidate = MenuItemCandidate(
                                        name=text,
                                        confidence=confidence,
                                        sources=['css'],
                                        category=self.categorize_food_item(text),
                                        extraction_method=f"css_{selector.replace('.', '').replace('[', '').replace(']', '')}"
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
            
            logger.info(f"CSS extraction: {len(candidates)} candidates")
            return candidates
            
        except Exception as e:
            logger.error(f"CSS extraction failed: {e}")
            return []
    
    def extract_with_ocr(self, page: Page) -> List[MenuItemCandidate]:
        """OCR extraction with better error handling"""
        candidates = []
        
        try:
            ocr_reader = self.get_easyocr_reader()
            if not ocr_reader:
                return candidates
            
            # Find images
            image_elements = []
            for selector in self.IMAGE_SELECTORS:
                try:
                    elements = page.locator(selector).all()
                    image_elements.extend(elements[:2])  # Limit per selector
                except Exception:
                    continue
            
            logger.info(f"Found {len(image_elements)} images for OCR")
            
            # Process images
            for i, img_element in enumerate(image_elements[:3]):
                try:
                    screenshot = img_element.screenshot()
                    results = ocr_reader.readtext(screenshot)
                    
                    for (bbox, text, ocr_confidence) in results:
                        if ocr_confidence > 0.4:  # Lower OCR threshold
                            is_valid, food_confidence, reason = self.is_valid_food_item(text)
                            if is_valid:
                                candidate = MenuItemCandidate(
                                    name=text.strip(),
                                    confidence=food_confidence * ocr_confidence,
                                    sources=['ocr'],
                                    category=self.categorize_food_item(text),
                                    extraction_method=f"ocr_img_{i}"
                                )
                                
                                price = self.extract_price(text)
                                if price:
                                    candidate.price = price
                                    candidate.confidence += 0.1
                                
                                candidates.append(candidate)
                
                except Exception as e:
                    logger.warning(f"OCR failed for image {i}: {e}")
                    continue
            
            logger.info(f"OCR extraction: {len(candidates)} candidates")
            return candidates
            
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return []
    
    def extract_structured_data(self, page: Page) -> List[MenuItemCandidate]:
        """Extract from JSON-LD structured data"""
        candidates = []
        
        try:
            json_scripts = page.locator('script[type="application/ld+json"]').all()
            
            for script in json_scripts:
                try:
                    content = script.inner_text()
                    data = json.loads(content)
                    
                    if isinstance(data, dict):
                        candidates.extend(self._extract_from_schema(data))
                    elif isinstance(data, list):
                        for item in data:
                            candidates.extend(self._extract_from_schema(item))
                            
                except Exception:
                    continue
            
            logger.info(f"Structured data: {len(candidates)} candidates")
            return candidates
            
        except Exception as e:
            logger.error(f"Structured data extraction failed: {e}")
            return []
    
    def _extract_from_schema(self, data: Dict) -> List[MenuItemCandidate]:
        """Extract from schema.org data"""
        candidates = []
        
        try:
            # Restaurant with menu
            if data.get('@type') == 'Restaurant' and 'hasMenu' in data:
                menu = data['hasMenu']
                if isinstance(menu, dict) and 'hasMenuSection' in menu:
                    for section in menu['hasMenuSection']:
                        if 'hasMenuItem' in section:
                            for item in section['hasMenuItem']:
                                candidate = self._create_candidate_from_item(item)
                                if candidate:
                                    candidates.append(candidate)
        
        except Exception:
            pass
        
        return candidates
    
    def _create_candidate_from_item(self, item: Dict) -> Optional[MenuItemCandidate]:
        """Create candidate from menu item"""
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
                sources=['structured'],
                category=self.categorize_food_item(name),
                extraction_method="json_ld"
            )
            
            # Extract price
            if 'offers' in item:
                offers = item['offers']
                if isinstance(offers, dict) and 'price' in offers:
                    candidate.price = str(offers['price'])
                elif isinstance(offers, list) and offers:
                    candidate.price = str(offers[0].get('price', ''))
            
            return candidate
            
        except Exception:
            return None
    
    def optimized_menu_detection(self, page: Page, url: str) -> Dict[str, Any]:
        """Optimized menu detection with balanced approach"""
        start_time = time.time()
        
        result = {
            'menu_items': [],
            'total_items': 0,
            'scraping_success': False,
            'ocr_used': False,
            'menu_page_found': False,
            'source': 'optimized_scraping',
            'strategies_used': 0,
            'raw_candidates': 0,
            'processing_time': 0,
            'extraction_methods': [],
            'quality_score': 0.0
        }
        
        try:
            logger.info(f"Starting optimized detection: {url}")
            
            # Navigate with timeout
            page.goto(url, wait_until='networkidle', timeout=25000)
            
            # Try to find menu pages
            menu_urls = self.find_menu_pages(page, url)
            if menu_urls:
                result['menu_page_found'] = True
                try:
                    page.goto(menu_urls[0], wait_until='networkidle', timeout=15000)
                    logger.info(f"Navigated to menu page")
                except Exception as e:
                    logger.warning(f"Menu navigation failed: {e}")
            
            all_candidates = []
            
            # Strategy 1: Structured data
            try:
                structured_candidates = self.extract_structured_data(page)
                if structured_candidates:
                    all_candidates.extend(structured_candidates)
                    result['strategies_used'] += 1
                    result['extraction_methods'].append('structured')
            except Exception as e:
                logger.error(f"Structured extraction failed: {e}")
            
            # Strategy 2: CSS extraction
            try:
                css_candidates = self.extract_with_css(page)
                if css_candidates:
                    all_candidates.extend(css_candidates)
                    result['strategies_used'] += 1
                    result['extraction_methods'].append('css')
            except Exception as e:
                logger.error(f"CSS extraction failed: {e}")
            
            # Strategy 3: OCR (if other methods found few items)
            if len(all_candidates) < 5:
                try:
                    ocr_candidates = self.extract_with_ocr(page)
                    if ocr_candidates:
                        all_candidates.extend(ocr_candidates)
                        result['strategies_used'] += 1
                        result['extraction_methods'].append('ocr')
                        result['ocr_used'] = True
                except Exception as e:
                    logger.error(f"OCR extraction failed: {e}")
            
            result['raw_candidates'] = len(all_candidates)
            
            # Process candidates
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
            
            logger.info(f"Optimized detection completed: {result['total_items']} items")
            
        except Exception as e:
            logger.error(f"Optimized detection failed: {e}")
            result['error'] = str(e)
            result['processing_time'] = round(time.time() - start_time, 2)
        
        return result
    
    def _process_candidates(self, candidates: List[MenuItemCandidate]) -> List[Dict[str, Any]]:
        """Process and deduplicate candidates"""
        if not candidates:
            return []
        
        # Group by normalized name
        grouped = {}
        for candidate in candidates:
            # Normalize name for grouping
            key = re.sub(r'[^a-zA-Z0-9\s]', '', candidate.name.lower()).strip()
            if len(key) < 3:  # Skip very short keys
                continue
                
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(candidate)
        
        # Select best from each group
        final_items = []
        for name_key, group in grouped.items():
            # Sort by confidence and sources
            best_candidate = max(group, key=lambda c: (c.confidence, len(c.sources)))
            
            # Merge sources
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
        
        # Sort by confidence
        final_items.sort(key=lambda x: x['confidence'], reverse=True)
        
        # Return top 30 items
        return final_items[:30]

# Example usage
if __name__ == "__main__":
    from playwright.sync_api import sync_playwright
    
    scraper = OptimizedMenuScraper()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        test_url = "https://example-restaurant.com"
        
        try:
            result = scraper.optimized_menu_detection(page, test_url)
            print(json.dumps(result, indent=2))
        finally:
            browser.close()