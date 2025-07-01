#!/usr/bin/env python3
"""
ML-Enhanced Menu Scraper with Comprehensive Restaurant Data Integration
Combines intelligent menu extraction, allergen detection, and multi-source data merging
Supports both web scraping and API-based data collection
"""

import re
import json
import time
import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urljoin, urlparse
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import aiohttp
from bs4 import BeautifulSoup

# Playwright imports
try:
    from playwright.async_api import async_playwright, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    Page = Any  # Fallback type annotation

# ML and NLP imports
try:
    from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    import torch
    import numpy as np
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    print("Warning: ML libraries not available. Install transformers, torch, scikit-learn for full functionality.")

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
class MenuItemML:
    """Enhanced menu item with ML predictions"""
    name: str
    description: str
    price: Optional[str]
    category: str
    allergens: List[AllergenType]
    allergen_confidence: Dict[str, float]
    nutritional_info: Dict[str, Any]
    dietary_tags: List[str]  # vegan, vegetarian, gluten-free, etc.
    confidence_score: float
    extraction_method: str
    ml_enhanced: bool = True

class MLMenuExtractor:
    """Machine Learning enhanced menu extraction system"""
    
    def __init__(self):
        self.allergen_keywords = {
            AllergenType.GLUTEN: [
                'wheat', 'barley', 'rye', 'oats', 'bread', 'pasta', 'flour', 
                'gluten', 'seitan', 'bulgur', 'couscous', 'semolina'
            ],
            AllergenType.MILK: [
                'milk', 'cheese', 'butter', 'cream', 'yogurt', 'dairy', 
                'lactose', 'casein', 'whey', 'mozzarella', 'parmesan'
            ],
            AllergenType.EGGS: [
                'egg', 'eggs', 'mayonnaise', 'mayo', 'meringue', 'custard',
                'albumin', 'lecithin'
            ],
            AllergenType.NUTS: [
                'almond', 'walnut', 'pecan', 'cashew', 'pistachio', 'hazelnut',
                'brazil nut', 'macadamia', 'pine nut', 'nut'
            ],
            AllergenType.PEANUTS: [
                'peanut', 'peanuts', 'groundnut', 'arachis'
            ],
            AllergenType.FISH: [
                'salmon', 'tuna', 'cod', 'bass', 'trout', 'anchovy', 'sardine',
                'fish', 'seafood'
            ],
            AllergenType.CRUSTACEANS: [
                'shrimp', 'crab', 'lobster', 'prawn', 'crawfish', 'crayfish'
            ],
            AllergenType.MOLLUSCS: [
                'oyster', 'mussel', 'clam', 'scallop', 'squid', 'octopus'
            ],
            AllergenType.SOYBEANS: [
                'soy', 'soya', 'tofu', 'tempeh', 'miso', 'edamame', 'soybean'
            ],
            AllergenType.SESAME: [
                'sesame', 'tahini', 'sesame seed', 'sesame oil'
            ],
            AllergenType.SULPHITES: [
                'wine', 'dried fruit', 'sulfite', 'sulphite', 'preservative'
            ],
            AllergenType.CELERY: [
                'celery', 'celeriac', 'celery seed'
            ],
            AllergenType.MUSTARD: [
                'mustard', 'mustard seed', 'dijon'
            ],
            AllergenType.LUPIN: [
                'lupin', 'lupine'
            ]
        }
        
        self.dietary_patterns = {
            'vegan': [
                'vegan', 'plant-based', 'no animal products', 'dairy-free',
                'egg-free', 'meat-free'
            ],
            'vegetarian': [
                'vegetarian', 'veggie', 'no meat', 'plant-based'
            ],
            'gluten-free': [
                'gluten-free', 'gluten free', 'gf', 'no gluten', 'celiac safe'
            ],
            'dairy-free': [
                'dairy-free', 'dairy free', 'lactose-free', 'no dairy'
            ],
            'nut-free': [
                'nut-free', 'nut free', 'no nuts', 'allergy-friendly'
            ],
            'keto': [
                'keto', 'ketogenic', 'low-carb', 'high-fat'
            ],
            'paleo': [
                'paleo', 'paleolithic', 'primal'
            ]
        }
        
        # Initialize ML models if available
        self.ner_model = None
        self.classification_model = None
        self.vectorizer = None
        
        if ML_AVAILABLE:
            self._initialize_ml_models()
    
    def _initialize_ml_models(self):
        """Initialize ML models for enhanced extraction"""
        try:
            # Named Entity Recognition for ingredient extraction
            self.ner_model = pipeline(
                "ner", 
                model="dbmdz/bert-large-cased-finetuned-conll03-english",
                aggregation_strategy="simple"
            )
            
            # Text classification for menu item categorization
            self.classification_model = pipeline(
                "text-classification",
                model="cardiffnlp/twitter-roberta-base-sentiment-latest"
            )
            
            # TF-IDF vectorizer for similarity matching
            self.vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 2)
            )
            
            logger.info("ML models initialized successfully")
            
        except Exception as e:
            logger.warning(f"Could not initialize ML models: {e}")
            self.ner_model = None
            self.classification_model = None
    
    def extract_ingredients_with_ner(self, text: str) -> List[str]:
        """Extract ingredients using Named Entity Recognition"""
        if not self.ner_model:
            return self._extract_ingredients_rule_based(text)
        
        try:
            # Use NER to identify potential ingredients
            entities = self.ner_model(text)
            ingredients = []
            
            for entity in entities:
                if entity['entity_group'] in ['MISC', 'ORG'] and entity['score'] > 0.8:
                    ingredient = entity['word'].lower().strip()
                    if len(ingredient) > 2 and ingredient.isalpha():
                        ingredients.append(ingredient)
            
            # Fallback to rule-based if NER doesn't find much
            if len(ingredients) < 2:
                ingredients.extend(self._extract_ingredients_rule_based(text))
            
            return list(set(ingredients))  # Remove duplicates
            
        except Exception as e:
            logger.warning(f"NER extraction failed: {e}")
            return self._extract_ingredients_rule_based(text)
    
    def _extract_ingredients_rule_based(self, text: str) -> List[str]:
        """Fallback rule-based ingredient extraction"""
        # Common food words that might be ingredients
        food_words = [
            'chicken', 'beef', 'pork', 'fish', 'salmon', 'tuna', 'shrimp',
            'cheese', 'tomato', 'onion', 'garlic', 'pepper', 'mushroom',
            'spinach', 'lettuce', 'avocado', 'bacon', 'ham', 'turkey',
            'rice', 'pasta', 'bread', 'potato', 'carrot', 'broccoli'
        ]
        
        text_lower = text.lower()
        found_ingredients = []
        
        for word in food_words:
            if word in text_lower:
                found_ingredients.append(word)
        
        return found_ingredients
    
    def detect_allergens_ml(self, text: str, ingredients: List[str]) -> Tuple[List[AllergenType], Dict[str, float]]:
        """Detect allergens using ML-enhanced keyword matching"""
        detected_allergens = []
        confidence_scores = {}
        
        # Combine text and ingredients for analysis
        analysis_text = f"{text} {' '.join(ingredients)}".lower()
        
        for allergen_type, keywords in self.allergen_keywords.items():
            max_confidence = 0.0
            found_keywords = []
            
            for keyword in keywords:
                if keyword in analysis_text:
                    found_keywords.append(keyword)
                    # Calculate confidence based on keyword specificity and context
                    base_confidence = 0.7
                    
                    # Boost confidence for exact matches
                    if f" {keyword} " in f" {analysis_text} ":
                        base_confidence += 0.2
                    
                    # Boost confidence for multiple keyword matches
                    if len(found_keywords) > 1:
                        base_confidence += 0.1
                    
                    max_confidence = max(max_confidence, base_confidence)
            
            if found_keywords and max_confidence > 0.6:
                detected_allergens.append(allergen_type)
                confidence_scores[allergen_type.value] = min(max_confidence, 0.95)
        
        return detected_allergens, confidence_scores
    
    def detect_dietary_tags(self, text: str) -> List[str]:
        """Detect dietary tags (vegan, gluten-free, etc.)"""
        detected_tags = []
        text_lower = text.lower()
        
        for tag, patterns in self.dietary_patterns.items():
            for pattern in patterns:
                if pattern in text_lower:
                    detected_tags.append(tag)
                    break
        
        return list(set(detected_tags))
    
    def categorize_menu_item_ml(self, name: str, description: str) -> str:
        """Categorize menu item using ML if available, otherwise rule-based"""
        text = f"{name} {description}".lower()
        
        # Rule-based categorization
        category_keywords = {
            'appetizer': ['appetizer', 'starter', 'small plate', 'shareables', 'apps', 'dip'],
            'salad': ['salad', 'greens', 'caesar', 'garden'],
            'soup': ['soup', 'bisque', 'chowder', 'broth'],
            'sandwich': ['sandwich', 'burger', 'wrap', 'panini', 'sub'],
            'pasta': ['pasta', 'spaghetti', 'linguine', 'penne', 'ravioli'],
            'pizza': ['pizza', 'flatbread', 'margherita'],
            'seafood': ['fish', 'salmon', 'tuna', 'shrimp', 'crab', 'lobster'],
            'meat': ['steak', 'beef', 'pork', 'chicken', 'lamb', 'ribs'],
            'dessert': ['dessert', 'cake', 'pie', 'ice cream', 'chocolate', 'sweet'],
            'beverage': ['drink', 'coffee', 'tea', 'juice', 'soda', 'beer', 'wine']
        }
        
        for category, keywords in category_keywords.items():
            if any(keyword in text for keyword in keywords):
                return category
        
        return 'entree'  # Default category
    
    def calculate_ml_confidence(self, item_data: Dict[str, Any]) -> float:
        """Calculate overall confidence score for ML-enhanced extraction"""
        base_confidence = item_data.get('confidence', 0.5)
        
        # Boost confidence for items with allergen detection
        if item_data.get('allergens'):
            base_confidence += 0.1
        
        # Boost confidence for items with dietary tags
        if item_data.get('dietary_tags'):
            base_confidence += 0.1
        
        # Boost confidence for items with price
        if item_data.get('price'):
            base_confidence += 0.1
        
        # Boost confidence for items with description
        if item_data.get('description') and len(item_data['description']) > 10:
            base_confidence += 0.1
        
        return min(base_confidence, 0.95)

