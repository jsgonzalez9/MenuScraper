#!/usr/bin/env python3
"""
Enhanced Allergen-Aware Menu Scraper
A practical implementation that works without ML dependencies
but provides allergen detection and improved extraction
"""

import re
import json
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urljoin, urlparse
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError
from dataclasses import dataclass
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AllergenType(Enum):
    """EU-regulated allergen types"""
    GLUTEN = "gluten"
    CRUSTACEANS = "crustaceans"
    EGGS = "eggs"
    FISH = "fish"
    PEANUTS = "peanuts"
    SOYBEANS = "soybeans"
    MILK = "milk"
    NUTS = "nuts"
    CELERY = "celery"
    MUSTARD = "mustard"
    SESAME = "sesame"
    SULPHITES = "sulphites"
    LUPIN = "lupin"
    MOLLUSCS = "molluscs"

@dataclass
class EnhancedMenuItem:
    """Enhanced menu item with allergen information"""
    name: str
    description: str
    price: Optional[str]
    category: str
    allergens: List[AllergenType]
    allergen_confidence: Dict[str, float]
    dietary_tags: List[str]
    confidence_score: float
    extraction_method: str

class AllergenDetector:
    """Rule-based allergen detection system"""
    
    def __init__(self):
        # Comprehensive allergen keyword database
        self.allergen_keywords = {
            AllergenType.GLUTEN: {
                'primary': ['wheat', 'barley', 'rye', 'oats', 'gluten'],
                'secondary': ['bread', 'pasta', 'flour', 'seitan', 'bulgur', 'couscous', 'semolina', 'farro', 'spelt'],
                'dishes': ['pizza', 'sandwich', 'burger', 'wrap', 'noodles', 'dumpling']
            },
            AllergenType.MILK: {
                'primary': ['milk', 'dairy', 'lactose', 'casein', 'whey'],
                'secondary': ['cheese', 'butter', 'cream', 'yogurt', 'ice cream'],
                'dishes': ['mozzarella', 'parmesan', 'cheddar', 'brie', 'feta', 'ricotta']
            },
            AllergenType.EGGS: {
                'primary': ['egg', 'eggs'],
                'secondary': ['mayonnaise', 'mayo', 'meringue', 'custard', 'albumin', 'lecithin'],
                'dishes': ['omelet', 'frittata', 'quiche', 'carbonara']
            },
            AllergenType.NUTS: {
                'primary': ['nuts', 'tree nuts'],
                'secondary': ['almond', 'walnut', 'pecan', 'cashew', 'pistachio', 'hazelnut', 'brazil nut', 'macadamia', 'pine nut'],
                'dishes': ['pesto', 'marzipan', 'nougat', 'praline']
            },
            AllergenType.PEANUTS: {
                'primary': ['peanut', 'peanuts', 'groundnut'],
                'secondary': ['arachis', 'peanut butter', 'peanut oil'],
                'dishes': ['satay', 'pad thai', 'kung pao']
            },
            AllergenType.FISH: {
                'primary': ['fish', 'seafood'],
                'secondary': ['salmon', 'tuna', 'cod', 'bass', 'trout', 'anchovy', 'sardine', 'halibut', 'sole'],
                'dishes': ['sushi', 'sashimi', 'fish and chips', 'ceviche']
            },
            AllergenType.CRUSTACEANS: {
                'primary': ['crustacean', 'shellfish'],
                'secondary': ['shrimp', 'crab', 'lobster', 'prawn', 'crawfish', 'crayfish'],
                'dishes': ['bisque', 'paella', 'jambalaya']
            },
            AllergenType.MOLLUSCS: {
                'primary': ['mollusc', 'mollusk'],
                'secondary': ['oyster', 'mussel', 'clam', 'scallop', 'squid', 'octopus'],
                'dishes': ['calamari', 'escargot']
            },
            AllergenType.SOYBEANS: {
                'primary': ['soy', 'soya', 'soybean'],
                'secondary': ['tofu', 'tempeh', 'miso', 'edamame', 'soy sauce', 'tamari'],
                'dishes': ['teriyaki', 'miso soup']
            },
            AllergenType.SESAME: {
                'primary': ['sesame'],
                'secondary': ['tahini', 'sesame seed', 'sesame oil'],
                'dishes': ['hummus', 'baba ganoush']
            },
            AllergenType.SULPHITES: {
                'primary': ['sulfite', 'sulphite'],
                'secondary': ['wine', 'dried fruit', 'preservative'],
                'dishes': ['wine sauce', 'dried tomatoes']
            },
            AllergenType.CELERY: {
                'primary': ['celery'],
                'secondary': ['celeriac', 'celery seed', 'celery salt'],
                'dishes': ['waldorf salad', 'bloody mary']
            },
            AllergenType.MUSTARD: {
                'primary': ['mustard'],
                'secondary': ['mustard seed', 'dijon', 'whole grain mustard'],
                'dishes': ['honey mustard', 'mustard sauce']
            },
            AllergenType.LUPIN: {
                'primary': ['lupin', 'lupine'],
                'secondary': ['lupin flour', 'lupin bean'],
                'dishes': []
            }
        }
        
        # Dietary pattern recognition
        self.dietary_patterns = {
            'vegan': [
                'vegan', 'plant-based', 'no animal products', 'dairy-free and egg-free',
                'completely plant', 'animal-free'
            ],
            'vegetarian': [
                'vegetarian', 'veggie', 'no meat', 'meat-free', 'plant-based'
            ],
            'gluten-free': [
                'gluten-free', 'gluten free', 'gf', 'no gluten', 'celiac safe',
                'wheat-free', 'gluten friendly'
            ],
            'dairy-free': [
                'dairy-free', 'dairy free', 'lactose-free', 'no dairy', 'milk-free',
                'lactose intolerant friendly'
            ],
            'nut-free': [
                'nut-free', 'nut free', 'no nuts', 'tree nut free', 'allergy-friendly'
            ],
            'keto': [
                'keto', 'ketogenic', 'low-carb', 'high-fat', 'keto-friendly'
            ],
            'paleo': [
                'paleo', 'paleolithic', 'primal', 'caveman diet'
            ],
            'low-sodium': [
                'low-sodium', 'low salt', 'heart-healthy', 'reduced sodium'
            ]
        }
    
    def detect_allergens(self, text: str) -> Tuple[List[AllergenType], Dict[str, float]]:
        """Detect allergens in menu item text with confidence scoring"""
        detected_allergens = []
        confidence_scores = {}
        
        text_lower = text.lower()
        
        for allergen_type, keyword_groups in self.allergen_keywords.items():
            max_confidence = 0.0
            found_keywords = []
            
            # Check primary keywords (highest confidence)
            for keyword in keyword_groups['primary']:
                if self._keyword_match(keyword, text_lower):
                    found_keywords.append(keyword)
                    max_confidence = max(max_confidence, 0.9)
            
            # Check secondary keywords (medium confidence)
            for keyword in keyword_groups['secondary']:
                if self._keyword_match(keyword, text_lower):
                    found_keywords.append(keyword)
                    max_confidence = max(max_confidence, 0.7)
            
            # Check dish keywords (lower confidence)
            for keyword in keyword_groups['dishes']:
                if self._keyword_match(keyword, text_lower):
                    found_keywords.append(keyword)
                    max_confidence = max(max_confidence, 0.6)
            
            # Boost confidence for multiple matches
            if len(found_keywords) > 1:
                max_confidence = min(max_confidence + 0.1, 0.95)
            
            # Add allergen if confidence threshold met
            if max_confidence >= 0.6:
                detected_allergens.append(allergen_type)
                confidence_scores[allergen_type.value] = round(max_confidence, 2)
        
        return detected_allergens, confidence_scores
    
    def _keyword_match(self, keyword: str, text: str) -> bool:
        """Enhanced keyword matching with word boundaries"""
        # Exact word match
        if f" {keyword} " in f" {text} ":
            return True
        
        # Start/end of string match
        if text.startswith(keyword + " ") or text.endswith(" " + keyword):
            return True
        
        # Single word match
        if text == keyword:
            return True
        
        return False
    
    def detect_dietary_tags(self, text: str) -> List[str]:
        """Detect dietary restriction tags"""
        detected_tags = []
        text_lower = text.lower()
        
        for tag, patterns in self.dietary_patterns.items():
            for pattern in patterns:
                if pattern in text_lower:
                    detected_tags.append(tag)
                    break
        
        return list(set(detected_tags))

