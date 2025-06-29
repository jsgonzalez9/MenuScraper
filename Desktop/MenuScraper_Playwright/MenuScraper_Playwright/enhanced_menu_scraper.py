#!/usr/bin/env python3
"""
Enhanced Menu Scraper - Phase 1 Implementation
Targets 25-30% success rate improvement through enhanced detection and multi-source scraping
"""

import json
import time
import re
from datetime import datetime
import os
from typing import Dict, List, Any, Optional
import requests
from playwright.sync_api import sync_playwright
from urllib.parse import urljoin, urlparse, quote
import easyocr
import cv2
import numpy as np
from PIL import Image
import io
import base64

class EnhancedMenuScraper:
    def __init__(self):
        self.easyocr_reader = None
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def get_easyocr_reader(self):
        """Initialize EasyOCR reader if not already done"""
        if self.easyocr_reader is None:
            try:
                self.easyocr_reader = easyocr.Reader(['en'])
                print("✅ EasyOCR initialized successfully")
            except Exception as e:
                print(f"❌ EasyOCR initialization failed: {e}")
        return self.easyocr_reader
    
    def find_restaurant_website(self, restaurant_name: str, location: str) -> Optional[str]:
        """Find restaurant's official website using Google search"""
        try:
            # Create search query
            query = f"{restaurant_name} {location} restaurant official website"
            search_url = f"https://www.google.com/search?q={quote(query)}"
            
            # Note: In production, you'd want to use Google Custom Search API
            # For now, we'll return None and rely on other methods
            return None
        except Exception as e:
            print(f"Website search failed: {e}")
            return None
    
    def enhanced_menu_detection(self, page, restaurant_url: str) -> Dict[str, Any]:
        """Enhanced menu detection with multiple strategies"""
        menu_data = {
            'menu_items': [],
            'menu_url': None,
            'total_items': 0,
            'scraping_success': False,
            'ocr_used': False,
            'source': 'enhanced_scraping'
        }
        
        try:
            print(f"    🔍 Enhanced menu detection for: {restaurant_url}")
            
            # Navigate to restaurant page
            page.goto(restaurant_url, timeout=30000)
            page.wait_for_load_state('networkidle', timeout=15000)
            
            # Strategy 1: Enhanced menu link detection
            menu_url = self.find_menu_page(page, restaurant_url)
            if menu_url:
                menu_data['menu_url'] = menu_url
                page.goto(menu_url, timeout=20000)
                page.wait_for_load_state('networkidle', timeout=10000)
            
            # Strategy 2: Dynamic content loading
            self.trigger_dynamic_content(page)
            
            # Strategy 3: Enhanced menu item extraction
            menu_items = self.extract_menu_items_enhanced(page)
            
            # Strategy 4: OCR fallback for images
            if len(menu_items) == 0:
                print("    📸 Attempting OCR extraction...")
                ocr_items = self.extract_menu_from_images(page)
                if ocr_items:
                    menu_items.extend(ocr_items)
                    menu_data['ocr_used'] = True
            
            # Strategy 5: Review mining
            if len(menu_items) == 0:
                print("    💬 Mining reviews for menu items...")
                review_items = self.extract_menu_from_reviews(page)
                menu_items.extend(review_items)
            
            menu_data['menu_items'] = menu_items
            menu_data['total_items'] = len(menu_items)
            menu_data['scraping_success'] = len(menu_items) > 0
            
            if menu_data['scraping_success']:
                print(f"    ✅ Successfully extracted {len(menu_items)} menu items")
            else:
                print(f"    ❌ No menu items found")
            
            return menu_data
            
        except Exception as e:
            print(f"    ❌ Enhanced menu detection failed: {str(e)}")
            menu_data['error'] = str(e)
            return menu_data
    
    def find_menu_page(self, page, base_url: str) -> Optional[str]:
        """Enhanced menu page detection"""
        menu_selectors = [
            # Standard menu links
            'a[href*="menu"]',
            'a:has-text("Menu")',
            'a:has-text("View Menu")',
            'a:has-text("Our Menu")',
            'a:has-text("Food Menu")',
            'button:has-text("Menu")',
            
            # Data attributes
            '[data-test*="menu"]',
            '[data-menu]',
            '[data-testid*="menu"]',
            
            # Class-based detection
            '.menu-link',
            '.view-menu',
            '.menu-button',
            
            # Yelp-specific
            'a[href*="/menu/"]',
            '.menu-tab',
            '.biz-menu-link'
        ]
        
        for selector in menu_selectors:
            try:
                menu_link = page.locator(selector).first
                if menu_link.is_visible(timeout=2000):
                    menu_url = menu_link.get_attribute('href')
                    if menu_url:
                        full_url = urljoin(base_url, menu_url)
                        print(f"    📋 Found menu link: {full_url}")
                        return full_url
            except:
                continue
        
        return None
    
    def trigger_dynamic_content(self, page):
        """Trigger dynamic content loading"""
        try:
            # Wait for page to be fully loaded
            page.wait_for_function("document.readyState === 'complete'", timeout=5000)
            
            # Click menu triggers
            menu_triggers = [
                'button:has-text("Menu")',
                'button:has-text("View Menu")',
                '.menu-toggle',
                '[data-menu-trigger]',
                '.menu-tab'
            ]
            
            for trigger in menu_triggers:
                try:
                    if page.locator(trigger).is_visible(timeout=1000):
                        page.click(trigger)
                        page.wait_for_timeout(2000)
                        break
                except:
                    continue
            
            # Scroll to load lazy content
            page.evaluate("""
                window.scrollTo(0, document.body.scrollHeight);
                setTimeout(() => window.scrollTo(0, 0), 1000);
            """)
            page.wait_for_timeout(2000)
            
        except Exception as e:
            print(f"    ⚠️ Dynamic content loading failed: {e}")
    
    def extract_menu_items_enhanced(self, page) -> List[Dict[str, Any]]:
        """Enhanced menu item extraction with multiple strategies"""
        menu_items = []
        
        # Strategy 1: Enhanced structured selectors
        structured_selectors = [
            # Standard menu item patterns
            '[class*="menu-item"]',
            '[data-test*="menu-item"]',
            '.menu-item',
            '.dish',
            '.food-item',
            
            # Food delivery patterns
            '[class*="dish"]',
            '[class*="food-item"]',
            '.item-card',
            '.product-card',
            '.menu-product',
            
            # Restaurant-specific patterns
            '.menu-section-item',
            '.restaurant-menu-item',
            '.food-card',
            
            # Yelp-specific
            '.menu-item-details',
            '.arrange-unit__09f24__rqHTg',
            '.menuItem__09f24__mp84j'
        ]
        
        for selector in structured_selectors:
            try:
                items = page.locator(selector).all()
                if len(items) > 0:
                    print(f"    📝 Found {len(items)} items with selector: {selector}")
                    for item in items[:20]:  # Limit to 20 items
                        try:
                            item_data = self.parse_menu_item(item)
                            if item_data:
                                menu_items.append(item_data)
                        except:
                            continue
                    if menu_items:
                        break
            except:
                continue
        
        # Strategy 2: Enhanced price-based extraction
        if len(menu_items) == 0:
            menu_items = self.extract_by_price_patterns(page)
        
        # Strategy 3: Table-based extraction
        if len(menu_items) == 0:
            menu_items = self.extract_from_tables(page)
        
        return menu_items
    
    def parse_menu_item(self, item_element) -> Optional[Dict[str, Any]]:
        """Parse individual menu item with enhanced extraction"""
        try:
            item_text = item_element.inner_text().strip()
            if len(item_text) < 5:
                return None
            
            # Enhanced price extraction
            price_patterns = [
                r'\$([0-9]+(?:\.[0-9]{2})?)',  # $12.99
                r'([0-9]+(?:\.[0-9]{2})?)\s*\$',  # 12.99 $
                r'\$\s*([0-9]+(?:\.[0-9]{2})?)',  # $ 12.99
                r'USD\s*([0-9]+(?:\.[0-9]{2})?)',  # USD 12.99
                r'([0-9]+)\s*dollars?',  # 12 dollars
            ]
            
            price = None
            for pattern in price_patterns:
                price_match = re.search(pattern, item_text, re.IGNORECASE)
                if price_match:
                    price = f"${price_match.group(1)}"
                    break
            
            # Clean description
            description = item_text
            for pattern in price_patterns:
                description = re.sub(pattern, '', description, flags=re.IGNORECASE)
            description = description.strip()
            
            # Extract name (first line or sentence)
            name_parts = description.split('\n')
            name = name_parts[0].strip() if name_parts else description
            name = name.split('.')[0].strip()[:60]
            
            # Skip if not food-related
            if not self.is_food_related(description):
                return None
            
            # Extract allergens
            allergens = self.extract_allergen_info(description)
            
            return {
                'name': name,
                'description': description,
                'price': price,
                'potential_allergens': allergens,
                'source': 'structured_extraction',
                'confidence': 'high' if price else 'medium'
            }
            
        except Exception as e:
            return None
    
    def extract_by_price_patterns(self, page) -> List[Dict[str, Any]]:
        """Enhanced price-based menu extraction"""
        menu_items = []
        
        try:
            page_text = page.inner_text('body')
            
            # Enhanced price patterns with food context
            price_patterns = [
                r'([A-Z][^$\n]{10,80}(?:chicken|beef|fish|pasta|salad|soup|pizza|burger|sandwich|steak|seafood|vegetarian|dessert|appetizer|entree|special)[^$\n]{0,30})\s*\$([0-9]+(?:\.[0-9]{2})?)',
                r'([^$\n]{15,100})\s*\$([0-9]+(?:\.[0-9]{2})?)',
                r'([A-Z][^\n]{20,80})\s*-\s*\$([0-9]+(?:\.[0-9]{2})?)',
                r'([A-Z][^\n]{15,60})\s*\.{2,}\s*\$([0-9]+(?:\.[0-9]{2})?)',
            ]
            
            for pattern in price_patterns:
                matches = re.findall(pattern, page_text, re.MULTILINE | re.IGNORECASE)
                for description, price in matches[:15]:
                    description = description.strip()
                    
                    if (len(description) > 10 and 
                        self.is_food_related(description) and
                        not self.is_excluded_content(description)):
                        
                        allergens = self.extract_allergen_info(description)
                        
                        menu_items.append({
                            'name': description.split('.')[0].strip()[:60],
                            'description': description,
                            'price': f'${price}',
                            'potential_allergens': allergens,
                            'source': 'price_pattern_extraction',
                            'confidence': 'high'
                        })
                
                if len(menu_items) > 0:
                    break
            
            print(f"    💰 Price-based extraction found {len(menu_items)} items")
            return menu_items
            
        except Exception as e:
            print(f"    ❌ Price-based extraction failed: {e}")
            return []
    
    def extract_from_tables(self, page) -> List[Dict[str, Any]]:
        """Extract menu items from table structures"""
        menu_items = []
        
        try:
            # Look for table-based menus
            table_selectors = ['table', '.menu-table', '[class*="table"]']
            
            for selector in table_selectors:
                tables = page.locator(selector).all()
                for table in tables:
                    rows = table.locator('tr').all()
                    for row in rows:
                        try:
                            row_text = row.inner_text().strip()
                            if len(row_text) > 10 and '$' in row_text:
                                # Parse table row
                                cells = row.locator('td, th').all()
                                if len(cells) >= 2:
                                    name_cell = cells[0].inner_text().strip()
                                    price_cell = cells[-1].inner_text().strip()
                                    
                                    if self.is_food_related(name_cell) and '$' in price_cell:
                                        price_match = re.search(r'\$([0-9]+(?:\.[0-9]{2})?)', price_cell)
                                        price = f"${price_match.group(1)}" if price_match else None
                                        
                                        allergens = self.extract_allergen_info(name_cell)
                                        
                                        menu_items.append({
                                            'name': name_cell[:60],
                                            'description': name_cell,
                                            'price': price,
                                            'potential_allergens': allergens,
                                            'source': 'table_extraction',
                                            'confidence': 'medium'
                                        })
                        except:
                            continue
                
                if menu_items:
                    break
            
            print(f"    📊 Table extraction found {len(menu_items)} items")
            return menu_items[:15]  # Limit results
            
        except Exception as e:
            print(f"    ❌ Table extraction failed: {e}")
            return []
    
    def extract_menu_from_images(self, page) -> List[Dict[str, Any]]:
        """Extract menu items from images using OCR"""
        menu_items = []
        
        try:
            reader = self.get_easyocr_reader()
            if not reader:
                return []
            
            # Enhanced image selectors
            image_selectors = [
                'img[src*="menu"]',
                'img[alt*="menu"]',
                'img[class*="menu"]',
                '.menu-image img',
                '[data-test*="menu"] img',
                'a[href*="menu"] img',
                '.photo-box img',
                '.biz-photo img'
            ]
            
            for selector in image_selectors:
                try:
                    images = page.locator(selector).all()
                    for img in images[:3]:  # Limit to 3 images
                        try:
                            # Get image source
                            img_src = img.get_attribute('src')
                            if img_src and ('menu' in img_src.lower() or 'food' in img_src.lower()):
                                # Download and process image
                                ocr_text = self.process_image_ocr(img_src)
                                if ocr_text:
                                    parsed_items = self.parse_menu_from_ocr_text(ocr_text)
                                    menu_items.extend(parsed_items)
                        except:
                            continue
                    
                    if menu_items:
                        break
                except:
                    continue
            
            print(f"    📸 OCR extraction found {len(menu_items)} items")
            return menu_items[:10]  # Limit results
            
        except Exception as e:
            print(f"    ❌ OCR extraction failed: {e}")
            return []
    
    def process_image_ocr(self, img_src: str) -> str:
        """Process image with OCR"""
        try:
            # Download image
            response = self.session.get(img_src, timeout=10)
            if response.status_code == 200:
                # Convert to PIL Image
                image = Image.open(io.BytesIO(response.content))
                
                # Convert to numpy array for EasyOCR
                img_array = np.array(image)
                
                # Extract text
                results = self.easyocr_reader.readtext(img_array)
                
                # Combine text
                text_lines = [result[1] for result in results if result[2] > 0.5]
                return '\n'.join(text_lines)
            
        except Exception as e:
            print(f"    ⚠️ Image OCR failed: {e}")
        
        return ""
    
    def parse_menu_from_ocr_text(self, ocr_text: str) -> List[Dict[str, Any]]:
        """Parse menu items from OCR text"""
        menu_items = []
        
        try:
            lines = ocr_text.split('\n')
            
            for i, line in enumerate(lines):
                line = line.strip()
                if len(line) < 5:
                    continue
                
                # Look for price patterns
                price_match = re.search(r'\$([0-9]+(?:\.[0-9]{2})?)', line)
                if price_match:
                    price = f"${price_match.group(1)}"
                    description = re.sub(r'\$[0-9]+(?:\.[0-9]{2})?', '', line).strip()
                    
                    if self.is_food_related(description):
                        allergens = self.extract_allergen_info(description)
                        
                        menu_items.append({
                            'name': description[:60],
                            'description': description,
                            'price': price,
                            'potential_allergens': allergens,
                            'source': 'ocr_extraction',
                            'confidence': 'medium'
                        })
                
                # Look for food keywords without prices
                elif self.is_food_related(line) and len(line) > 10:
                    # Check next line for price
                    price = None
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        price_match = re.search(r'\$([0-9]+(?:\.[0-9]{2})?)', next_line)
                        if price_match:
                            price = f"${price_match.group(1)}"
                    
                    allergens = self.extract_allergen_info(line)
                    
                    menu_items.append({
                        'name': line[:60],
                        'description': line,
                        'price': price,
                        'potential_allergens': allergens,
                        'source': 'ocr_extraction',
                        'confidence': 'low' if not price else 'medium'
                    })
            
            return menu_items[:8]  # Limit results
            
        except Exception as e:
            print(f"    ❌ OCR text parsing failed: {e}")
            return []
    
    def extract_menu_from_reviews(self, page) -> List[Dict[str, Any]]:
        """Extract menu items mentioned in reviews"""
        menu_items = []
        
        try:
            # Look for review sections
            review_selectors = [
                '.review-content',
                '.review-text',
                '[class*="review"]',
                '.user-review',
                '.comment-text'
            ]
            
            for selector in review_selectors:
                try:
                    reviews = page.locator(selector).all()
                    for review in reviews[:5]:  # Limit to 5 reviews
                        review_text = review.inner_text().strip()
                        
                        # Extract food mentions
                        food_patterns = [
                            r'I ordered the ([^.!?\n]{5,40})',
                            r'The ([^.!?\n]{5,40}) was (?:delicious|amazing|great|good|excellent)',
                            r'Try the ([^.!?\n]{5,40})',
                            r'([A-Z][a-z]+ [A-Z][a-z]+) is (?:delicious|amazing|great|good)',
                            r'([A-Z][^.!?\n]{10,40}) \$([0-9]+)'
                        ]
                        
                        for pattern in food_patterns:
                            matches = re.findall(pattern, review_text, re.IGNORECASE)
                            for match in matches:
                                if isinstance(match, tuple):
                                    food_name = match[0].strip()
                                    price = f"${match[1]}" if len(match) > 1 else None
                                else:
                                    food_name = match.strip()
                                    price = None
                                
                                if (self.is_food_related(food_name) and 
                                    len(food_name) > 5 and 
                                    food_name not in [item['name'] for item in menu_items]):
                                    
                                    allergens = self.extract_allergen_info(food_name)
                                    
                                    menu_items.append({
                                        'name': food_name[:60],
                                        'description': food_name,
                                        'price': price,
                                        'potential_allergens': allergens,
                                        'source': 'review_mining',
                                        'confidence': 'low'
                                    })
                    
                    if menu_items:
                        break
                except:
                    continue
            
            print(f"    💬 Review mining found {len(menu_items)} items")
            return menu_items[:5]  # Limit results
            
        except Exception as e:
            print(f"    ❌ Review mining failed: {e}")
            return []
    
    def is_food_related(self, text: str) -> bool:
        """Check if text is food-related"""
        food_keywords = [
            'chicken', 'beef', 'fish', 'pasta', 'salad', 'soup', 'pizza', 'burger',
            'sandwich', 'steak', 'seafood', 'vegetarian', 'dessert', 'appetizer',
            'entree', 'special', 'grilled', 'fried', 'baked', 'roasted', 'sauteed',
            'served', 'with', 'sauce', 'cheese', 'bread', 'rice', 'noodles',
            'shrimp', 'lobster', 'crab', 'salmon', 'tuna', 'pork', 'lamb',
            'wings', 'ribs', 'tacos', 'burrito', 'quesadilla', 'nachos'
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in food_keywords)
    
    def is_excluded_content(self, text: str) -> bool:
        """Check if text should be excluded"""
        excluded_keywords = [
            'copyright', 'privacy', 'terms', 'contact', 'address', 'phone',
            'hours', 'location', 'directions', 'parking', 'website',
            'follow us', 'social media', 'newsletter', 'subscribe'
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in excluded_keywords)
    
    def extract_allergen_info(self, text: str) -> List[str]:
        """Extract allergen information from text"""
        allergens = []
        text_lower = text.lower()
        
        allergen_patterns = {
            'dairy': ['milk', 'cheese', 'butter', 'cream', 'yogurt', 'dairy'],
            'eggs': ['egg', 'eggs', 'mayonnaise'],
            'fish': ['fish', 'salmon', 'tuna', 'cod', 'halibut'],
            'shellfish': ['shrimp', 'lobster', 'crab', 'oyster', 'mussel', 'clam'],
            'tree_nuts': ['almond', 'walnut', 'pecan', 'cashew', 'pistachio'],
            'peanuts': ['peanut', 'peanuts'],
            'wheat': ['wheat', 'flour', 'bread', 'pasta', 'noodles'],
            'soy': ['soy', 'tofu', 'soybean']
        }
        
        for allergen, keywords in allergen_patterns.items():
            if any(keyword in text_lower for keyword in keywords):
                allergens.append(allergen)
        
        return allergens

# Example usage
if __name__ == "__main__":
    scraper = EnhancedMenuScraper()
    
    # Test with a sample restaurant URL
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Example restaurant URL (replace with actual URL)
        test_url = "https://www.yelp.com/biz/some-restaurant"
        
        try:
            result = scraper.enhanced_menu_detection(page, test_url)
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(f"Test failed: {e}")
        finally:
            browser.close()