class MLEnhancedMenuScraper:
    """Main scraper class with ML enhancement capabilities"""
    
    def __init__(self):
        self.ml_extractor = MLMenuExtractor()
        self.menu_keywords = [
            'menu', 'food', 'dining', 'cuisine', 'dishes', 'entrees', 'appetizers',
            'desserts', 'beverages', 'drinks', 'specials', 'breakfast', 'lunch',
            'dinner', 'brunch', 'takeout', 'delivery', 'order'
        ]
        
        self.price_patterns = [
            r'\$\d+(?:\.\d{2})?',
            r'\d+(?:\.\d{2})?\s*(?:dollars?|usd|\$)',
            r'\b\d{1,3}(?:,\d{3})*(?:\.\d{2})?\b',
        ]
    
    def extract_menu_items_with_ml(self, page: Page) -> List[MenuItemML]:
        """Extract menu items with ML enhancement"""
        items = []
        
        try:
            # Enhanced CSS selectors for menu items
            menu_selectors = [
                '.menu-item, .menuitem, .menu_item',
                '.food-item, .fooditem, .food_item',
                '.dish, .dish-item, .dish_item',
                '.product, .product-item',
                '[class*="menu"][class*="item"]',
                '[class*="food"][class*="item"]',
                '.menu ul li, .menu ol li',
                '.food-menu li, .restaurant-menu li'
            ]
            
            for selector in menu_selectors:
                try:
                    elements = page.query_selector_all(selector)
                    
                    for element in elements[:30]:  # Limit to prevent overload
                        try:
                            item = self._extract_ml_item_from_element(element)
                            if item and self._is_valid_ml_menu_item(item):
                                items.append(item)
                        except Exception as e:
                            continue
                    
                    if len(items) >= 15:  # Stop if we have enough items
                        break
                        
                except Exception as e:
                    continue
            
            return items
            
        except Exception as e:
            logger.warning(f"Error extracting ML menu items: {e}")
            return []
    
    def _extract_ml_item_from_element(self, element) -> Optional[MenuItemML]:
        """Extract menu item with ML enhancement from DOM element"""
        try:
            # Get text content
            text = element.inner_text().strip()
            if not text or len(text) < 3:
                return None
            
            # Parse basic information
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            if not lines:
                return None
            
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
            
            # Clean up name (remove price if included)
            name = re.sub(r'\$\d+(?:\.\d{2})?', '', name).strip()
            
            if len(name) < 2:
                return None
            
            # ML Enhancement
            full_text = f"{name} {description}"
            
            # Extract ingredients using ML
            ingredients = self.ml_extractor.extract_ingredients_with_ner(full_text)
            
            # Detect allergens
            allergens, allergen_confidence = self.ml_extractor.detect_allergens_ml(full_text, ingredients)
            
            # Detect dietary tags
            dietary_tags = self.ml_extractor.detect_dietary_tags(full_text)
            
            # Categorize item
            category = self.ml_extractor.categorize_menu_item_ml(name, description)
            
            # Calculate confidence
            item_data = {
                'confidence': 0.7,
                'allergens': allergens,
                'dietary_tags': dietary_tags,
                'price': price,
                'description': description
            }
            confidence_score = self.ml_extractor.calculate_ml_confidence(item_data)
            
            return MenuItemML(
                name=name,
                description=description,
                price=price,
                category=category,
                allergens=allergens,
                allergen_confidence=allergen_confidence,
                nutritional_info={},  # Could be enhanced with nutrition API
                dietary_tags=dietary_tags,
                confidence_score=confidence_score,
                extraction_method='ml_enhanced',
                ml_enhanced=True
            )
            
        except Exception as e:
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
    
    def _is_valid_ml_menu_item(self, item: MenuItemML) -> bool:
        """Validate ML-enhanced menu item"""
        # Skip items with very low confidence
        if item.confidence_score < 0.4:
            return False
        
        # Skip very short names
        if len(item.name.strip()) < 3:
            return False
        
        # Skip navigation items
        nav_words = ['home', 'about', 'contact', 'menu', 'location', 'hours']
        if any(word in item.name.lower() for word in nav_words):
            return False
        
        return True
    
    def ml_enhanced_detection(self, page: Page, url: str) -> Dict[str, Any]:
        """Main ML-enhanced menu detection method"""
        start_time = time.time()
        
        result = {
            'menu_items': [],
            'total_items': 0,
            'scraping_success': False,
            'ml_enhanced': True,
            'allergen_detection_enabled': True,
            'dietary_tags_detected': [],
            'allergen_summary': {},
            'source': 'ml_enhanced_scraping',
            'processing_time': 0,
            'confidence_score': 0.0,
            'ml_features_used': []
        }
        
        try:
            logger.info(f"Starting ML-enhanced menu detection for: {url}")
            
            # Navigate to URL
            try:
                page.goto(url, wait_until='networkidle', timeout=25000)
                time.sleep(2)
            except Exception as e:
                result['error'] = f"Navigation failed: {str(e)}"
                return result
            
            # Extract menu items with ML
            ml_items = self.extract_menu_items_with_ml(page)
            
            if ml_items:
                result['ml_features_used'].append('ml_extraction')
                result['ml_features_used'].append('allergen_detection')
                result['ml_features_used'].append('dietary_tag_detection')
                
                # Convert ML items to serializable format
                serializable_items = []
                all_allergens = set()
                all_dietary_tags = set()
                total_confidence = 0
                
                for item in ml_items:
                    # Collect allergen and dietary information
                    for allergen in item.allergens:
                        all_allergens.add(allergen.value)
                    
                    all_dietary_tags.update(item.dietary_tags)
                    total_confidence += item.confidence_score
                    
                    # Convert to serializable format
                    serializable_items.append({
                        'name': item.name,
                        'description': item.description,
                        'price': item.price,
                        'category': item.category,
                        'allergens': [a.value for a in item.allergens],
                        'allergen_confidence': item.allergen_confidence,
                        'dietary_tags': item.dietary_tags,
                        'confidence': item.confidence_score,
                        'extraction_method': item.extraction_method,
                        'ml_enhanced': item.ml_enhanced
                    })
                
                result['menu_items'] = serializable_items
                result['total_items'] = len(serializable_items)
                result['scraping_success'] = len(serializable_items) >= 3
                result['dietary_tags_detected'] = list(all_dietary_tags)
                result['allergen_summary'] = {allergen: 0 for allergen in all_allergens}
                
                # Count allergen occurrences
                for item in serializable_items:
                    for allergen in item['allergens']:
                        if allergen in result['allergen_summary']:
                            result['allergen_summary'][allergen] += 1
                
                # Calculate overall confidence
                if ml_items:
                    result['confidence_score'] = round(total_confidence / len(ml_items), 3)
            
            result['processing_time'] = round(time.time() - start_time, 2)
            
            logger.info(f"ML-enhanced detection completed: {len(ml_items)} items found")
            return result
            
        except Exception as e:
            result['error'] = str(e)
            result['processing_time'] = round(time.time() - start_time, 2)
            logger.error(f"ML-enhanced detection failed: {e}")
            return result