class EnhancedMenuScraper:
    """Enhanced menu scraper with allergen detection"""
    
    def __init__(self):
        self.allergen_detector = AllergenDetector()
        self.price_patterns = [
            r'\$\d+(?:\.\d{2})?',
            r'\d+(?:\.\d{2})?\s*(?:dollars?|usd|\$)',
            r'\b\d{1,3}(?:,\d{3})*(?:\.\d{2})?\b',
        ]
        
        # Enhanced CSS selectors
        self.menu_selectors = [
            # Standard menu item selectors
            '.menu-item, .menuitem, .menu_item',
            '.food-item, .fooditem, .food_item',
            '.dish, .dish-item, .dish_item',
            '.product, .product-item',
            
            # Yelp-specific selectors
            '[data-testid*="menu"]',
            '.menu-section-item',
            '.menu-item-details',
            
            # Generic content selectors
            '[class*="menu"][class*="item"]',
            '[class*="food"][class*="item"]',
            '.menu ul li, .menu ol li',
            '.food-menu li, .restaurant-menu li',
            
            # Fallback selectors
            'li:has-text("$")',
            'div:has-text("$"):not(:has(div:has-text("$")))',
            'p:has-text("$")',
        ]
    
    def enhanced_menu_detection(self, page: Page, url: str) -> Dict[str, Any]:
        """Enhanced menu detection with allergen analysis"""
        start_time = time.time()
        
        result = {
            'menu_items': [],
            'total_items': 0,
            'scraping_success': False,
            'allergen_detection_enabled': True,
            'dietary_tags_detected': [],
            'allergen_summary': {},
            'category_distribution': {},
            'source': 'enhanced_allergen_scraping',
            'processing_time': 0,
            'confidence_score': 0.0,
            'extraction_strategies': []
        }
        
        try:
            logger.info(f"Starting enhanced menu detection for: {url}")
            
            # Navigate with enhanced error handling
            try:
                page.goto(url, wait_until='networkidle', timeout=30000)
                time.sleep(3)  # Allow dynamic content to load
            except Exception as e:
                result['error'] = f"Navigation failed: {str(e)}"
                return result
            
            # Try multiple extraction strategies
            items = []
            
            # Strategy 1: Enhanced CSS selector extraction
            items.extend(self._extract_with_css_selectors(page))
            if items:
                result['extraction_strategies'].append('css_selectors')
            
            # Strategy 2: Text pattern extraction
            if len(items) < 5:
                text_items = self._extract_with_text_patterns(page)
                items.extend(text_items)
                if text_items:
                    result['extraction_strategies'].append('text_patterns')
            
            # Strategy 3: Structured data extraction
            if len(items) < 3:
                structured_items = self._extract_structured_data(page)
                items.extend(structured_items)
                if structured_items:
                    result['extraction_strategies'].append('structured_data')
            
            # Remove duplicates and validate
            unique_items = self._deduplicate_items(items)
            valid_items = [item for item in unique_items if self._is_valid_menu_item(item)]
            
            if valid_items:
                # Analyze allergens and dietary information
                all_allergens = set()
                all_dietary_tags = set()
                category_counts = {}
                total_confidence = 0
                
                for item in valid_items:
                    # Collect statistics
                    for allergen in item.allergens:
                        all_allergens.add(allergen.value)
                    all_dietary_tags.update(item.dietary_tags)
                    
                    category = item.category
                    category_counts[category] = category_counts.get(category, 0) + 1
                    total_confidence += item.confidence_score
                
                # Convert to serializable format
                serializable_items = []
                for item in valid_items:
                    serializable_items.append({
                        'name': item.name,
                        'description': item.description,
                        'price': item.price,
                        'category': item.category,
                        'allergens': [a.value for a in item.allergens],
                        'allergen_confidence': item.allergen_confidence,
                        'dietary_tags': item.dietary_tags,
                        'confidence': item.confidence_score,
                        'extraction_method': item.extraction_method
                    })
                
                result['menu_items'] = serializable_items
                result['total_items'] = len(serializable_items)
                result['scraping_success'] = len(serializable_items) >= 3
                result['dietary_tags_detected'] = list(all_dietary_tags)
                result['category_distribution'] = category_counts
                
                # Allergen summary
                allergen_summary = {allergen: 0 for allergen in all_allergens}
                for item in serializable_items:
                    for allergen in item['allergens']:
                        if allergen in allergen_summary:
                            allergen_summary[allergen] += 1
                result['allergen_summary'] = allergen_summary
                
                # Overall confidence
                if valid_items:
                    result['confidence_score'] = round(total_confidence / len(valid_items), 3)
            
            result['processing_time'] = round(time.time() - start_time, 2)
            
            logger.info(f"Enhanced detection completed: {len(valid_items)} items found")
            return result
            
        except Exception as e:
            result['error'] = str(e)
            result['processing_time'] = round(time.time() - start_time, 2)
            logger.error(f"Enhanced detection failed: {e}")
            return result
    
    def _extract_with_css_selectors(self, page: Page) -> List[EnhancedMenuItem]:
        """Extract menu items using CSS selectors"""
        items = []
        
        for selector in self.menu_selectors:
            try:
                elements = page.query_selector_all(selector)
                
                for element in elements[:25]:  # Limit to prevent overload
                    try:
                        item = self._extract_item_from_element(element, 'css_selector')
                        if item:
                            items.append(item)
                    except Exception:
                        continue
                
                if len(items) >= 15:  # Stop if we have enough
                    break
                    
            except Exception:
                continue
        
        return items
    
    def _extract_with_text_patterns(self, page: Page) -> List[EnhancedMenuItem]:
        """Extract menu items using text pattern matching"""
        items = []
        
        try:
            # Get page text content
            page_text = page.inner_text('body')
            lines = [line.strip() for line in page_text.split('\n') if line.strip()]
            
            # Look for lines with prices
            price_pattern = re.compile(r'\$\d+(?:\.\d{2})?')
            
            for i, line in enumerate(lines):
                if price_pattern.search(line) and len(line) > 5 and len(line) < 200:
                    # Try to extract menu item from this line
                    item = self._extract_item_from_text(line, 'text_pattern')
                    if item:
                        items.append(item)
                        
                        if len(items) >= 10:
                            break
        
        except Exception as e:
            logger.warning(f"Text pattern extraction failed: {e}")
        
        return items
    
    def _extract_structured_data(self, page: Page) -> List[EnhancedMenuItem]:
        """Extract menu items from structured data (JSON-LD, microdata)"""
        items = []
        
        try:
            # Look for JSON-LD structured data
            json_scripts = page.query_selector_all('script[type="application/ld+json"]')
            
            for script in json_scripts:
                try:
                    content = script.inner_text()
                    data = json.loads(content)
                    
                    # Extract menu items from structured data
                    menu_items = self._parse_structured_menu_data(data)
                    items.extend(menu_items)
                    
                except Exception:
                    continue
        
        except Exception as e:
            logger.warning(f"Structured data extraction failed: {e}")
        
        return items
    
    def _extract_item_from_element(self, element, method: str) -> Optional[EnhancedMenuItem]:
        """Extract menu item from DOM element"""
        try:
            text = element.inner_text().strip()
            if not text or len(text) < 3:
                return None
            
            return self._extract_item_from_text(text, method)
            
        except Exception:
            return None
    
    def _extract_item_from_text(self, text: str, method: str) -> Optional[EnhancedMenuItem]:
        """Extract menu item from text with allergen detection"""
        try:
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            if not lines:
                return None
            
            # Parse basic information
            name = lines[0]
            description = ''
            price = None
            
            # Extract price
            for line in lines:
                price_match = self._extract_price_from_text(line)
                if price_match:
                    price = price_match
                    break
            
            # Extract description
            if len(lines) > 1:
                description = ' '.join(lines[1:]).replace(price or '', '').strip()
            
            # Clean up name
            name = re.sub(r'\$\d+(?:\.\d{2})?', '', name).strip()
            
            if len(name) < 2:
                return None
            
            # Enhanced analysis
            full_text = f"{name} {description}"
            
            # Detect allergens
            allergens, allergen_confidence = self.allergen_detector.detect_allergens(full_text)
            
            # Detect dietary tags
            dietary_tags = self.allergen_detector.detect_dietary_tags(full_text)
            
            # Categorize item
            category = self._categorize_menu_item(name, description)
            
            # Calculate confidence
            confidence_score = self._calculate_confidence(name, description, price, allergens, dietary_tags)
            
            return EnhancedMenuItem(
                name=name,
                description=description,
                price=price,
                category=category,
                allergens=allergens,
                allergen_confidence=allergen_confidence,
                dietary_tags=dietary_tags,
                confidence_score=confidence_score,
                extraction_method=method
            )
            
        except Exception:
            return None
    
    def _extract_price_from_text(self, text: str) -> Optional[str]:
        """Extract price from text"""
        for pattern in self.price_patterns:
            match = re.search(pattern, text)
            if match:
                price = match.group()
                if not price.startswith('$'):
                    price = f'${price}'
                return price
        return None
    
    def _categorize_menu_item(self, name: str, description: str) -> str:
        """Categorize menu item based on keywords"""
        text = f"{name} {description}".lower()
        
        category_keywords = {
            'appetizer': ['appetizer', 'starter', 'small plate', 'shareables', 'apps', 'dip', 'wings'],
            'salad': ['salad', 'greens', 'caesar', 'garden', 'mixed greens'],
            'soup': ['soup', 'bisque', 'chowder', 'broth', 'gazpacho'],
            'sandwich': ['sandwich', 'burger', 'wrap', 'panini', 'sub', 'hoagie'],
            'pasta': ['pasta', 'spaghetti', 'linguine', 'penne', 'ravioli', 'lasagna'],
            'pizza': ['pizza', 'flatbread', 'margherita', 'pepperoni'],
            'seafood': ['fish', 'salmon', 'tuna', 'shrimp', 'crab', 'lobster', 'scallop'],
            'meat': ['steak', 'beef', 'pork', 'chicken', 'lamb', 'ribs', 'turkey'],
            'dessert': ['dessert', 'cake', 'pie', 'ice cream', 'chocolate', 'sweet', 'tiramisu'],
            'beverage': ['drink', 'coffee', 'tea', 'juice', 'soda', 'beer', 'wine', 'cocktail']
        }
        
        for category, keywords in category_keywords.items():
            if any(keyword in text for keyword in keywords):
                return category
        
        return 'entree'
    
    def _calculate_confidence(self, name: str, description: str, price: Optional[str], 
                            allergens: List[AllergenType], dietary_tags: List[str]) -> float:
        """Calculate confidence score for menu item"""
        confidence = 0.5  # Base confidence
        
        # Name quality
        if len(name) > 5:
            confidence += 0.1
        if len(name) > 10:
            confidence += 0.1
        
        # Description quality
        if description and len(description) > 10:
            confidence += 0.1
        if description and len(description) > 30:
            confidence += 0.1
        
        # Price presence
        if price:
            confidence += 0.15
        
        # Allergen detection
        if allergens:
            confidence += 0.05
        
        # Dietary tags
        if dietary_tags:
            confidence += 0.05
        
        return min(confidence, 0.95)
    
    def _parse_structured_menu_data(self, data: Dict[str, Any]) -> List[EnhancedMenuItem]:
        """Parse structured data for menu items"""
        items = []
        
        # This would be expanded based on common structured data formats
        # For now, return empty list
        return items
    
    def _deduplicate_items(self, items: List[EnhancedMenuItem]) -> List[EnhancedMenuItem]:
        """Remove duplicate menu items"""
        seen_names = set()
        unique_items = []
        
        for item in items:
            name_key = item.name.lower().strip()
            if name_key not in seen_names and len(name_key) > 2:
                seen_names.add(name_key)
                unique_items.append(item)
        
        return unique_items
    
    def _is_valid_menu_item(self, item: EnhancedMenuItem) -> bool:
        """Validate menu item"""
        # Skip items with very low confidence
        if item.confidence_score < 0.4:
            return False
        
        # Skip very short names
        if len(item.name.strip()) < 3:
            return False
        
        # Skip navigation items
        nav_words = ['home', 'about', 'contact', 'menu', 'location', 'hours', 'order online']
        if any(word in item.name.lower() for word in nav_words):
            return False
        
        # Skip items that are just prices
        if re.match(r'^\$?\d+(?:\.\d{2})?$', item.name.strip()):
            return False
        
        return True

if __name__ == "__main__":
    # Test the enhanced scraper
    from playwright.sync_api import sync_playwright
    
    scraper = EnhancedMenuScraper()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        test_url = "https://www.yelp.com/biz/alinea-chicago"
        result = scraper.enhanced_menu_detection(page, test_url)
        
        print(f"Success: {result['scraping_success']}")
        print(f"Items found: {result['total_items']}")
        print(f"Strategies used: {result['extraction_strategies']}")
        print(f"Allergens detected: {list(result['allergen_summary'].keys())}")
        print(f"Dietary tags: {result['dietary_tags_detected']}")
        
        for item in result['menu_items'][:3]:
            print(f"\n- {item['name']}: {item.get('price', 'No price')}")
            print(f"  Allergens: {item['allergens']}")
            print(f"  Dietary: {item['dietary_tags']}")
            print(f"  Confidence: {item['confidence']:.2f}")
        
        browser.close()