#!/usr/bin/env python3
"""
Practical ML-Inspired Menu Scraper
Combines successful scraping techniques with ML-inspired allergen detection
Focuses on reliability and practical implementation without heavy ML dependencies
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

class PracticalMLScraper:
    """Practical ML-inspired menu scraper with enhanced allergen detection"""
    
    def __init__(self, headless: bool = True, timeout: int = 30000):
        self.headless = headless
        self.timeout = timeout
        self.browser = None
        self.context = None
        
        # ML-inspired allergen detection patterns
        self.allergen_patterns = {
            'gluten': [
                r'\b(?:gluten|wheat|flour|bread|pasta|noodle|cereal|barley|rye|oat)\b',
                r'\b(?:contains?\s+gluten|gluten[\s-]?free|wheat[\s-]?free)\b'
            ],
            'dairy': [
                r'\b(?:milk|cheese|cream|butter|yogurt|dairy|lactose|casein|whey)\b',
                r'\b(?:contains?\s+dairy|dairy[\s-]?free|lactose[\s-]?free)\b'
            ],
            'nuts': [
                r'\b(?:nuts?|almond|walnut|pecan|cashew|pistachio|hazelnut|macadamia)\b',
                r'\b(?:peanut|tree\s+nuts?|nut[\s-]?free|contains?\s+nuts?)\b'
            ],
            'eggs': [
                r'\b(?:eggs?|egg\s+white|egg\s+yolk|mayonnaise|mayo)\b',
                r'\b(?:contains?\s+eggs?|egg[\s-]?free)\b'
            ],
            'soy': [
                r'\b(?:soy|soya|tofu|tempeh|miso|soy\s+sauce|edamame)\b',
                r'\b(?:contains?\s+soy|soy[\s-]?free)\b'
            ],
            'fish': [
                r'\b(?:fish|salmon|tuna|cod|halibut|anchovy|sardine)\b',
                r'\b(?:contains?\s+fish|fish[\s-]?free)\b'
            ],
            'shellfish': [
                r'\b(?:shellfish|shrimp|crab|lobster|oyster|mussel|clam|scallop)\b',
                r'\b(?:contains?\s+shellfish|shellfish[\s-]?free)\b'
            ],
            'sesame': [
                r'\b(?:sesame|tahini|sesame\s+oil|sesame\s+seed)\b',
                r'\b(?:contains?\s+sesame|sesame[\s-]?free)\b'
            ]
        }
        
        # Dietary tag patterns (ML-inspired classification)
        self.dietary_patterns = {
            'vegetarian': r'\b(?:vegetarian|veggie|plant[\s-]?based)\b',
            'vegan': r'\b(?:vegan|plant[\s-]?based|dairy[\s-]?free)\b',
            'gluten_free': r'\b(?:gluten[\s-]?free|gf|celiac[\s-]?friendly)\b',
            'keto': r'\b(?:keto|ketogenic|low[\s-]?carb)\b',
            'paleo': r'\b(?:paleo|paleolithic)\b',
            'organic': r'\b(?:organic|natural|farm[\s-]?fresh)\b',
            'spicy': r'\b(?:spicy|hot|jalapeño|habanero|sriracha|chili)\b'
        }
        
        # Enhanced CSS selectors (ML-inspired feature extraction)
        self.menu_selectors = [
            # Common menu item patterns
            '[class*="menu"] [class*="item"]',
            '[class*="food"] [class*="item"]',
            '[class*="dish"]',
            '[class*="product"]',
            '.menu-item, .food-item, .dish-item',
            '[data-testid*="menu"], [data-testid*="item"]',
            
            # Price-based detection
            '*:has-text("$") + *, *:has-text("$")',
            
            # List-based patterns
            'ul li, ol li',
            '.list-item, .item',
            
            # Table-based patterns
            'table tr td, table tr th',
            
            # Generic content patterns
            'div:has-text("$"), span:has-text("$")',
            'p:has-text("$")'
        ]
        
        # Smart navigation patterns
        self.menu_link_patterns = [
            r'menu',
            r'food',
            r'order',
            r'dine',
            r'eat',
            r'cuisine'
        ]
    
    async def setup_browser(self) -> bool:
        """Setup browser with enhanced stealth features"""
        try:
            playwright = await async_playwright().start()
            
            # Launch browser with stealth settings
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
            
            # Create context with realistic settings
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='en-US',
                timezone_id='America/New_York'
            )
            
            return True
            
        except Exception as e:
            print(f"❌ Browser setup failed: {e}")
            return False
    
    async def smart_navigate(self, page: Page, url: str) -> bool:
        """Smart navigation with menu detection"""
        try:
            # Navigate to main page
            await page.goto(url, wait_until='domcontentloaded', timeout=self.timeout)
            await asyncio.sleep(2)
            
            # Check if we're already on a menu page
            page_content = await page.content()
            if self._has_menu_content(page_content):
                return True
            
            # Look for menu links
            menu_links = await self._find_menu_links(page)
            
            if menu_links:
                # Try the most promising menu link
                for link in menu_links[:3]:  # Try top 3 candidates
                    try:
                        await link.click(timeout=5000)
                        await page.wait_for_load_state('domcontentloaded', timeout=10000)
                        await asyncio.sleep(2)
                        
                        # Check if we found menu content
                        new_content = await page.content()
                        if self._has_menu_content(new_content):
                            return True
                            
                    except Exception:
                        continue
            
            # If no menu links worked, stay on current page
            return True
            
        except Exception as e:
            print(f"Navigation error: {e}")
            return False
    
    def _has_menu_content(self, content: str) -> bool:
        """ML-inspired content analysis for menu detection"""
        content_lower = content.lower()
        
        # Count menu indicators
        menu_indicators = [
            'menu', 'food', 'dish', 'appetizer', 'entree', 'dessert',
            'price', '$', 'order', 'cuisine', 'restaurant'
        ]
        
        indicator_count = sum(1 for indicator in menu_indicators if indicator in content_lower)
        
        # Price pattern detection
        price_patterns = len(re.findall(r'\$\d+\.\d{2}|\$\d+', content))
        
        # ML-inspired scoring
        menu_score = indicator_count + (price_patterns * 2)
        
        return menu_score >= 5
    
    async def _find_menu_links(self, page: Page) -> List:
        """Find potential menu links using ML-inspired pattern matching"""
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
                    
                    # ML-inspired relevance scoring
                    relevance_score = 0
                    
                    # Text-based scoring
                    for pattern in self.menu_link_patterns:
                        if pattern in text_lower:
                            relevance_score += 3
                        if pattern in href_lower:
                            relevance_score += 2
                    
                    # Exact matches get higher scores
                    if text_lower in ['menu', 'food menu', 'our menu']:
                        relevance_score += 5
                    
                    # Add to candidates if relevant
                    if relevance_score >= 2:
                        menu_links.append((link, relevance_score, text))
                        
                except Exception:
                    continue
            
            # Sort by relevance score
            menu_links.sort(key=lambda x: x[1], reverse=True)
            return [link[0] for link in menu_links]
            
        except Exception:
            return []
    
    def _extract_with_ml_analysis(self, content: str) -> List[Dict[str, Any]]:
        """ML-inspired content extraction and analysis"""
        items = []
        
        # Split content into potential menu items
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if len(line) < 5 or len(line) > 200:
                continue
            
            # ML-inspired item detection
            item_score = self._calculate_item_score(line)
            
            if item_score >= 3:
                item = self._analyze_menu_item(line)
                if item:
                    items.append(item)
        
        return items
    
    def _calculate_item_score(self, text: str) -> int:
        """ML-inspired scoring for menu item likelihood"""
        score = 0
        text_lower = text.lower()
        
        # Price indicators
        if re.search(r'\$\d+', text):
            score += 4
        
        # Food-related keywords
        food_keywords = [
            'served', 'grilled', 'fried', 'baked', 'fresh', 'homemade',
            'sauce', 'cheese', 'chicken', 'beef', 'fish', 'pasta',
            'salad', 'soup', 'sandwich', 'burger', 'pizza'
        ]
        
        for keyword in food_keywords:
            if keyword in text_lower:
                score += 1
        
        # Length-based scoring
        if 10 <= len(text) <= 100:
            score += 1
        
        return score
    
    def _analyze_menu_item(self, text: str) -> Optional[Dict[str, Any]]:
        """Comprehensive ML-inspired menu item analysis"""
        # Extract price
        price_match = re.search(r'\$([\d,]+(?:\.\d{2})?)', text)
        price = price_match.group(1) if price_match else None
        
        # Clean item name (remove price)
        name = re.sub(r'\$[\d,]+(?:\.\d{2})?', '', text).strip()
        name = re.sub(r'\s+', ' ', name)  # Normalize whitespace
        
        if len(name) < 3:
            return None
        
        # ML-inspired allergen detection
        allergens = self._detect_allergens(text)
        
        # Dietary tag detection
        dietary_tags = self._detect_dietary_tags(text)
        
        # Risk assessment
        risk_level = self._assess_allergen_risk(allergens, text)
        
        # Confidence scoring
        confidence = self._calculate_confidence(text, price, allergens)
        
        return {
            'name': name,
            'price': price,
            'description': text if len(text) > len(name) + 10 else None,
            'allergens': allergens,
            'dietary_tags': dietary_tags,
            'allergen_risk_level': risk_level,
            'confidence_score': confidence,
            'category': self._classify_category(name)
        }
    
    def _detect_allergens(self, text: str) -> List[str]:
        """ML-inspired allergen detection"""
        detected = []
        text_lower = text.lower()
        
        for allergen, patterns in self.allergen_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    detected.append(allergen)
                    break
        
        return list(set(detected))  # Remove duplicates
    
    def _detect_dietary_tags(self, text: str) -> List[str]:
        """Detect dietary tags using pattern matching"""
        tags = []
        text_lower = text.lower()
        
        for tag, pattern in self.dietary_patterns.items():
            if re.search(pattern, text_lower, re.IGNORECASE):
                tags.append(tag)
        
        return tags
    
    def _assess_allergen_risk(self, allergens: List[str], text: str) -> str:
        """ML-inspired risk assessment"""
        if not allergens:
            return 'low'
        
        high_risk_allergens = ['nuts', 'shellfish', 'eggs']
        medium_risk_allergens = ['dairy', 'gluten', 'soy']
        
        if any(allergen in high_risk_allergens for allergen in allergens):
            return 'high'
        elif any(allergen in medium_risk_allergens for allergen in allergens):
            return 'medium'
        else:
            return 'low'
    
    def _calculate_confidence(self, text: str, price: str, allergens: List[str]) -> float:
        """ML-inspired confidence scoring"""
        confidence = 0.5  # Base confidence
        
        # Price presence increases confidence
        if price:
            confidence += 0.2
        
        # Allergen detection increases confidence
        if allergens:
            confidence += 0.1
        
        # Text quality assessment
        if 20 <= len(text) <= 150:
            confidence += 0.1
        
        # Food-related keywords
        food_indicators = ['served', 'with', 'fresh', 'grilled', 'fried']
        if any(indicator in text.lower() for indicator in food_indicators):
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _classify_category(self, name: str) -> str:
        """ML-inspired category classification"""
        name_lower = name.lower()
        
        categories = {
            'appetizer': ['appetizer', 'starter', 'app', 'wings', 'nachos', 'dip'],
            'salad': ['salad', 'greens', 'caesar', 'garden'],
            'soup': ['soup', 'bisque', 'chowder', 'broth'],
            'sandwich': ['sandwich', 'burger', 'wrap', 'panini', 'sub'],
            'pasta': ['pasta', 'spaghetti', 'linguine', 'ravioli', 'lasagna'],
            'pizza': ['pizza', 'pie'],
            'seafood': ['fish', 'salmon', 'shrimp', 'crab', 'lobster', 'scallop'],
            'meat': ['steak', 'beef', 'chicken', 'pork', 'lamb'],
            'dessert': ['dessert', 'cake', 'pie', 'ice cream', 'chocolate']
        }
        
        for category, keywords in categories.items():
            if any(keyword in name_lower for keyword in keywords):
                return category
        
        return 'other'
    
    async def extract_menu_items(self, url: str) -> Dict[str, Any]:
        """Main extraction method with ML-inspired analysis"""
        start_time = time.time()
        
        result = {
            'success': False,
            'total_items': 0,
            'items': [],
            'extraction_method': None,
            'processing_time': 0,
            'error': None,
            'ml_features': {
                'confidence_scores': [],
                'allergen_detections': {},
                'quality_assessment': 0,
                'extraction_strategies_used': []
            },
            'allergen_summary': {},
            'price_coverage': 0
        }
        
        try:
            # Create new page
            page = await self.context.new_page()
            
            # Smart navigation
            if not await self.smart_navigate(page, url):
                result['error'] = 'Smart navigation failed'
                return result
            
            # Try multiple extraction strategies
            items = []
            strategies_used = []
            
            # Strategy 1: Enhanced CSS selectors
            for selector in self.menu_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        strategy_items = await self._extract_from_elements(elements)
                        if strategy_items:
                            items.extend(strategy_items)
                            strategies_used.append('enhanced_css_selectors')
                            break
                except Exception:
                    continue
            
            # Strategy 2: ML-inspired text analysis
            if not items:
                try:
                    content = await page.content()
                    text_items = self._extract_with_ml_analysis(content)
                    if text_items:
                        items.extend(text_items)
                        strategies_used.append('ml_text_analysis')
                except Exception:
                    pass
            
            # Strategy 3: Structured data extraction
            if not items:
                try:
                    structured_items = await self._extract_structured_data(page)
                    if structured_items:
                        items.extend(structured_items)
                        strategies_used.append('structured_data_ml')
                except Exception:
                    pass
            
            await page.close()
            
            if items:
                # Process and analyze items
                processed_items = self._post_process_items(items)
                
                # Calculate metrics
                confidence_scores = [item.get('confidence_score', 0) for item in processed_items]
                allergen_summary = self._calculate_allergen_summary(processed_items)
                price_coverage = self._calculate_price_coverage(processed_items)
                quality_score = self._calculate_quality_score(processed_items)
                
                result.update({
                    'success': True,
                    'total_items': len(processed_items),
                    'items': processed_items,
                    'extraction_method': ', '.join(strategies_used),
                    'ml_features': {
                        'confidence_scores': confidence_scores,
                        'allergen_detections': allergen_summary,
                        'quality_assessment': quality_score,
                        'extraction_strategies_used': strategies_used
                    },
                    'allergen_summary': allergen_summary,
                    'price_coverage': price_coverage
                })
            else:
                result['error'] = 'No menu items found with any strategy'
            
        except Exception as e:
            result['error'] = f'Extraction failed: {str(e)}'
        
        finally:
            result['processing_time'] = round(time.time() - start_time, 2)
        
        return result
    
    async def _extract_from_elements(self, elements) -> List[Dict[str, Any]]:
        """Extract items from DOM elements"""
        items = []
        
        for element in elements[:50]:  # Limit to prevent overload
            try:
                text = await element.inner_text()
                if text and len(text.strip()) > 5:
                    item = self._analyze_menu_item(text.strip())
                    if item:
                        items.append(item)
            except Exception:
                continue
        
        return items
    
    async def _extract_structured_data(self, page: Page) -> List[Dict[str, Any]]:
        """Extract from structured data (JSON-LD, microdata)"""
        items = []
        
        try:
            # Look for JSON-LD structured data
            scripts = await page.query_selector_all('script[type="application/ld+json"]')
            
            for script in scripts:
                try:
                    content = await script.inner_text()
                    data = json.loads(content)
                    
                    # Extract menu items from structured data
                    structured_items = self._parse_structured_menu_data(data)
                    items.extend(structured_items)
                    
                except Exception:
                    continue
        
        except Exception:
            pass
        
        return items
    
    def _parse_structured_menu_data(self, data: Any) -> List[Dict[str, Any]]:
        """Parse structured data for menu items"""
        items = []
        
        if isinstance(data, dict):
            # Look for menu-related structured data
            if data.get('@type') in ['Menu', 'MenuItem', 'FoodEstablishment']:
                if 'hasMenuItem' in data:
                    for item_data in data['hasMenuItem']:
                        item = self._parse_menu_item_data(item_data)
                        if item:
                            items.append(item)
            
            # Recursively search nested data
            for value in data.values():
                items.extend(self._parse_structured_menu_data(value))
        
        elif isinstance(data, list):
            for item in data:
                items.extend(self._parse_structured_menu_data(item))
        
        return items
    
    def _parse_menu_item_data(self, item_data: Dict) -> Optional[Dict[str, Any]]:
        """Parse individual menu item from structured data"""
        try:
            name = item_data.get('name', '')
            description = item_data.get('description', '')
            
            # Extract price
            price = None
            if 'offers' in item_data:
                offers = item_data['offers']
                if isinstance(offers, list) and offers:
                    price = offers[0].get('price')
                elif isinstance(offers, dict):
                    price = offers.get('price')
            
            if name:
                full_text = f"{name} {description}".strip()
                return self._analyze_menu_item(full_text)
        
        except Exception:
            pass
        
        return None
    
    def _post_process_items(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Post-process and deduplicate items"""
        # Remove duplicates based on name similarity
        unique_items = []
        seen_names = set()
        
        for item in items:
            name = item.get('name', '').lower().strip()
            if name and name not in seen_names:
                seen_names.add(name)
                unique_items.append(item)
        
        return unique_items[:100]  # Limit to reasonable number
    
    def _calculate_allergen_summary(self, items: List[Dict[str, Any]]) -> Dict[str, int]:
        """Calculate allergen summary statistics"""
        summary = {}
        
        for item in items:
            allergens = item.get('allergens', [])
            for allergen in allergens:
                summary[allergen] = summary.get(allergen, 0) + 1
        
        return summary
    
    def _calculate_price_coverage(self, items: List[Dict[str, Any]]) -> float:
        """Calculate percentage of items with prices"""
        if not items:
            return 0
        
        items_with_prices = sum(1 for item in items if item.get('price'))
        return round((items_with_prices / len(items)) * 100, 1)
    
    def _calculate_quality_score(self, items: List[Dict[str, Any]]) -> float:
        """Calculate overall quality score"""
        if not items:
            return 0
        
        total_score = 0
        
        for item in items:
            score = 0
            
            # Name quality
            if item.get('name') and len(item['name']) > 3:
                score += 0.3
            
            # Price presence
            if item.get('price'):
                score += 0.2
            
            # Description quality
            if item.get('description') and len(item['description']) > 10:
                score += 0.2
            
            # Allergen detection
            if item.get('allergens'):
                score += 0.15
            
            # Dietary tags
            if item.get('dietary_tags'):
                score += 0.1
            
            # Category classification
            if item.get('category') and item['category'] != 'other':
                score += 0.05
            
            total_score += score
        
        return round(total_score / len(items), 2)
    
    async def cleanup(self):
        """Clean up browser resources"""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
        except Exception:
            pass

# Example usage
if __name__ == "__main__":
    async def test_scraper():
        scraper = PracticalMLScraper(headless=True)
        
        if await scraper.setup_browser():
            # Test with a sample URL
            result = await scraper.extract_menu_items("https://www.yelp.com/biz/la-crepe-bistro-homer-glen")
            print(json.dumps(result, indent=2))
            
            await scraper.cleanup()
    
    asyncio.run(test_scraper())