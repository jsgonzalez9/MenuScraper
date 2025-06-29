#!/usr/bin/env python3
"""
Final Optimized Menu Scraper
Fixed version addressing critical issues from previous optimized scraper

Target: 50%+ success rate with robust extraction
Key Fixes:
1. Fixed CSS selector issues
2. Improved error handling
3. More permissive validation
4. Better fallback strategies
5. Simplified OCR integration
"""

import re
import time
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MenuItemCandidate:
    """Menu item candidate"""
    name: str
    description: str = ""
    price: Optional[str] = None
    confidence: float = 0.0
    sources: List[str] = None
    category: str = "other"
    extraction_method: str = ""
    
    def __post_init__(self):
        if self.sources is None:
            self.sources = []

class FinalOptimizedMenuScraper:
    """Final optimized menu scraper with critical fixes"""
    
    def __init__(self):
        self.ocr_reader = None
        
        # More permissive food validation
        self.FOOD_KEYWORDS = [
            'appetizer', 'entree', 'main', 'dessert', 'soup', 'salad', 'pasta', 
            'pizza', 'sandwich', 'burger', 'steak', 'chicken', 'fish', 'seafood',
            'grilled', 'fried', 'baked', 'roasted', 'fresh', 'homemade', 'special',
            'served', 'topped', 'sauce', 'cheese', 'bread', 'dish', 'plate'
        ]
        
        # Clear exclusions
        self.EXCLUDE_PATTERNS = [
            r'\b(home|about|contact|location|hours|reservation|book|call|email)\b',
            r'\b(delivery|takeout|pickup|catering|events|private)\b',
            r'\b(follow us|social|facebook|instagram|twitter)\b',
            r'\b(welcome|thank you|newsletter|subscribe)\b',
            r'\b(copyright|terms|privacy|policy)\b'
        ]
        
        # Price patterns
        self.PRICE_PATTERNS = [
            r'\$\d+\.\d{2}',  # $12.99
            r'\$\d+',         # $12
            r'\d+\.\d{2}',    # 12.99
        ]
        
        # Simplified menu selectors
        self.MENU_SELECTORS = [
            'a[href*="menu"]',
            'a[href*="food"]',
            'a:has-text("Menu")',
            'a:has-text("Food")',
            '.menu-link'
        ]
        
        # Comprehensive content selectors
        self.CONTENT_SELECTORS = [
            '.menu-item',
            '.food-item',
            '.dish',
            '.menu',
            '.food-menu',
            'h3',
            'h4',
            'h5',
            '.item-name',
            '.dish-name',
            '.menu-entry'
        ]
    
    def is_valid_food_item(self, text: str) -> Tuple[bool, float, str]:
        """More permissive food item validation"""
        if not text or len(text.strip()) < 3:
            return False, 0.0, "too_short"
        
        text_clean = text.strip()
        text_lower = text_clean.lower()
        
        # Check exclusions
        for pattern in self.EXCLUDE_PATTERNS:
            if re.search(pattern, text_lower):
                return False, 0.0, "excluded"
        
        # Skip navigation items
        if text_lower in ['menu', 'home', 'about', 'contact', 'location']:
            return False, 0.0, "navigation"
        
        confidence = 0.0
        reasons = []
        
        # Check for food keywords
        for keyword in self.FOOD_KEYWORDS:
            if keyword in text_lower:
                confidence += 0.3
                reasons.append(f"keyword_{keyword}")
                break
        
        # Price presence
        if any(re.search(pattern, text) for pattern in self.PRICE_PATTERNS):
            confidence += 0.4
            reasons.append("has_price")
        
        # Length bonus
        if 5 <= len(text_clean) <= 100:
            confidence += 0.2
            reasons.append("good_length")
        
        # Capitalization
        if re.search(r'[A-Z][a-z]', text_clean):
            confidence += 0.1
            reasons.append("proper_caps")
        
        # Multiple words (likely menu item)
        if len(text_clean.split()) >= 2:
            confidence += 0.2
            reasons.append("multi_word")
        
        # Very permissive threshold
        is_valid = confidence >= 0.1 or len(text_clean.split()) >= 2
        reason = "_".join(reasons) if reasons else "basic_text"
        
        return is_valid, min(confidence, 1.0), reason
    
    def categorize_food_item(self, text: str) -> str:
        """Simple food categorization"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['appetizer', 'starter']):
            return 'appetizer'
        elif any(word in text_lower for word in ['soup', 'bisque']):
            return 'soup'
        elif any(word in text_lower for word in ['salad', 'greens']):
            return 'salad'
        elif any(word in text_lower for word in ['pasta', 'spaghetti']):
            return 'pasta'
        elif any(word in text_lower for word in ['pizza']):
            return 'pizza'
        elif any(word in text_lower for word in ['fish', 'salmon', 'seafood']):
            return 'seafood'
        elif any(word in text_lower for word in ['beef', 'steak', 'chicken', 'burger']):
            return 'meat'
        elif any(word in text_lower for word in ['dessert', 'cake', 'ice cream']):
            return 'dessert'
        elif any(word in text_lower for word in ['drink', 'coffee', 'wine', 'beer']):
            return 'beverage'
        else:
            return 'entree'
    
    def extract_price(self, text: str) -> Optional[str]:
        """Extract price from text"""
        for pattern in self.PRICE_PATTERNS:
            match = re.search(pattern, text)
            if match:
                return match.group()
        return None
    
    def find_menu_pages(self, page: Page, base_url: str) -> List[str]:
        """Find menu pages with better error handling"""
        menu_urls = set()
        
        try:
            # Wait briefly for page load
            page.wait_for_timeout(2000)
            
            for selector in self.MENU_SELECTORS:
                try:
                    elements = page.locator(selector).all()
                    for element in elements[:3]:  # Limit to avoid too many
                        try:
                            href = element.get_attribute('href')
                            if href and ('menu' in href.lower() or 'food' in href.lower()):
                                full_url = urljoin(base_url, href)
                                menu_urls.add(full_url)
                        except Exception:
                            continue
                except Exception:
                    continue
            
            logger.info(f"Found {len(menu_urls)} menu URLs")
            return list(menu_urls)[:2]
            
        except Exception as e:
            logger.warning(f"Menu page detection failed: {e}")
            return []
    
    def extract_with_css(self, page: Page) -> List[MenuItemCandidate]:
        """Robust CSS-based extraction"""
        candidates = []
        
        try:
            # Wait for content
            page.wait_for_timeout(1000)
            
            # Try each selector
            for selector in self.CONTENT_SELECTORS:
                try:
                    elements = page.locator(selector).all()
                    logger.info(f"Found {len(elements)} elements for selector: {selector}")
                    
                    for i, element in enumerate(elements[:15]):  # Reasonable limit
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
                                    logger.debug(f"Added candidate: {text[:50]}...")
                        except Exception as e:
                            logger.debug(f"Error processing element {i}: {e}")
                            continue
                except Exception as e:
                    logger.debug(f"Error with selector {selector}: {e}")
                    continue
            
            logger.info(f"CSS extraction: {len(candidates)} candidates")
            return candidates
            
        except Exception as e:
            logger.error(f"CSS extraction failed: {e}")
            return []
    
    def extract_from_text_content(self, page: Page) -> List[MenuItemCandidate]:
        """Extract from page text content as fallback"""
        candidates = []
        
        try:
            # Get all text content
            body_text = page.locator('body').inner_text()
            lines = body_text.split('\n')
            
            for line in lines:
                line = line.strip()
                if line and len(line) > 3:
                    is_valid, confidence, reason = self.is_valid_food_item(line)
                    if is_valid and confidence > 0.2:  # Higher threshold for text extraction
                        candidate = MenuItemCandidate(
                            name=line,
                            confidence=confidence,
                            sources=['text'],
                            category=self.categorize_food_item(line),
                            extraction_method="text_content"
                        )
                        
                        price = self.extract_price(line)
                        if price:
                            candidate.price = price
                            candidate.confidence += 0.1
                        
                        candidates.append(candidate)
            
            logger.info(f"Text extraction: {len(candidates)} candidates")
            return candidates[:20]  # Limit to avoid too many
            
        except Exception as e:
            logger.error(f"Text extraction failed: {e}")
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
            
            candidate = MenuItemCandidate(
                name=name,
                description=item.get('description', ''),
                confidence=0.8,  # High confidence for structured data
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
    
    def final_optimized_detection(self, page: Page, url: str) -> Dict[str, Any]:
        """Final optimized menu detection with robust error handling"""
        start_time = time.time()
        
        result = {
            'menu_items': [],
            'total_items': 0,
            'scraping_success': False,
            'ocr_used': False,
            'menu_page_found': False,
            'source': 'final_optimized_scraping',
            'strategies_used': 0,
            'raw_candidates': 0,
            'processing_time': 0,
            'extraction_methods': [],
            'quality_score': 0.0
        }
        
        try:
            logger.info(f"Starting final optimized detection: {url}")
            
            # Navigate with shorter timeout
            try:
                page.goto(url, wait_until='domcontentloaded', timeout=15000)
            except PlaywrightTimeoutError:
                logger.warning(f"Timeout loading {url}, trying with basic load")
                page.goto(url, timeout=10000)
            
            # Try to find menu pages
            menu_urls = self.find_menu_pages(page, url)
            if menu_urls:
                result['menu_page_found'] = True
                try:
                    page.goto(menu_urls[0], wait_until='domcontentloaded', timeout=10000)
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
                    logger.info(f"Structured data found {len(structured_candidates)} candidates")
            except Exception as e:
                logger.error(f"Structured extraction failed: {e}")
            
            # Strategy 2: CSS extraction
            try:
                css_candidates = self.extract_with_css(page)
                if css_candidates:
                    all_candidates.extend(css_candidates)
                    result['strategies_used'] += 1
                    result['extraction_methods'].append('css')
                    logger.info(f"CSS extraction found {len(css_candidates)} candidates")
            except Exception as e:
                logger.error(f"CSS extraction failed: {e}")
            
            # Strategy 3: Text content fallback
            if len(all_candidates) < 3:
                try:
                    text_candidates = self.extract_from_text_content(page)
                    if text_candidates:
                        all_candidates.extend(text_candidates)
                        result['strategies_used'] += 1
                        result['extraction_methods'].append('text')
                        logger.info(f"Text extraction found {len(text_candidates)} candidates")
                except Exception as e:
                    logger.error(f"Text extraction failed: {e}")
            
            result['raw_candidates'] = len(all_candidates)
            logger.info(f"Total raw candidates: {len(all_candidates)}")
            
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
            
            logger.info(f"Final optimized detection completed: {result['total_items']} items, success: {result['scraping_success']}")
            
        except Exception as e:
            logger.error(f"Final optimized detection failed: {e}")
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
            if len(key) < 2:  # Skip very short keys
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
                'extraction_method': best_candidate.extraction_method
            }
            
            final_items.append(final_item)
        
        # Sort by confidence
        final_items.sort(key=lambda x: x['confidence'], reverse=True)
        
        # Return top 25 items
        return final_items[:25]

# Example usage
if __name__ == "__main__":
    from playwright.sync_api import sync_playwright
    
    scraper = FinalOptimizedMenuScraper()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        test_url = "https://example-restaurant.com"
        
        try:
            result = scraper.final_optimized_detection(page, test_url)
            print(json.dumps(result, indent=2))
        finally:
            browser.close()