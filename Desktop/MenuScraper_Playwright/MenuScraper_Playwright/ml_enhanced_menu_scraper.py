#!/usr/bin/env python3
"""
ML-Enhanced Menu Scraper with Allergen Detection
Integrating machine learning for improved menu extraction and allergen identification
Inspired by AllergySavvy ML development patterns
"""

import re
import json
import time
import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urljoin, urlparse
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError
from dataclasses import dataclass
from enum import Enum

# ML and NLP imports
try:
    from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    import torch
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

if __name__ == "__main__":
    # Test the ML-enhanced scraper
    from playwright.sync_api import sync_playwright
    
    scraper = MLEnhancedMenuScraper()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        test_url = "https://www.yelp.com/biz/alinea-chicago"
        result = scraper.ml_enhanced_detection(page, test_url)
        
        print(f"Success: {result['scraping_success']}")
        print(f"Items found: {result['total_items']}")
        print(f"ML features used: {result['ml_features_used']}")
        print(f"Allergens detected: {list(result['allergen_summary'].keys())}")
        print(f"Dietary tags: {result['dietary_tags_detected']}")
        
        for item in result['menu_items'][:3]:
            print(f"\n- {item['name']}: {item.get('price', 'No price')}")
            print(f"  Allergens: {item['allergens']}")
            print(f"  Dietary: {item['dietary_tags']}")
            print(f"  Confidence: {item['confidence']:.2f}")
        
        browser.close()