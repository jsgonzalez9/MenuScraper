#!/usr/bin/env python3
"""
Advanced Menu Scraper - Phase 2 Implementation
Targets 60-75% success rate through advanced techniques and larger sample testing
"""

import json
import time
import re
from datetime import datetime
import os
from typing import Dict, List, Any, Optional, Tuple
import requests
from playwright.sync_api import sync_playwright, Page
from urllib.parse import urljoin, urlparse, quote
import easyocr
import cv2
import numpy as np
from PIL import Image
import io
import base64
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MenuItemCandidate:
    """Represents a potential menu item with confidence scoring"""
    name: str
    description: str = ""
    price: Optional[str] = None
    confidence: float = 0.0
    source: str = "unknown"
    allergens: List[str] = None
    category: str = ""
    
    def __post_init__(self):
        if self.allergens is None:
            self.allergens = []

class AdvancedMenuScraper:
    def __init__(self):
        self.easyocr_reader = None
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        # Enhanced menu detection patterns
        self.menu_indicators = [
            'menu', 'food', 'dishes', 'cuisine', 'specialties', 'offerings',
            'appetizers', 'entrees', 'mains', 'desserts', 'beverages',
            'breakfast', 'lunch', 'dinner', 'brunch', 'specials'
        ]
        
        # Price patterns (enhanced)
        self.price_patterns = [
            r'\$\d+\.\d{2}',  # $12.99
            r'\$\d+',         # $12
            r'\d+\.\d{2}\s*\$',  # 12.99$
            r'\d+\s*\$',      # 12$
            r'\d+\.\d{2}',    # 12.99 (context dependent)
            r'USD\s*\d+\.\d{2}',  # USD 12.99
            r'\d+\.\d{2}\s*USD',  # 12.99 USD
        ]
        
        # Food category keywords
        self.food_categories = {
            'appetizers': ['appetizer', 'starter', 'small plate', 'tapas', 'antipasti'],
            'soups': ['soup', 'bisque', 'chowder', 'broth', 'consomme'],
            'salads': ['salad', 'greens', 'caesar', 'cobb'],
            'mains': ['entree', 'main', 'dish', 'plate', 'special'],
            'pasta': ['pasta', 'spaghetti', 'linguine', 'ravioli', 'lasagna'],
            'pizza': ['pizza', 'pie', 'margherita', 'pepperoni'],
            'seafood': ['fish', 'salmon', 'tuna', 'shrimp', 'lobster', 'crab'],
            'meat': ['beef', 'chicken', 'pork', 'lamb', 'steak', 'burger'],
            'desserts': ['dessert', 'cake', 'pie', 'ice cream', 'tiramisu'],
            'beverages': ['drink', 'beverage', 'coffee', 'tea', 'wine', 'beer']
        }
    
    def get_easyocr_reader(self):
        """Initialize EasyOCR reader if not already done"""
        if self.easyocr_reader is None:
            try:
                self.easyocr_reader = easyocr.Reader(['en'])
                logger.info("✅ EasyOCR initialized successfully")
            except Exception as e:
                logger.error(f"❌ EasyOCR initialization failed: {e}")
        return self.easyocr_reader
    
    def find_restaurant_website(self, restaurant_name: str, location: str) -> Optional[str]:
        """Find restaurant's official website using search"""
        try:
            # Simple search simulation - in production, use Google Custom Search API
            search_terms = [f"{restaurant_name} restaurant", f"{restaurant_name} {location}"]
            
            # For now, return None - this would be implemented with actual search API
            return None
        except Exception as e:
            logger.error(f"Website search failed: {e}")
            return None
    
    def extract_menu_from_images(self, page: Page) -> List[MenuItemCandidate]:
        """Extract menu items from images using OCR"""
        candidates = []
        
        try:
            # Find images that might contain menus
            image_selectors = [
                'img[alt*="menu" i]',
                'img[src*="menu" i]',
                'img[alt*="food" i]',
                '.menu img',
                '.food-menu img',
                '[class*="menu"] img'
            ]
            
            reader = self.get_easyocr_reader()
            if not reader:
                return candidates
            
            for selector in image_selectors:
                try:
                    images = page.query_selector_all(selector)
                    for img in images[:3]:  # Limit to 3 images per selector
                        try:
                            # Get image source
                            src = img.get_attribute('src')
                            if not src:
                                continue
                            
                            # Convert relative URLs to absolute
                            if src.startswith('//'):
                                src = 'https:' + src
                            elif src.startswith('/'):
                                src = urljoin(page.url, src)
                            
                            # Download and process image
                            response = self.session.get(src, timeout=10)
                            if response.status_code == 200:
                                # Convert to PIL Image
                                image = Image.open(io.BytesIO(response.content))
                                
                                # Convert to numpy array for OCR
                                img_array = np.array(image)
                                
                                # Perform OCR
                                results = reader.readtext(img_array)
                                
                                # Process OCR results
                                for (bbox, text, confidence) in results:
                                    if confidence > 0.5 and self.is_potential_menu_item(text):
                                        candidate = MenuItemCandidate(
                                            name=text.strip(),
                                            confidence=confidence,
                                            source="ocr_image"
                                        )
                                        candidates.append(candidate)
                                        
                        except Exception as e:
                            logger.debug(f"Image OCR failed: {e}")
                            continue
                            
                except Exception as e:
                    logger.debug(f"Image selector failed: {e}")
                    continue
            
            logger.info(f"📸 OCR extracted {len(candidates)} potential items from images")
            
        except Exception as e:
            logger.error(f"Image extraction failed: {e}")
        
        return candidates
    
    def extract_from_structured_data(self, page: Page) -> List[MenuItemCandidate]:
        """Extract menu items from structured data (JSON-LD, microdata)"""
        candidates = []
        
        try:
            # Look for JSON-LD structured data
            json_scripts = page.query_selector_all('script[type="application/ld+json"]')
            
            for script in json_scripts:
                try:
                    content = script.inner_text()
                    data = json.loads(content)
                    
                    # Check if it's restaurant/menu data
                    if isinstance(data, dict):
                        schema_type = data.get('@type', '')
                        if 'Restaurant' in schema_type or 'Menu' in schema_type:
                            # Extract menu items from structured data
                            menu_items = self.parse_structured_menu(data)
                            candidates.extend(menu_items)
                            
                except Exception as e:
                    logger.debug(f"JSON-LD parsing failed: {e}")
                    continue
            
            logger.info(f"📋 Structured data extracted {len(candidates)} items")
            
        except Exception as e:
            logger.error(f"Structured data extraction failed: {e}")
        
        return candidates
    
    def parse_structured_menu(self, data: dict) -> List[MenuItemCandidate]:
        """Parse menu items from structured data"""
        candidates = []
        
        def extract_items(obj, path=""):
            if isinstance(obj, dict):
                # Look for menu-related keys
                for key, value in obj.items():
                    if any(indicator in key.lower() for indicator in ['menu', 'food', 'dish', 'item']):
                        if isinstance(value, list):
                            for item in value:
                                if isinstance(item, dict):
                                    name = item.get('name', '')
                                    description = item.get('description', '')
                                    price = item.get('price', item.get('offers', {}).get('price', ''))
                                    
                                    if name:
                                        candidate = MenuItemCandidate(
                                            name=name,
                                            description=description,
                                            price=str(price) if price else None,
                                            confidence=0.9,
                                            source="structured_data"
                                        )
                                        candidates.append(candidate)
                    else:
                        extract_items(value, f"{path}.{key}")
            elif isinstance(obj, list):
                for item in obj:
                    extract_items(item, path)
        
        extract_items(data)
        return candidates
    
    def extract_from_reviews_advanced(self, page: Page) -> List[MenuItemCandidate]:
        """Advanced review mining with better pattern recognition"""
        candidates = []
        
        try:
            # Enhanced review selectors
            review_selectors = [
                '[class*="review"] p',
                '[class*="comment"] p',
                '[data-testid*="review"]',
                '.review-content',
                '.user-review',
                '[class*="review-text"]',
                '.review p',
                '[class*="comment-text"]'
            ]
            
            review_texts = []
            for selector in review_selectors:
                elements = page.query_selector_all(selector)
                for element in elements[:20]:  # Limit reviews processed
                    text = element.inner_text().strip()
                    if len(text) > 20:  # Filter out very short texts
                        review_texts.append(text)
            
            # Enhanced food mention patterns
            food_patterns = [
                r'(?:had|tried|ordered|got|ate)\s+(?:the\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
                r'(?:delicious|amazing|great|excellent|tasty)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
                r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:was|is)\s+(?:delicious|amazing|great|excellent|tasty)',
                r'recommend\s+(?:the\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
                r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+\$\d+',
                r'\$\d+\s+for\s+(?:the\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            ]
            
            for text in review_texts:
                for pattern in food_patterns:
                    matches = re.finditer(pattern, text, re.IGNORECASE)
                    for match in matches:
                        item_name = match.group(1).strip()
                        
                        # Validate if it's likely a food item
                        if self.is_potential_menu_item(item_name) and len(item_name.split()) <= 4:
                            # Calculate confidence based on context
                            confidence = self.calculate_food_confidence(item_name, text)
                            
                            if confidence > 0.3:
                                candidate = MenuItemCandidate(
                                    name=item_name,
                                    description=text[:100] + "..." if len(text) > 100 else text,
                                    confidence=confidence,
                                    source="review_mining",
                                    category=self.categorize_food_item(item_name)
                                )
                                candidates.append(candidate)
            
            logger.info(f"💬 Advanced review mining found {len(candidates)} items")
            
        except Exception as e:
            logger.error(f"Advanced review mining failed: {e}")
        
        return candidates
    
    def calculate_food_confidence(self, item_name: str, context: str) -> float:
        """Calculate confidence score for a potential food item"""
        confidence = 0.5  # Base confidence
        
        item_lower = item_name.lower()
        context_lower = context.lower()
        
        # Boost confidence for food-related words
        food_indicators = ['delicious', 'tasty', 'amazing', 'great', 'excellent', 'recommend', 'ordered', 'tried']
        for indicator in food_indicators:
            if indicator in context_lower:
                confidence += 0.1
        
        # Boost for price mentions
        if re.search(r'\$\d+', context):
            confidence += 0.2
        
        # Boost for food categories
        for category, keywords in self.food_categories.items():
            if any(keyword in item_lower for keyword in keywords):
                confidence += 0.15
                break
        
        # Penalize for non-food words
        non_food_words = ['service', 'staff', 'atmosphere', 'location', 'parking', 'music', 'decor']
        if any(word in item_lower for word in non_food_words):
            confidence -= 0.3
        
        return min(1.0, max(0.0, confidence))
    
    def categorize_food_item(self, item_name: str) -> str:
        """Categorize a food item"""
        item_lower = item_name.lower()
        
        for category, keywords in self.food_categories.items():
            if any(keyword in item_lower for keyword in keywords):
                return category
        
        return "other"
    
    def is_potential_menu_item(self, text: str) -> bool:
        """Enhanced check if text could be a menu item"""
        if not text or len(text.strip()) < 2:
            return False
        
        text_clean = text.strip().lower()
        
        # Exclude obvious non-food items
        excluded_patterns = [
            r'^\d+$',  # Just numbers
            r'^[a-z]$',  # Single letters
            r'copyright|privacy|terms|contact|address|phone|hours|location|directions',
            r'follow us|social media|newsletter|subscribe|website|email',
            r'^(and|or|the|a|an|in|on|at|to|for|with|by)$',  # Common words
            r'^(monday|tuesday|wednesday|thursday|friday|saturday|sunday)$',  # Days
            r'^(january|february|march|april|may|june|july|august|september|october|november|december)$',  # Months
        ]
        
        for pattern in excluded_patterns:
            if re.search(pattern, text_clean):
                return False
        
        # Check for food-related keywords
        food_keywords = [
            'soup', 'salad', 'sandwich', 'burger', 'pizza', 'pasta', 'chicken', 'beef', 'fish',
            'salmon', 'tuna', 'shrimp', 'lobster', 'steak', 'pork', 'lamb', 'rice', 'noodles',
            'bread', 'cheese', 'sauce', 'cream', 'butter', 'wine', 'beer', 'coffee', 'tea',
            'cake', 'pie', 'ice cream', 'chocolate', 'vanilla', 'strawberry', 'apple', 'orange',
            'grilled', 'fried', 'baked', 'roasted', 'steamed', 'sauteed', 'braised', 'marinated',
            'appetizer', 'entree', 'dessert', 'special', 'fresh', 'organic', 'homemade'
        ]
        
        # If it contains food keywords, likely a menu item
        if any(keyword in text_clean for keyword in food_keywords):
            return True
        
        # Check if it looks like a dish name (capitalized words)
        words = text.split()
        if len(words) >= 2 and all(word[0].isupper() for word in words if word):
            return True
        
        return False
    
    def merge_and_deduplicate_candidates(self, all_candidates: List[MenuItemCandidate]) -> List[Dict[str, Any]]:
        """Merge similar candidates and remove duplicates"""
        if not all_candidates:
            return []
        
        # Group similar items
        grouped = {}
        
        for candidate in all_candidates:
            # Create a normalized key for grouping
            key = re.sub(r'[^a-zA-Z0-9\s]', '', candidate.name.lower()).strip()
            key = ' '.join(key.split())  # Normalize whitespace
            
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(candidate)
        
        # Merge grouped candidates
        final_items = []
        
        for key, candidates in grouped.items():
            if not candidates:
                continue
            
            # Sort by confidence
            candidates.sort(key=lambda x: x.confidence, reverse=True)
            best = candidates[0]
            
            # Merge information from other candidates
            descriptions = [c.description for c in candidates if c.description]
            prices = [c.price for c in candidates if c.price]
            sources = list(set(c.source for c in candidates))
            
            # Create final item
            item = {
                'name': best.name,
                'description': descriptions[0] if descriptions else best.description,
                'price': prices[0] if prices else best.price,
                'confidence': best.confidence,
                'sources': sources,
                'category': best.category,
                'allergens': list(set(sum([c.allergens for c in candidates], [])))
            }
            
            final_items.append(item)
        
        # Sort by confidence
        final_items.sort(key=lambda x: x['confidence'], reverse=True)
        
        return final_items
    
    def advanced_menu_detection(self, page: Page, url: str) -> Dict[str, Any]:
        """Advanced menu detection with multiple strategies"""
        logger.info(f"🔍 Advanced menu detection for: {url}")
        
        all_candidates = []
        
        try:
            # Navigate to the page
            page.goto(url, wait_until='networkidle', timeout=30000)
            page.wait_for_timeout(2000)  # Wait for dynamic content
            
            # Strategy 1: Structured data extraction
            structured_candidates = self.extract_from_structured_data(page)
            all_candidates.extend(structured_candidates)
            
            # Strategy 2: Enhanced review mining
            review_candidates = self.extract_from_reviews_advanced(page)
            all_candidates.extend(review_candidates)
            
            # Strategy 3: Image OCR extraction
            image_candidates = self.extract_menu_from_images(page)
            all_candidates.extend(image_candidates)
            
            # Strategy 4: Enhanced CSS selector extraction
            css_candidates = self.extract_with_enhanced_selectors(page)
            all_candidates.extend(css_candidates)
            
            # Strategy 5: Price-based extraction
            price_candidates = self.extract_price_based_items(page)
            all_candidates.extend(price_candidates)
            
            # Merge and deduplicate
            final_items = self.merge_and_deduplicate_candidates(all_candidates)
            
            # Filter by confidence threshold
            high_confidence_items = [item for item in final_items if item['confidence'] > 0.4]
            
            success = len(high_confidence_items) > 0
            ocr_used = any('ocr' in item.get('sources', []) for item in high_confidence_items)
            
            result = {
                'menu_items': high_confidence_items,
                'total_items': len(high_confidence_items),
                'scraping_success': success,
                'ocr_used': ocr_used,
                'source': 'advanced_scraping',
                'strategies_used': len([c for c in [structured_candidates, review_candidates, image_candidates, css_candidates, price_candidates] if c]),
                'raw_candidates': len(all_candidates)
            }
            
            if success:
                logger.info(f"✅ Success! Found {len(high_confidence_items)} high-confidence items")
            else:
                logger.info(f"❌ No high-confidence menu items found")
            
            return result
            
        except Exception as e:
            logger.error(f"Advanced menu detection failed: {e}")
            return {
                'menu_items': [],
                'total_items': 0,
                'scraping_success': False,
                'ocr_used': False,
                'source': 'advanced_scraping',
                'error': str(e)
            }
    
    def extract_with_enhanced_selectors(self, page: Page) -> List[MenuItemCandidate]:
        """Extract using enhanced CSS selectors"""
        candidates = []
        
        # Enhanced selectors for menu items
        selectors = [
            # Menu-specific selectors
            '.menu-item', '.menu-dish', '.food-item', '.dish-item',
            '[class*="menu-item"]', '[class*="dish"]', '[class*="food"]',
            
            # List-based selectors
            '.menu ul li', '.food-menu li', '.dish-list li',
            
            # Card-based selectors
            '.menu-card', '.dish-card', '.food-card',
            
            # Table-based selectors
            '.menu-table tr', '.price-list tr',
            
            # Generic content selectors
            '[data-testid*="menu"]', '[data-testid*="dish"]',
            '[id*="menu"] p', '[class*="menu"] p'
        ]
        
        for selector in selectors:
            try:
                elements = page.query_selector_all(selector)
                for element in elements[:15]:  # Limit per selector
                    text = element.inner_text().strip()
                    if text and self.is_potential_menu_item(text):
                        # Look for price in the same element or nearby
                        price = self.extract_price_from_element(element)
                        
                        candidate = MenuItemCandidate(
                            name=text,
                            price=price,
                            confidence=0.6,
                            source="enhanced_css",
                            category=self.categorize_food_item(text)
                        )
                        candidates.append(candidate)
                        
            except Exception as e:
                logger.debug(f"Selector {selector} failed: {e}")
                continue
        
        logger.info(f"🎯 Enhanced CSS extraction found {len(candidates)} items")
        return candidates
    
    def extract_price_based_items(self, page: Page) -> List[MenuItemCandidate]:
        """Extract items based on price patterns"""
        candidates = []
        
        try:
            # Get all text content from body
            text_content = page.locator('body').inner_text()
            
            # Find price patterns with context
            for pattern in self.price_patterns:
                matches = list(re.finditer(pattern, text_content))
                
                for match in matches:
                    price = match.group()
                    start_pos = match.start()
                    
                    # Get context around the price (50 chars before)
                    context_start = max(0, start_pos - 50)
                    context = text_content[context_start:start_pos].strip()
                    
                    # Look for potential item name in the context
                    lines = context.split('\n')
                    for line in reversed(lines[-3:]):  # Check last 3 lines
                        line = line.strip()
                        if line and self.is_potential_menu_item(line):
                            candidate = MenuItemCandidate(
                                name=line,
                                price=price,
                                confidence=0.7,
                                source="price_based",
                                category=self.categorize_food_item(line)
                            )
                            candidates.append(candidate)
                            break
            
            logger.info(f"💰 Price-based extraction found {len(candidates)} items")
            
        except Exception as e:
            logger.error(f"Price-based extraction failed: {e}")
        
        return candidates
    
    def extract_price_from_element(self, element) -> Optional[str]:
        """Extract price from an element or its siblings"""
        try:
            # Check element text for price
            text = element.inner_text()
            for pattern in self.price_patterns:
                match = re.search(pattern, text)
                if match:
                    return match.group()
            
            # Check next sibling
            try:
                next_sibling = element.evaluate('el => el.nextElementSibling')
                if next_sibling:
                    sibling_text = element.evaluate('el => el.nextElementSibling.textContent')
                    for pattern in self.price_patterns:
                        match = re.search(pattern, sibling_text or '')
                        if match:
                            return match.group()
            except:
                pass
            
            return None
            
        except Exception:
            return None

# Example usage and testing
if __name__ == "__main__":
    scraper = AdvancedMenuScraper()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Test URL
        test_url = "https://www.yelp.com/biz/some-restaurant"
        
        try:
            result = scraper.advanced_menu_detection(page, test_url)
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(f"Test failed: {e}")
        finally:
            browser.close()