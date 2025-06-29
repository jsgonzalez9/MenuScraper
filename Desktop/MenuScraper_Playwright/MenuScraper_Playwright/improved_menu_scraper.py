#!/usr/bin/env python3
"""
Improved Menu Scraper - Phase 3 Quick Wins Implementation
Focuses on high-priority fixes: OCR pipeline, menu navigation, better selectors
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

class ImprovedMenuScraper:
    def __init__(self):
        self.easyocr_reader = None
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        # Menu page indicators
        self.menu_page_indicators = [
            'menu', 'food', 'dining', 'cuisine', 'dishes', 'order',
            'takeout', 'delivery', 'catering', 'specials', 'offerings'
        ]
        
        # Enhanced price patterns
        self.price_patterns = [
            r'\$\d+\.\d{2}',  # $12.99
            r'\$\d+',         # $12
            r'\d+\.\d{2}\s*\$',  # 12.99$
            r'\d+\s*\$',      # 12$
            r'USD\s*\d+\.\d{2}',  # USD 12.99
            r'\d+\.\d{2}\s*USD',  # 12.99 USD
        ]
        
        # Food category keywords (enhanced)
        self.food_categories = {
            'appetizers': ['appetizer', 'starter', 'small plate', 'tapas', 'antipasti', 'hors', 'calamari', 'wings', 'nachos'],
            'soups': ['soup', 'bisque', 'chowder', 'broth', 'consomme', 'gazpacho', 'minestrone'],
            'salads': ['salad', 'greens', 'caesar', 'cobb', 'arugula', 'spinach', 'kale'],
            'mains': ['entree', 'main', 'dish', 'plate', 'special', 'signature'],
            'pasta': ['pasta', 'spaghetti', 'linguine', 'ravioli', 'lasagna', 'fettuccine', 'penne', 'gnocchi'],
            'pizza': ['pizza', 'pie', 'margherita', 'pepperoni', 'flatbread'],
            'seafood': ['fish', 'salmon', 'tuna', 'shrimp', 'lobster', 'crab', 'scallops', 'mussels', 'oysters'],
            'meat': ['beef', 'chicken', 'pork', 'lamb', 'steak', 'burger', 'ribs', 'turkey'],
            'desserts': ['dessert', 'cake', 'pie', 'ice cream', 'tiramisu', 'cheesecake', 'chocolate', 'gelato'],
            'beverages': ['drink', 'beverage', 'coffee', 'tea', 'wine', 'beer', 'cocktail', 'smoothie', 'juice']
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
    
    def find_menu_page(self, page: Page) -> bool:
        """Try to navigate to a dedicated menu page if it exists"""
        try:
            # Look for menu links
            menu_link_selectors = [
                'a[href*="menu" i]',
                'a[href*="food" i]',
                'a[href*="dining" i]',
                'a:has-text("Menu")',
                'a:has-text("Food")',
                'a:has-text("Dining")',
                'a:has-text("Order")',
                'a:has-text("Takeout")',
                'a:has-text("Delivery")',
                '.menu-link',
                '.food-link',
                '[data-testid*="menu"]'
            ]
            
            for selector in menu_link_selectors:
                try:
                    menu_links = page.query_selector_all(selector)
                    for link in menu_links:
                        href = link.get_attribute('href')
                        text = link.inner_text().strip().lower()
                        
                        # Check if this looks like a menu link
                        if href and any(indicator in text for indicator in self.menu_page_indicators):
                            # Convert relative URL to absolute
                            if href.startswith('/'):
                                href = urljoin(page.url, href)
                            elif not href.startswith('http'):
                                continue
                            
                            logger.info(f"🔗 Found menu link: {href}")
                            
                            # Navigate to menu page
                            page.goto(href, wait_until='networkidle', timeout=20000)
                            page.wait_for_timeout(2000)
                            
                            logger.info(f"✅ Successfully navigated to menu page")
                            return True
                            
                except Exception as e:
                    logger.debug(f"Menu link navigation failed: {e}")
                    continue
            
            logger.info("ℹ️ No dedicated menu page found, using current page")
            return False
            
        except Exception as e:
            logger.error(f"Menu page navigation failed: {e}")
            return False
    
    def extract_menu_from_images_enhanced(self, page: Page) -> List[MenuItemCandidate]:
        """Enhanced image extraction with better detection and preprocessing"""
        candidates = []
        
        try:
            # Enhanced image selectors
            image_selectors = [
                # Direct image tags
                'img[alt*="menu" i]',
                'img[src*="menu" i]',
                'img[alt*="food" i]',
                'img[src*="food" i]',
                'img[class*="menu" i]',
                'img[class*="food" i]',
                
                # Menu-specific containers
                '.menu img',
                '.food-menu img',
                '.menu-image img',
                '.dish-image img',
                
                # Modern picture elements
                'picture img',
                'figure img',
                
                # Gallery and carousel images
                '.gallery img',
                '.carousel img',
                '.slider img',
                
                # PDF and document embeds
                'embed[src*="menu" i]',
                'object[data*="menu" i]',
                'iframe[src*="menu" i]'
            ]
            
            # Also check for background images in CSS
            background_elements = page.query_selector_all('[style*="background-image"]')
            
            reader = self.get_easyocr_reader()
            if not reader:
                return candidates
            
            processed_urls = set()  # Avoid processing same image multiple times
            
            # Process regular images
            for selector in image_selectors:
                try:
                    images = page.query_selector_all(selector)
                    for img in images[:5]:  # Limit per selector
                        try:
                            src = img.get_attribute('src')
                            if not src or src in processed_urls:
                                continue
                            
                            processed_urls.add(src)
                            
                            # Convert relative URLs to absolute
                            if src.startswith('//'):
                                src = 'https:' + src
                            elif src.startswith('/'):
                                src = urljoin(page.url, src)
                            elif not src.startswith('http'):
                                continue
                            
                            # Skip very small images (likely icons)
                            try:
                                width = img.get_attribute('width')
                                height = img.get_attribute('height')
                                if width and height:
                                    if int(width) < 100 or int(height) < 100:
                                        continue
                            except:
                                pass
                            
                            # Download and process image
                            response = self.session.get(src, timeout=15)
                            if response.status_code == 200 and len(response.content) > 1000:  # Skip tiny images
                                candidates.extend(self.process_image_with_ocr(response.content, src))
                                
                        except Exception as e:
                            logger.debug(f"Image processing failed: {e}")
                            continue
                            
                except Exception as e:
                    logger.debug(f"Image selector {selector} failed: {e}")
                    continue
            
            # Process background images
            for element in background_elements[:3]:  # Limit background images
                try:
                    style = element.get_attribute('style')
                    if style:
                        # Extract URL from background-image CSS
                        match = re.search(r'background-image:\s*url\(["\']?([^"\')]+)["\']?\)', style)
                        if match:
                            bg_url = match.group(1)
                            if bg_url not in processed_urls:
                                processed_urls.add(bg_url)
                                
                                if bg_url.startswith('//'):
                                    bg_url = 'https:' + bg_url
                                elif bg_url.startswith('/'):
                                    bg_url = urljoin(page.url, bg_url)
                                
                                response = self.session.get(bg_url, timeout=15)
                                if response.status_code == 200:
                                    candidates.extend(self.process_image_with_ocr(response.content, bg_url))
                                    
                except Exception as e:
                    logger.debug(f"Background image processing failed: {e}")
                    continue
            
            logger.info(f"📸 Enhanced OCR extracted {len(candidates)} potential items from {len(processed_urls)} images")
            
        except Exception as e:
            logger.error(f"Enhanced image extraction failed: {e}")
        
        return candidates
    
    def process_image_with_ocr(self, image_content: bytes, source_url: str) -> List[MenuItemCandidate]:
        """Process a single image with OCR and return candidates"""
        candidates = []
        
        try:
            # Convert to PIL Image
            image = Image.open(io.BytesIO(image_content))
            
            # Skip very small images
            if image.width < 100 or image.height < 100:
                return candidates
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize if too large (for performance)
            max_size = 1500
            if image.width > max_size or image.height > max_size:
                image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            # Convert to numpy array for OCR
            img_array = np.array(image)
            
            # Perform OCR
            results = self.easyocr_reader.readtext(img_array)
            
            # Process OCR results
            for (bbox, text, confidence) in results:
                if confidence > 0.6:  # Higher threshold for images
                    text_clean = text.strip()
                    
                    # Check if it could be a menu item
                    if self.is_potential_menu_item(text_clean):
                        candidate = MenuItemCandidate(
                            name=text_clean,
                            confidence=confidence * 0.9,  # Slight penalty for OCR
                            source="ocr_image",
                            category=self.categorize_food_item(text_clean)
                        )
                        candidates.append(candidate)
                    
                    # Check if it contains a price
                    elif any(re.search(pattern, text_clean) for pattern in self.price_patterns):
                        # Look for nearby text that might be a menu item
                        # This is a simplified approach - in practice, you'd analyze spatial relationships
                        pass
            
            logger.debug(f"OCR processed image from {source_url}: {len(candidates)} candidates")
            
        except Exception as e:
            logger.debug(f"OCR processing failed for {source_url}: {e}")
        
        return candidates
    
    def extract_with_modern_selectors(self, page: Page) -> List[MenuItemCandidate]:
        """Extract using modern CSS selectors and frameworks"""
        candidates = []
        
        # Modern framework selectors
        modern_selectors = [
            # React/Vue component selectors
            '[data-testid*="menu-item"]',
            '[data-testid*="dish"]',
            '[data-testid*="food-item"]',
            '[data-cy*="menu"]',
            '[data-qa*="menu"]',
            
            # Material UI / Ant Design patterns
            '.MuiCard-root:has-text("$")',
            '.ant-card:has-text("$")',
            '.chakra-ui-card:has-text("$")',
            
            # Common CSS class patterns
            '[class*="MenuItem"]',
            '[class*="FoodItem"]',
            '[class*="DishCard"]',
            '[class*="menu-card"]',
            '[class*="food-card"]',
            
            # Grid and flex layouts
            '.menu-grid > div',
            '.food-grid > div',
            '.menu-list > li',
            '.dish-list > li',
            
            # Price-based selectors
            '*:has-text("$"):not(script):not(style)',
            
            # Semantic HTML
            'article:has-text("$")',
            'section[class*="menu"] > div',
            'section[class*="food"] > div'
        ]
        
        for selector in modern_selectors:
            try:
                elements = page.query_selector_all(selector)
                for element in elements[:10]:  # Limit per selector
                    text = element.inner_text().strip()
                    
                    # Skip if too long (likely not a menu item)
                    if len(text) > 200:
                        continue
                    
                    # Look for potential menu items
                    lines = text.split('\n')
                    for line in lines:
                        line = line.strip()
                        if line and self.is_potential_menu_item(line):
                            # Extract price if present
                            price = None
                            for pattern in self.price_patterns:
                                price_match = re.search(pattern, text)
                                if price_match:
                                    price = price_match.group()
                                    break
                            
                            candidate = MenuItemCandidate(
                                name=line,
                                price=price,
                                confidence=0.7,
                                source="modern_css",
                                category=self.categorize_food_item(line)
                            )
                            candidates.append(candidate)
                            break  # Only take first valid item per element
                        
            except Exception as e:
                logger.debug(f"Modern selector {selector} failed: {e}")
                continue
        
        logger.info(f"🎯 Modern CSS extraction found {len(candidates)} items")
        return candidates
    
    def categorize_food_item(self, item_name: str) -> str:
        """Enhanced categorization with better matching"""
        if not item_name:
            return "other"
        
        item_lower = item_name.lower()
        
        # Direct keyword matching
        for category, keywords in self.food_categories.items():
            if any(keyword in item_lower for keyword in keywords):
                return category
        
        # Pattern-based categorization
        if re.search(r'\b(grilled|fried|baked|roasted)\b', item_lower):
            if any(meat in item_lower for meat in ['chicken', 'beef', 'pork', 'lamb']):
                return "meat"
            elif any(seafood in item_lower for seafood in ['fish', 'salmon', 'tuna']):
                return "seafood"
        
        # Price-based hints
        if '$' in item_name:
            # Higher prices often indicate mains
            price_match = re.search(r'\$(\d+)', item_name)
            if price_match and int(price_match.group(1)) > 15:
                return "mains"
        
        return "other"
    
    def is_potential_menu_item(self, text: str) -> bool:
        """Enhanced menu item detection with better filtering"""
        if not text or len(text.strip()) < 2:
            return False
        
        text_clean = text.strip()
        text_lower = text_clean.lower()
        
        # Length checks
        if len(text_clean) > 100:  # Too long
            return False
        if len(text_clean.split()) > 8:  # Too many words
            return False
        
        # Exclude obvious non-food items (enhanced)
        excluded_patterns = [
            r'^\d+$',  # Just numbers
            r'^[a-z]$',  # Single letters
            r'^\$\d+\.?\d*$',  # Just prices
            r'copyright|privacy|terms|contact|address|phone|hours|location|directions',
            r'follow us|social media|newsletter|subscribe|website|email|login|register',
            r'^(and|or|the|a|an|in|on|at|to|for|with|by|of|from|about)$',
            r'^(monday|tuesday|wednesday|thursday|friday|saturday|sunday)$',
            r'^(january|february|march|april|may|june|july|august|september|october|november|december)$',
            r'\b(reviews?|photos?|rating|stars?)\b',
            r'\b(delivery|pickup|takeout|order online)\b$',  # Unless part of item name
            r'^(open|closed|hours?|am|pm)\b',
            r'\b(yelp|google|facebook|instagram|twitter)\b'
        ]
        
        for pattern in excluded_patterns:
            if re.search(pattern, text_lower):
                return False
        
        # Positive indicators (enhanced)
        positive_indicators = [
            # Food keywords
            r'\b(soup|salad|sandwich|burger|pizza|pasta|chicken|beef|fish|salmon|shrimp)\b',
            r'\b(appetizer|entree|dessert|special|fresh|organic|homemade)\b',
            r'\b(grilled|fried|baked|roasted|steamed|sauteed|braised)\b',
            r'\b(sauce|cream|butter|cheese|wine|beer|coffee|tea)\b',
            
            # Dish patterns
            r'\bwith\s+\w+',  # "Chicken with rice"
            r'\bin\s+\w+\s+(sauce|broth)',  # "Fish in garlic sauce"
            r'\band\s+\w+',  # "Steak and potatoes"
            
            # Price indicators
            r'\$\d+',  # Contains price
            
            # Capitalization patterns (proper nouns often indicate dishes)
            r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*$'  # Title Case
        ]
        
        for pattern in positive_indicators:
            if re.search(pattern, text_clean):
                return True
        
        # Check for food-related words
        food_words = [
            'soup', 'salad', 'sandwich', 'burger', 'pizza', 'pasta', 'rice', 'noodles',
            'chicken', 'beef', 'pork', 'lamb', 'fish', 'salmon', 'tuna', 'shrimp',
            'cheese', 'bread', 'sauce', 'cream', 'butter', 'wine', 'beer', 'coffee',
            'cake', 'pie', 'ice', 'chocolate', 'vanilla', 'fruit', 'vegetable'
        ]
        
        if any(word in text_lower for word in food_words):
            return True
        
        # If it has proper capitalization and reasonable length, might be a dish name
        words = text_clean.split()
        if 2 <= len(words) <= 5 and all(word[0].isupper() for word in words if word):
            return True
        
        return False
    
    def merge_and_deduplicate_candidates(self, all_candidates: List[MenuItemCandidate]) -> List[Dict[str, Any]]:
        """Enhanced merging with better similarity detection"""
        if not all_candidates:
            return []
        
        # Group similar items with enhanced similarity
        grouped = {}
        
        for candidate in all_candidates:
            # Create multiple keys for grouping
            name_clean = re.sub(r'[^a-zA-Z0-9\s]', '', candidate.name.lower()).strip()
            name_normalized = ' '.join(name_clean.split())
            
            # Also try without common words
            name_core = ' '.join([word for word in name_normalized.split() 
                                if word not in ['the', 'a', 'an', 'with', 'and', 'or']])
            
            # Use the core name as key, fallback to normalized
            key = name_core if name_core else name_normalized
            
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(candidate)
        
        # Merge grouped candidates
        final_items = []
        
        for key, candidates in grouped.items():
            if not candidates or not key:
                continue
            
            # Sort by confidence and source priority
            source_priority = {'structured_data': 4, 'modern_css': 3, 'enhanced_css': 2, 'ocr_image': 1, 'review_mining': 0}
            candidates.sort(key=lambda x: (x.confidence, source_priority.get(x.source, 0)), reverse=True)
            
            best = candidates[0]
            
            # Merge information from other candidates
            descriptions = [c.description for c in candidates if c.description]
            prices = [c.price for c in candidates if c.price]
            sources = list(set(c.source for c in candidates))
            categories = [c.category for c in candidates if c.category and c.category != "other"]
            
            # Create final item
            item = {
                'name': best.name,
                'description': descriptions[0] if descriptions else best.description,
                'price': prices[0] if prices else best.price,
                'confidence': min(1.0, best.confidence + 0.1 * (len(candidates) - 1)),  # Boost for multiple sources
                'sources': sources,
                'category': categories[0] if categories else best.category,
                'allergens': list(set(sum([c.allergens for c in candidates], [])))
            }
            
            final_items.append(item)
        
        # Sort by confidence
        final_items.sort(key=lambda x: x['confidence'], reverse=True)
        
        return final_items
    
    def improved_menu_detection(self, page: Page, url: str) -> Dict[str, Any]:
        """Improved menu detection with navigation and enhanced extraction"""
        logger.info(f"🔍 Improved menu detection for: {url}")
        
        all_candidates = []
        
        try:
            # Navigate to the page
            page.goto(url, wait_until='networkidle', timeout=30000)
            page.wait_for_timeout(2000)
            
            # Try to find and navigate to menu page
            menu_page_found = self.find_menu_page(page)
            
            # Strategy 1: Modern CSS selectors
            modern_candidates = self.extract_with_modern_selectors(page)
            all_candidates.extend(modern_candidates)
            
            # Strategy 2: Enhanced image OCR
            image_candidates = self.extract_menu_from_images_enhanced(page)
            all_candidates.extend(image_candidates)
            
            # Strategy 3: Enhanced review mining (from previous implementation)
            # This would be imported from the advanced scraper
            
            # Merge and deduplicate
            final_items = self.merge_and_deduplicate_candidates(all_candidates)
            
            # Filter by confidence threshold
            high_confidence_items = [item for item in final_items if item['confidence'] > 0.5]
            
            success = len(high_confidence_items) > 0
            ocr_used = any('ocr' in item.get('sources', []) for item in high_confidence_items)
            
            result = {
                'menu_items': high_confidence_items,
                'total_items': len(high_confidence_items),
                'scraping_success': success,
                'ocr_used': ocr_used,
                'menu_page_found': menu_page_found,
                'source': 'improved_scraping',
                'strategies_used': len([c for c in [modern_candidates, image_candidates] if c]),
                'raw_candidates': len(all_candidates)
            }
            
            if success:
                logger.info(f"✅ Success! Found {len(high_confidence_items)} high-confidence items")
            else:
                logger.info(f"❌ No high-confidence menu items found")
            
            return result
            
        except Exception as e:
            logger.error(f"Improved menu detection failed: {e}")
            return {
                'menu_items': [],
                'total_items': 0,
                'scraping_success': False,
                'ocr_used': False,
                'menu_page_found': False,
                'source': 'improved_scraping',
                'error': str(e)
            }

# Example usage
if __name__ == "__main__":
    scraper = ImprovedMenuScraper()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Test URL
        test_url = "https://www.yelp.com/biz/some-restaurant"
        
        try:
            result = scraper.improved_menu_detection(page, test_url)
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(f"Test failed: {e}")
        finally:
            browser.close()