class ComprehensiveMenuProcessor:
    """Comprehensive menu processing for merged restaurant data"""
    
    def __init__(self):
        self.session = None
        self.ml_extractor = MLMenuExtractor()
        
        # Enhanced selectors for menu detection
        self.menu_selectors = [
            '.menu', '.menu-items', '.food-menu', '.restaurant-menu',
            '[class*="menu"]', '[id*="menu"]', '.menu-section',
            '.menu-category', '.dish', '.food-item', '.menu-item'
        ]
        
        self.price_patterns = [
            r'\$\d+\.\d{2}',  # $12.99
            r'\$\d+',         # $12
            r'\d+\.\d{2}',    # 12.99
            r'\d+\s*dollars?', # 12 dollars
        ]
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def extract_price(self, text: str) -> Optional[str]:
        """Extract price from text using regex patterns"""
        for pattern in self.price_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                price = match.group()
                if not price.startswith('$'):
                    if 'dollar' in price.lower():
                        price = '$' + re.search(r'\d+', price).group()
                    else:
                        price = '$' + price
                return price
        return None
    
    def extract_menu_items_from_html(self, html: str, url: str) -> List[Dict[str, Any]]:
        """Extract menu items from HTML content using ML-enhanced parsing"""
        soup = BeautifulSoup(html, 'html.parser')
        menu_items = []
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Try different menu extraction strategies
        strategies = [
            self._extract_structured_menu,
            self._extract_list_based_menu,
            self._extract_text_based_menu
        ]
        
        for strategy in strategies:
            items = strategy(soup)
            if items:
                menu_items.extend(items)
                break
        
        # Deduplicate and filter items
        unique_items = self._deduplicate_menu_items(menu_items)
        filtered_items = [item for item in unique_items if item.get('confidence_score', 0) >= 0.4]
        
        return filtered_items
    
    def _extract_structured_menu(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract menu items from structured HTML"""
        items = []
        
        for selector in self.menu_selectors:
            menu_elements = soup.select(selector)
            
            for menu_element in menu_elements:
                item_containers = menu_element.find_all(['div', 'li', 'tr'], 
                                                       class_=re.compile(r'(item|dish|food)', re.I))
                
                for container in item_containers:
                    item = self._extract_item_from_container(container)
                    if item:
                        items.append(item)
        
        return items
    
    def _extract_list_based_menu(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract menu items from list-based structures"""
        items = []
        
        lists = soup.find_all(['ul', 'ol', 'dl'])
        
        for list_element in lists:
            list_items = list_element.find_all('li')
            
            # Check if this looks like a menu
            menu_indicators = 0
            for li in list_items[:5]:
                text = li.get_text()
                if any(pattern in text for pattern in ['$', 'price', 'menu']):
                    menu_indicators += 1
            
            if menu_indicators >= 2:
                for li in list_items:
                    item = self._extract_item_from_container(li)
                    if item:
                        items.append(item)
        
        return items
    
    def _extract_text_based_menu(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract menu items from plain text using pattern matching"""
        items = []
        
        text_content = soup.get_text()
        lines = text_content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            price = self.extract_price(line)
            if price:
                name_match = re.search(r'^(.+?)\s*\$', line)
                if name_match:
                    name = name_match.group(1).strip()
                    
                    desc_match = re.search(r'\$[\d.]+\s*(.+)$', line)
                    description = desc_match.group(1).strip() if desc_match else ""
                    
                    if name and len(name) > 2:
                        item_data = {
                            'name': name,
                            'price': price,
                            'description': description
                        }
                        
                        item = self._create_menu_item(item_data)
                        if item:
                            items.append(item)
        
        return items
    
    def _extract_item_from_container(self, container) -> Optional[Dict[str, Any]]:
        """Extract menu item data from a container element"""
        text = container.get_text(separator=' ', strip=True)
        
        if not text or len(text) < 3:
            return None
        
        price = self.extract_price(text)
        
        name_element = container.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'strong', 'b']) or \
                      container.find(class_=re.compile(r'(name|title|dish)', re.I))
        
        if name_element:
            name = name_element.get_text(strip=True)
        else:
            parts = text.split('.')
            if parts:
                name = parts[0].strip()
        
        desc_element = container.find(class_=re.compile(r'(desc|description|detail)', re.I))
        if desc_element:
            description = desc_element.get_text(strip=True)
        else:
            remaining_text = text.replace(name, '').replace(price or '', '').strip()
            description = remaining_text if remaining_text else ""
        
        if name:
            item_data = {
                'name': name,
                'price': price,
                'description': description
            }
            
            return self._create_menu_item(item_data)
        
        return None
    
    def _create_menu_item(self, item_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create menu item with ML enhancement"""
        name = item_data.get('name', '').strip()
        price = item_data.get('price')
        description = item_data.get('description', '').strip()
        
        if not name or len(name) < 2:
            return None
        
        # ML Enhancement
        full_text = f"{name} {description}"
        
        # Extract ingredients using ML
        ingredients = self.ml_extractor.extract_ingredients_with_ner(full_text)
        
        # Detect allergens
        allergens, allergen_confidence = self.ml_extractor.detect_allergens_ml(full_text, ingredients)
        
        # Detect dietary tags
        dietary_tags = self.ml_extractor.detect_dietary_tags(full_text)
        
        # Categorize item
        category = self.ml_extractor.categorize_menu_item_ml(name, description)
        
        # Calculate confidence
        confidence_data = {
            'confidence': 0.7,
            'allergens': allergens,
            'dietary_tags': dietary_tags,
            'price': price,
            'description': description
        }
        confidence_score = self.ml_extractor.calculate_ml_confidence(confidence_data)
        
        return {
            'name': name,
            'price': price,
            'description': description,
            'category': category,
            'allergens': [a.value for a in allergens],
            'allergen_confidence': allergen_confidence,
            'dietary_tags': dietary_tags,
            'confidence_score': confidence_score,
            'extraction_method': 'ml_enhanced_async',
            'ml_enhanced': True
        }
    
    def _deduplicate_menu_items(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate menu items"""
        seen_names = set()
        unique_items = []
        
        for item in items:
            name_normalized = item['name'].lower().strip()
            if name_normalized not in seen_names:
                seen_names.add(name_normalized)
                unique_items.append(item)
        
        return unique_items
    
    async def scrape_restaurant_menu(self, restaurant: Dict[str, Any]) -> Dict[str, Any]:
        """Scrape menu for a single restaurant with ML enhancement"""
        start_time = time.time()
        
        restaurant_id = restaurant.get('id', 'unknown')
        restaurant_name = restaurant.get('name', 'Unknown Restaurant')
        website_url = restaurant.get('website') or restaurant.get('url')
        
        result = {
            'restaurant_id': restaurant_id,
            'restaurant_name': restaurant_name,
            'website_url': website_url or "",
            'extraction_timestamp': datetime.now().isoformat(),
            'success': False,
            'menu_items': [],
            'categories': [],
            'extraction_method': 'ml_enhanced_async',
            'processing_time': 0.0,
            'error_message': None,
            'ml_features_used': [],
            'allergen_summary': {},
            'dietary_tags_detected': []
        }
        
        if not website_url:
            result['error_message'] = "No website URL available"
            result['processing_time'] = round(time.time() - start_time, 2)
            return result
        
        try:
            async with self.session.get(website_url) as response:
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}: {response.reason}")
                
                html_content = await response.text()
            
            # Extract menu items with ML
            menu_items = self.extract_menu_items_from_html(html_content, website_url)
            
            if menu_items:
                result['ml_features_used'] = [
                    'ml_extraction', 'allergen_detection', 
                    'dietary_tag_detection', 'automatic_categorization'
                ]
                
                # Collect statistics
                all_allergens = set()
                all_dietary_tags = set()
                categories = set()
                
                for item in menu_items:
                    all_allergens.update(item.get('allergens', []))
                    all_dietary_tags.update(item.get('dietary_tags', []))
                    if item.get('category'):
                        categories.add(item['category'])
                
                result['menu_items'] = menu_items
                result['categories'] = list(categories)
                result['success'] = len(menu_items) >= 3
                result['dietary_tags_detected'] = list(all_dietary_tags)
                result['allergen_summary'] = {allergen: 0 for allergen in all_allergens}
                
                # Count allergen occurrences
                for item in menu_items:
                    for allergen in item.get('allergens', []):
                        if allergen in result['allergen_summary']:
                            result['allergen_summary'][allergen] += 1
            
            result['processing_time'] = round(time.time() - start_time, 2)
            
        except Exception as e:
            result['error_message'] = str(e)
            result['processing_time'] = round(time.time() - start_time, 2)
        
        return result
    
    async def process_merged_restaurants(self, merged_data_file: str, 
                                       max_concurrent: int = 5) -> Dict[str, Any]:
        """Process merged restaurant data for comprehensive menu extraction"""
        print("🤖 Starting ML-Enhanced Menu Processing for Merged Data")
        
        # Load merged restaurant data
        try:
            with open(merged_data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            restaurants = data.get('restaurants', [])
            print(f"📊 Loaded {len(restaurants)} restaurants from merged data")
            
        except Exception as e:
            print(f"❌ Error loading merged data: {e}")
            return {'error': str(e)}
        
        # Filter restaurants with websites
        restaurants_with_websites = [
            r for r in restaurants 
            if r.get('website') or r.get('url')
        ]
        
        print(f"🌐 Found {len(restaurants_with_websites)} restaurants with websites")
        
        # Process restaurants with concurrency control
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_with_semaphore(restaurant):
            async with semaphore:
                return await self.scrape_restaurant_menu(restaurant)
        
        print(f"🔄 Processing menus with {max_concurrent} concurrent requests...")
        start_time = time.time()
        
        tasks = [process_with_semaphore(r) for r in restaurants_with_websites[:50]]  # Limit for demo
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter valid results
        valid_results = []
        for result in results:
            if isinstance(result, dict) and not isinstance(result, Exception):
                valid_results.append(result)
            else:
                logger.error(f"Exception in menu processing: {result}")
        
        processing_time = round(time.time() - start_time, 2)
        
        # Calculate comprehensive statistics
        successful_extractions = [r for r in valid_results if r.get('success')]
        total_menu_items = sum(len(r.get('menu_items', [])) for r in successful_extractions)
        
        all_allergens = set()
        all_dietary_tags = set()
        all_categories = set()
        
        for result in successful_extractions:
            all_allergens.update(result.get('allergen_summary', {}).keys())
            all_dietary_tags.update(result.get('dietary_tags_detected', []))
            all_categories.update(result.get('categories', []))
        
        comprehensive_stats = {
            'total_restaurants_processed': len(valid_results),
            'successful_menu_extractions': len(successful_extractions),
            'failed_extractions': len(valid_results) - len(successful_extractions),
            'success_rate': round(len(successful_extractions) / len(valid_results) * 100, 1) if valid_results else 0,
            'total_menu_items_extracted': total_menu_items,
            'average_items_per_restaurant': round(total_menu_items / len(successful_extractions), 1) if successful_extractions else 0,
            'unique_allergens_detected': list(all_allergens),
            'unique_dietary_tags_detected': list(all_dietary_tags),
            'unique_categories_detected': list(all_categories),
            'processing_time_seconds': processing_time,
            'processing_timestamp': datetime.now().isoformat()
        }
        
        # Save comprehensive results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"output/chicago_comprehensive_menus_{timestamp}.json"
        
        comprehensive_data = {
            'processing_info': {
                'timestamp': datetime.now().isoformat(),
                'source_file': merged_data_file,
                'processing_method': 'ml_enhanced_comprehensive',
                'ml_features': [
                    'intelligent_html_parsing',
                    'allergen_detection',
                    'dietary_tag_extraction',
                    'automatic_categorization',
                    'confidence_scoring',
                    'concurrent_processing'
                ]
            },
            'statistics': comprehensive_stats,
            'results': valid_results
        }
        
        # Create output directory
        import os
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(comprehensive_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n🎉 Comprehensive Menu Processing Completed!")
        print(f"📊 Processed: {comprehensive_stats['successful_menu_extractions']}/{comprehensive_stats['total_restaurants_processed']} restaurants")
        print(f"🍽️ Total menu items: {comprehensive_stats['total_menu_items_extracted']}")
        print(f"🏷️ Allergens detected: {len(comprehensive_stats['unique_allergens_detected'])}")
        print(f"🥗 Dietary tags: {len(comprehensive_stats['unique_dietary_tags_detected'])}")
        print(f"⏱️ Processing time: {comprehensive_stats['processing_time_seconds']} seconds")
        print(f"💾 Results saved to: {output_file}")
        
        return {
            'output_file': output_file,
            'statistics': comprehensive_stats,
            'success': True
        }

async def main():
    """Main execution function for comprehensive menu processing"""
    print("🚀 Starting Comprehensive Restaurant Data Processing Pipeline")
    
    # Find the most recent merged data file
    print("\n📊 Step 1: Locating Merged Data...")
    output_dir = Path('output')
    merged_files = list(output_dir.glob('chicago_restaurants_merged_*.json'))
    
    if not merged_files:
        print("❌ No merged data files found. Please run comprehensive_data_merger.py first.")
        return
    
    merged_file = max(merged_files, key=lambda x: x.stat().st_mtime)
    print(f"✅ Using merged data: {merged_file}")
    
    # Process menus with ML enhancement
    print("\n🤖 Step 2: Running ML-Enhanced Menu Processing...")
    async with ComprehensiveMenuProcessor() as processor:
        menu_result = await processor.process_merged_restaurants(str(merged_file))
        
        if menu_result.get('success'):
            print(f"\n🎉 Complete Pipeline Success!")
            print(f"📁 Final output: {menu_result.get('output_file')}")
            return menu_result
        else:
            print(f"❌ Menu processing failed: {menu_result.get('error')}")
            return menu_result

async def run_data_merger():
    """Run the data merger as part of the pipeline"""
    try:
        # Import and run the comprehensive data merger
        import subprocess
        import sys
        
        result = subprocess.run(
            [sys.executable, 'comprehensive_data_merger.py'],
            capture_output=True,
            text=True,
            cwd=Path.cwd()
        )
        
        if result.returncode == 0:
            # Find the most recent merged file
            output_dir = Path('output')
            merged_files = list(output_dir.glob('chicago_restaurants_merged_*.json'))
            
            if merged_files:
                latest_file = max(merged_files, key=lambda x: x.stat().st_mtime)
                return {
                    'success': True,
                    'output_file': str(latest_file)
                }
        
        return {'success': False, 'error': 'Data merger execution failed'}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

if __name__ == "__main__":
    # Run the comprehensive pipeline
    asyncio.run(main())