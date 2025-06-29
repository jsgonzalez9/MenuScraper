#!/usr/bin/env python3
"""
Final ML-Enhanced Menu Scraper
Integrates machine learning concepts from AllergySavvy project with practical menu scraping
Focuses on achieving 50%+ success rate with enhanced allergen detection
"""

import asyncio
import json
import logging
import random
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urljoin, urlparse
import math

try:
    from playwright.async_api import async_playwright, Browser, Page
except ImportError:
    print("❌ Playwright not installed. Run: pip install playwright")
    exit(1)

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("❌ BeautifulSoup not installed. Run: pip install beautifulsoup4")
    exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('final_ml_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FinalMLMenuScraper:
    """Final ML-enhanced menu scraper with advanced allergen detection and extraction"""
    
    def __init__(self, headless: bool = True, timeout: int = 20000):
        self.headless = headless
        self.timeout = timeout
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        
        # Enhanced menu selectors based on successful patterns
        self.menu_selectors = [
            # High-success Yelp selectors
            'div[data-testid="menu-item"]',
            'div.menu-item',
            'div.menu-section-item',
            'div[class*="menu"][class*="item"]',
            
            # Generic high-probability selectors
            '.menu-item', '.menu-entry', '.dish', '.food-item',
            '[class*="menu-item"]', '[class*="dish"]', '[class*="food"]',
            'li[class*="menu"]', 'div[class*="menu"]',
            
            # Content-based selectors
            'div:has-text("$")', 'li:has-text("$")',
            'div[class*="price"]', 'span[class*="price"]'
        ]
        
        # ML-inspired allergen detection (based on AllergySavvy approach)
        self.allergen_database = {
            'gluten': {
                'primary': ['gluten', 'wheat', 'flour', 'bread', 'pasta', 'noodles', 'cereal', 'barley', 'rye', 'oats'],
                'secondary': ['breaded', 'battered', 'crusted', 'dough', 'pastry', 'cake', 'cookie', 'cracker'],
                'weight': 1.0
            },
            'dairy': {
                'primary': ['milk', 'cheese', 'butter', 'cream', 'yogurt', 'dairy', 'lactose', 'casein', 'whey'],
                'secondary': ['creamy', 'cheesy', 'buttery', 'milky', 'parmesan', 'mozzarella', 'cheddar'],
                'weight': 1.0
            },
            'nuts': {
                'primary': ['nuts', 'almond', 'walnut', 'pecan', 'cashew', 'pistachio', 'hazelnut', 'macadamia'],
                'secondary': ['nutty', 'nut-based', 'tree nuts'],
                'weight': 1.0
            },
            'peanuts': {
                'primary': ['peanut', 'peanuts', 'groundnut'],
                'secondary': ['peanut butter', 'pb'],
                'weight': 1.0
            },
            'shellfish': {
                'primary': ['shrimp', 'crab', 'lobster', 'shellfish', 'prawns', 'crayfish', 'scallops', 'mussels', 'clams', 'oysters'],
                'secondary': ['seafood', 'crustacean', 'mollusk'],
                'weight': 1.0
            },
            'fish': {
                'primary': ['fish', 'salmon', 'tuna', 'cod', 'halibut', 'trout', 'bass', 'anchovy', 'sardine'],
                'secondary': ['fishy', 'seafood'],
                'weight': 0.8
            },
            'eggs': {
                'primary': ['egg', 'eggs', 'mayonnaise', 'mayo', 'albumin'],
                'secondary': ['eggy', 'egg-based', 'custard', 'meringue'],
                'weight': 1.0
            },
            'soy': {
                'primary': ['soy', 'soybean', 'tofu', 'tempeh', 'miso', 'soy sauce', 'edamame'],
                'secondary': ['soy-based', 'soya'],
                'weight': 1.0
            },
            'sesame': {
                'primary': ['sesame', 'tahini', 'sesame seeds', 'sesame oil'],
                'secondary': ['seeded'],
                'weight': 1.0
            }
        }
        
        # Price extraction patterns
        self.price_patterns = [
            r'\$\d+\.\d{2}',  # $12.99
            r'\$\d+',         # $12
            r'\d+\.\d{2}',    # 12.99
            r'Price:\s*\$?\d+(?:\.\d{2})?',  # Price: $12.99
            r'\b\d{1,3}(?:\.\d{2})?\s*(?:dollars?|USD|\$)\b'  # 12.99 dollars
        ]
        
        # ML-inspired confidence scoring
        self.confidence_weights = {
            'has_price': 0.3,
            'has_description': 0.2,
            'reasonable_length': 0.2,
            'food_keywords': 0.2,
            'allergen_context': 0.1
        }
        
        # Food-related keywords for ML scoring
        self.food_keywords = [
            'served', 'grilled', 'fried', 'baked', 'roasted', 'steamed', 'sauteed',
            'fresh', 'organic', 'homemade', 'house', 'special', 'signature',
            'sauce', 'dressing', 'marinade', 'seasoned', 'spiced', 'flavored',
            'tender', 'crispy', 'juicy', 'delicious', 'savory', 'sweet'
        ]
    
    async def setup_browser(self) -> bool:
        """Setup browser with enhanced stealth configuration"""
        try:
            playwright = await async_playwright().start()
            
            # Advanced stealth browser setup
            self.browser = await playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--no-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-features=VizDisplayCompositor',
                    '--disable-web-security',
                    '--disable-features=TranslateUI',
                    '--disable-ipc-flooding-protection',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding',
                    '--disable-field-trial-config',
                    '--disable-back-forward-cache',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding',
                    '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                ]
            )
            
            # Create page with enhanced settings
            self.page = await self.browser.new_page()
            
            # Set realistic viewport
            await self.page.set_viewport_size({"width": 1920, "height": 1080})
            
            # Enhanced stealth scripts
            await self.page.add_init_script("""
                // Remove webdriver property
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                
                // Mock plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
                
                // Mock languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en'],
                });
                
                // Mock permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
                
                // Mock chrome object
                window.chrome = {
                    runtime: {},
                };
            """)
            
            logger.info("✅ Enhanced browser setup completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Browser setup failed: {e}")
            return False
    
    async def smart_navigate(self, url: str, max_retries: int = 2) -> bool:
        """Smart navigation with ML-inspired retry logic"""
        for attempt in range(max_retries):
            try:
                logger.info(f"🌐 Smart navigation to {url} (attempt {attempt + 1}/{max_retries})")
                
                # Human-like delay with randomization
                delay = random.uniform(2, 5) + (attempt * 2)  # Increase delay on retries
                await asyncio.sleep(delay)
                
                # Navigate with optimized settings
                response = await self.page.goto(
                    url, 
                    wait_until='networkidle',  # Wait for network to be idle
                    timeout=self.timeout
                )
                
                if response and response.status == 200:
                    # Additional wait for dynamic content
                    await asyncio.sleep(random.uniform(3, 6))
                    
                    # Check page content quality
                    content = await self.page.content()
                    if self._assess_page_quality(content):
                        logger.info("✅ Smart navigation successful")
                        return True
                    else:
                        logger.warning(f"⚠️ Poor page quality on attempt {attempt + 1}")
                else:
                    logger.warning(f"⚠️ HTTP {response.status if response else 'No response'}")
                    
            except Exception as e:
                logger.error(f"❌ Navigation attempt {attempt + 1} failed: {e}")
                
            if attempt < max_retries - 1:
                await asyncio.sleep(random.uniform(5, 10))
        
        return False
    
    def _assess_page_quality(self, content: str) -> bool:
        """ML-inspired page quality assessment"""
        content_lower = content.lower()
        
        # Check for bot detection
        bot_indicators = [
            "robot", "captcha", "verification", "blocked",
            "access denied", "suspicious activity",
            "please verify", "security check", "cloudflare"
        ]
        
        if any(indicator in content_lower for indicator in bot_indicators):
            return False
        
        # Check for meaningful content
        quality_indicators = [
            "menu", "food", "restaurant", "dish", "price", "$",
            "order", "delivery", "cuisine", "meal"
        ]
        
        quality_score = sum(1 for indicator in quality_indicators if indicator in content_lower)
        return quality_score >= 3  # Require at least 3 quality indicators
    
    async def extract_menu_items(self, url: str) -> Dict[str, Any]:
        """ML-enhanced menu extraction with confidence scoring"""
        start_time = time.time()
        result = {
            'url': url,
            'success': False,
            'items': [],
            'total_items': 0,
            'processing_time': 0,
            'extraction_method': None,
            'ml_features': {
                'confidence_scores': [],
                'allergen_detections': {},
                'quality_assessment': 0,
                'extraction_strategies_used': []
            },
            'allergen_summary': {},
            'price_coverage': 0,
            'error': None
        }
        
        try:
            # Smart navigation
            if not await self.smart_navigate(url):
                result['error'] = 'Smart navigation failed'
                return result
            
            # Get page content
            content = await self.page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # ML-enhanced extraction pipeline
            items = []
            extraction_strategies = []
            
            # Strategy 1: Enhanced CSS Selectors with ML scoring
            css_items = await self._extract_with_css_selectors()
            if css_items:
                items.extend(css_items)
                extraction_strategies.append('enhanced_css_selectors')
            
            # Strategy 2: ML-inspired text pattern analysis
            if len(items) < 5:  # Only if we need more items
                text_items = self._extract_with_ml_text_analysis(soup)
                if text_items:
                    items.extend(text_items)
                    extraction_strategies.append('ml_text_analysis')
            
            # Strategy 3: Structured data with ML validation
            if len(items) < 3:  # Only if we still need more items
                structured_items = self._extract_structured_data_ml(soup)
                if structured_items:
                    items.extend(structured_items)
                    extraction_strategies.append('structured_data_ml')
            
            # ML post-processing
            if items:
                # Remove duplicates with ML similarity
                unique_items = self._ml_deduplicate(items)
                
                # Score and rank items
                scored_items = []
                for item in unique_items:
                    confidence = self._calculate_ml_confidence(item)
                    allergens = self._ml_allergen_detection(item)
                    
                    item['confidence_score'] = confidence
                    item['allergens'] = allergens
                    item['allergen_risk_level'] = self._assess_allergen_risk(allergens)
                    
                    if confidence > 0.3:  # ML confidence threshold
                        scored_items.append(item)
                
                # Sort by confidence
                scored_items.sort(key=lambda x: x['confidence_score'], reverse=True)
                
                # Take top items
                final_items = scored_items[:15]  # Limit to prevent overwhelming
                
                result.update({
                    'success': True,
                    'items': final_items,
                    'total_items': len(final_items),
                    'extraction_method': ' + '.join(extraction_strategies),
                    'ml_features': {
                        'confidence_scores': [item['confidence_score'] for item in final_items],
                        'allergen_detections': self._summarize_allergens(final_items),
                        'quality_assessment': self._assess_extraction_quality(final_items),
                        'extraction_strategies_used': extraction_strategies
                    },
                    'allergen_summary': self._summarize_allergens(final_items),
                    'price_coverage': self._calculate_price_coverage(final_items)
                })
                
                logger.info(f"✅ ML extraction successful: {len(final_items)} items")
            else:
                result['error'] = 'No valid menu items found'
                logger.warning("⚠️ ML extraction found no items")
                
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"❌ ML extraction failed: {e}")
        
        finally:
            result['processing_time'] = round(time.time() - start_time, 2)
        
        return result
    
    async def _extract_with_css_selectors(self) -> List[Dict[str, Any]]:
        """Enhanced CSS selector extraction with ML validation"""
        items = []
        
        for selector in self.menu_selectors:
            try:
                elements = await self.page.query_selector_all(selector)
                if elements and len(elements) > 0:
                    logger.info(f"📋 Found {len(elements)} elements with selector: {selector}")
                    
                    for element in elements[:20]:  # Limit processing
                        item_data = await self._extract_item_data_ml(element)
                        if item_data and self._validate_item_ml(item_data):
                            items.append(item_data)
                    
                    if items:
                        break  # Use first successful selector
                        
            except Exception as e:
                logger.debug(f"Selector {selector} failed: {e}")
                continue
        
        return items
    
    async def _extract_item_data_ml(self, element) -> Optional[Dict[str, Any]]:
        """ML-enhanced item data extraction"""
        try:
            # Get comprehensive text content
            text_content = await element.text_content()
            if not text_content or len(text_content.strip()) < 3:
                return None
            
            # Get HTML for structure analysis
            html_content = await element.inner_html()
            
            # ML-inspired extraction
            name = self._extract_item_name_ml(text_content)
            price = self._extract_price_ml(text_content)
            description = self._extract_description_ml(text_content, name)
            
            # Additional ML features
            category = self._predict_category_ml(text_content)
            dietary_tags = self._extract_dietary_tags_ml(text_content)
            
            return {
                'name': name,
                'description': description,
                'price': price,
                'category': category,
                'dietary_tags': dietary_tags,
                'raw_text': text_content.strip(),
                'html_structure': len(html_content),
                'allergens': [],  # Will be populated later
                'confidence_score': 0  # Will be calculated later
            }
            
        except Exception as e:
            logger.debug(f"ML item extraction failed: {e}")
            return None
    
    def _extract_item_name_ml(self, text: str) -> str:
        """ML-enhanced name extraction"""
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if not lines:
            return "Unknown Item"
        
        # Find the most likely name line using ML heuristics
        best_line = lines[0]
        best_score = 0
        
        for line in lines[:3]:  # Check first 3 lines
            score = 0
            
            # Scoring factors
            if len(line) > 5 and len(line) < 50:  # Reasonable length
                score += 2
            if not re.search(r'\$\d+', line):  # No price
                score += 2
            if any(keyword in line.lower() for keyword in self.food_keywords[:10]):
                score += 1
            if line[0].isupper():  # Starts with capital
                score += 1
            
            if score > best_score:
                best_score = score
                best_line = line
        
        # Clean the name
        name = re.sub(r'\$\d+(?:\.\d{2})?', '', best_line).strip()
        return name[:100]  # Limit length
    
    def _extract_price_ml(self, text: str) -> Optional[str]:
        """ML-enhanced price extraction"""
        for pattern in self.price_patterns:
            matches = re.findall(pattern, text)
            if matches:
                # Return the most reasonable price (not too high/low)
                for match in matches:
                    price_num = re.findall(r'\d+(?:\.\d{2})?', match)
                    if price_num:
                        price_val = float(price_num[0])
                        if 1 <= price_val <= 200:  # Reasonable price range
                            return match
        return None
    
    def _extract_description_ml(self, text: str, name: str) -> str:
        """ML-enhanced description extraction"""
        # Remove name and price to get description
        description = text.replace(name, '', 1)
        
        # Remove prices
        for pattern in self.price_patterns:
            description = re.sub(pattern, '', description)
        
        # Clean up
        description = re.sub(r'\s+', ' ', description).strip()
        
        # Extract meaningful description (not just single words)
        if len(description) > 10:
            return description[:500]
        return ""
    
    def _predict_category_ml(self, text: str) -> str:
        """ML-inspired category prediction"""
        text_lower = text.lower()
        
        categories = {
            'appetizer': ['appetizer', 'starter', 'app', 'small plate', 'sharing'],
            'main': ['entree', 'main', 'dinner', 'lunch', 'plate', 'served with'],
            'dessert': ['dessert', 'sweet', 'cake', 'ice cream', 'chocolate'],
            'beverage': ['drink', 'beverage', 'coffee', 'tea', 'soda', 'juice'],
            'salad': ['salad', 'greens', 'lettuce', 'mixed greens'],
            'soup': ['soup', 'broth', 'bisque', 'chowder']
        }
        
        for category, keywords in categories.items():
            if any(keyword in text_lower for keyword in keywords):
                return category
        
        return 'main'  # Default category
    
    def _extract_dietary_tags_ml(self, text: str) -> List[str]:
        """ML-enhanced dietary tag extraction"""
        text_lower = text.lower()
        tags = []
        
        dietary_patterns = {
            'vegetarian': ['vegetarian', 'veggie', 'no meat'],
            'vegan': ['vegan', 'plant-based', 'dairy-free'],
            'gluten-free': ['gluten-free', 'gf', 'no gluten'],
            'organic': ['organic', 'farm-fresh', 'locally sourced'],
            'spicy': ['spicy', 'hot', 'jalapeño', 'chili', 'pepper']
        }
        
        for tag, patterns in dietary_patterns.items():
            if any(pattern in text_lower for pattern in patterns):
                tags.append(tag)
        
        return tags
    
    def _extract_with_ml_text_analysis(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """ML-inspired text pattern analysis"""
        items = []
        
        # Find text blocks that look like menu items
        text_elements = soup.find_all(text=True)
        
        for text in text_elements:
            if text and len(text.strip()) > 15:  # Minimum length for menu item
                # ML scoring for menu item likelihood
                score = 0
                text_lower = text.lower()
                
                # Price presence (strong indicator)
                if any(re.search(pattern, text) for pattern in self.price_patterns):
                    score += 3
                
                # Food keywords
                food_word_count = sum(1 for keyword in self.food_keywords if keyword in text_lower)
                score += min(food_word_count, 2)  # Cap at 2 points
                
                # Length scoring
                if 20 <= len(text) <= 200:
                    score += 1
                
                # If score is high enough, extract as menu item
                if score >= 3:
                    item = {
                        'name': self._extract_item_name_ml(text),
                        'description': self._extract_description_ml(text, ''),
                        'price': self._extract_price_ml(text),
                        'category': self._predict_category_ml(text),
                        'dietary_tags': self._extract_dietary_tags_ml(text),
                        'raw_text': text.strip(),
                        'html_structure': 0,
                        'allergens': [],
                        'confidence_score': 0
                    }
                    
                    if self._validate_item_ml(item):
                        items.append(item)
        
        return items[:10]  # Limit results
    
    def _extract_structured_data_ml(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """ML-enhanced structured data extraction"""
        items = []
        
        # JSON-LD structured data
        scripts = soup.find_all('script', type='application/ld+json')
        for script in scripts:
            try:
                data = json.loads(script.string)
                menu_items = self._process_structured_menu_ml(data)
                items.extend(menu_items)
            except (json.JSONDecodeError, KeyError):
                continue
        
        # Microdata with ML validation
        microdata_items = soup.find_all(attrs={'itemtype': re.compile(r'MenuItem|Food')})
        for item in microdata_items:
            menu_item = self._process_microdata_item_ml(item)
            if menu_item:
                items.append(menu_item)
        
        return items
    
    def _process_structured_menu_ml(self, data: Dict) -> List[Dict[str, Any]]:
        """Process structured menu data with ML validation"""
        items = []
        # Implementation would depend on specific structured data format
        # This is a placeholder for structured data processing
        return items
    
    def _process_microdata_item_ml(self, element) -> Optional[Dict[str, Any]]:
        """Process microdata with ML validation"""
        try:
            name_elem = element.find(attrs={'itemprop': 'name'})
            desc_elem = element.find(attrs={'itemprop': 'description'})
            price_elem = element.find(attrs={'itemprop': 'price'})
            
            if name_elem:
                item = {
                    'name': name_elem.get_text(strip=True),
                    'description': desc_elem.get_text(strip=True) if desc_elem else '',
                    'price': price_elem.get_text(strip=True) if price_elem else None,
                    'category': 'main',
                    'dietary_tags': [],
                    'raw_text': element.get_text(strip=True),
                    'html_structure': len(str(element)),
                    'allergens': [],
                    'confidence_score': 0
                }
                
                if self._validate_item_ml(item):
                    return item
        except Exception:
            pass
        return None
    
    def _validate_item_ml(self, item: Dict[str, Any]) -> bool:
        """ML-enhanced item validation"""
        if not item or not item.get('name'):
            return False
        
        name = item['name'].lower()
        
        # ML-based filtering
        invalid_patterns = [
            'submit', 'button', 'click', 'menu', 'section',
            'category', 'view', 'more', 'see', 'robot', 'verify',
            'loading', 'error', 'please', 'try', 'again'
        ]
        
        if any(pattern in name for pattern in invalid_patterns):
            return False
        
        # Length validation
        if len(item['name']) < 2 or len(item['name']) > 100:
            return False
        
        # ML confidence pre-check
        basic_confidence = self._calculate_basic_confidence(item)
        return basic_confidence > 0.2
    
    def _calculate_basic_confidence(self, item: Dict[str, Any]) -> float:
        """Calculate basic confidence score"""
        score = 0.0
        
        # Has price
        if item.get('price'):
            score += 0.3
        
        # Has description
        if item.get('description') and len(item['description']) > 5:
            score += 0.2
        
        # Reasonable name length
        name_len = len(item.get('name', ''))
        if 5 <= name_len <= 50:
            score += 0.2
        
        # Food keywords in text
        text = (item.get('name', '') + ' ' + item.get('description', '')).lower()
        food_matches = sum(1 for keyword in self.food_keywords[:20] if keyword in text)
        score += min(food_matches * 0.05, 0.2)
        
        return min(score, 1.0)
    
    def _calculate_ml_confidence(self, item: Dict[str, Any]) -> float:
        """Calculate ML-enhanced confidence score"""
        score = 0.0
        
        # Price presence and validity
        if item.get('price'):
            price_text = item['price']
            price_nums = re.findall(r'\d+(?:\.\d{2})?', price_text)
            if price_nums:
                price_val = float(price_nums[0])
                if 1 <= price_val <= 200:
                    score += self.confidence_weights['has_price']
        
        # Description quality
        description = item.get('description', '')
        if len(description) > 10:
            score += self.confidence_weights['has_description']
            
            # Bonus for descriptive words
            desc_words = len(description.split())
            if desc_words >= 5:
                score += 0.1
        
        # Name length reasonableness
        name_len = len(item.get('name', ''))
        if 5 <= name_len <= 50:
            score += self.confidence_weights['reasonable_length']
        
        # Food keyword presence
        text = (item.get('name', '') + ' ' + description).lower()
        food_matches = sum(1 for keyword in self.food_keywords if keyword in text)
        food_score = min(food_matches / 10, 1.0) * self.confidence_weights['food_keywords']
        score += food_score
        
        # Allergen context (indicates food-related content)
        allergen_matches = 0
        for allergen_data in self.allergen_database.values():
            allergen_matches += sum(1 for keyword in allergen_data['primary'][:5] if keyword in text)
        
        allergen_score = min(allergen_matches / 5, 1.0) * self.confidence_weights['allergen_context']
        score += allergen_score
        
        return min(score, 1.0)
    
    def _ml_allergen_detection(self, item: Dict[str, Any]) -> List[str]:
        """ML-enhanced allergen detection based on AllergySavvy approach"""
        allergens = []
        text = (item.get('name', '') + ' ' + item.get('description', '')).lower()
        
        for allergen, data in self.allergen_database.items():
            confidence = 0.0
            
            # Primary keyword matches (high confidence)
            primary_matches = sum(1 for keyword in data['primary'] if keyword in text)
            confidence += primary_matches * 0.8
            
            # Secondary keyword matches (medium confidence)
            secondary_matches = sum(1 for keyword in data['secondary'] if keyword in text)
            confidence += secondary_matches * 0.4
            
            # Apply allergen weight
            confidence *= data['weight']
            
            # Threshold for detection
            if confidence >= 0.5:
                allergens.append(allergen)
        
        return allergens
    
    def _assess_allergen_risk(self, allergens: List[str]) -> str:
        """Assess allergen risk level"""
        if not allergens:
            return 'low'
        
        high_risk_allergens = ['nuts', 'peanuts', 'shellfish', 'fish']
        medium_risk_allergens = ['dairy', 'eggs', 'gluten']
        
        if any(allergen in high_risk_allergens for allergen in allergens):
            return 'high'
        elif any(allergen in medium_risk_allergens for allergen in allergens):
            return 'medium'
        else:
            return 'low'
    
    def _ml_deduplicate(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """ML-enhanced deduplication using similarity scoring"""
        if not items:
            return []
        
        unique_items = []
        
        for item in items:
            is_duplicate = False
            item_name = item['name'].lower().strip()
            
            for existing in unique_items:
                existing_name = existing['name'].lower().strip()
                
                # Calculate similarity
                similarity = self._calculate_text_similarity(item_name, existing_name)
                
                if similarity > 0.8:  # High similarity threshold
                    is_duplicate = True
                    # Keep the item with higher confidence
                    if item.get('confidence_score', 0) > existing.get('confidence_score', 0):
                        unique_items.remove(existing)
                        unique_items.append(item)
                    break
            
            if not is_duplicate:
                unique_items.append(item)
        
        return unique_items
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity using simple ML approach"""
        # Simple Jaccard similarity
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 and not words2:
            return 1.0
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def _assess_extraction_quality(self, items: List[Dict[str, Any]]) -> float:
        """Assess overall extraction quality"""
        if not items:
            return 0.0
        
        total_score = 0.0
        
        for item in items:
            item_score = 0.0
            
            # Price coverage
            if item.get('price'):
                item_score += 0.3
            
            # Description quality
            if item.get('description') and len(item['description']) > 10:
                item_score += 0.3
            
            # Allergen detection
            if item.get('allergens'):
                item_score += 0.2
            
            # Confidence score
            item_score += item.get('confidence_score', 0) * 0.2
            
            total_score += item_score
        
        return round(total_score / len(items), 2)
    
    def _summarize_allergens(self, items: List[Dict[str, Any]]) -> Dict[str, int]:
        """Summarize allergen occurrences"""
        allergen_counts = {}
        
        for item in items:
            for allergen in item.get('allergens', []):
                allergen_counts[allergen] = allergen_counts.get(allergen, 0) + 1
        
        return allergen_counts
    
    def _calculate_price_coverage(self, items: List[Dict[str, Any]]) -> float:
        """Calculate price coverage percentage"""
        if not items:
            return 0.0
        
        items_with_price = sum(1 for item in items if item.get('price'))
        return round((items_with_price / len(items)) * 100, 1)
    
    async def cleanup(self):
        """Clean up browser resources"""
        try:
            if self.page:
                await self.page.close()
            if self.browser:
                await self.browser.close()
            logger.info("🧹 ML scraper cleanup completed")
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")

# Example usage
if __name__ == "__main__":
    async def test_ml_scraper():
        scraper = FinalMLMenuScraper(headless=True)
        
        try:
            await scraper.setup_browser()
            
            # Test with a sample URL
            test_url = "https://www.yelp.com/biz/la-crepe-bistro-homer-glen"
            result = await scraper.extract_menu_items(test_url)
            
            print(f"\n🎯 FINAL ML SCRAPER TEST RESULTS:")
            print(f"Success: {result['success']}")
            print(f"Items extracted: {result['total_items']}")
            print(f"Processing time: {result['processing_time']}s")
            print(f"Extraction method: {result['extraction_method']}")
            print(f"ML Quality: {result['ml_features']['quality_assessment']}")
            
            if result['items']:
                print(f"\n📋 Sample items:")
                for i, item in enumerate(result['items'][:3], 1):
                    print(f"  {i}. {item['name']} - {item.get('price', 'No price')}")
                    print(f"     Confidence: {item['confidence_score']:.2f}")
                    if item.get('allergens'):
                        print(f"     Allergens: {', '.join(item['allergens'])}")
            
        finally:
            await scraper.cleanup()
    
    # Run the test
    asyncio.run(test_ml_scraper())