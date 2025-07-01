#!/usr/bin/env python3
"""
Enhanced Allergen Analyzer & Menu Data Enhancement System
Builds upon existing Chicago restaurant data to provide comprehensive allergen analysis
and enhanced menu data extraction with health-focused features
"""

import json
import re
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import asyncio
from urllib.parse import urljoin, urlparse

try:
    from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeoutError
except ImportError:
    print("❌ Playwright not installed. Run: pip install playwright")
    exit(1)

class AllergenType(Enum):
    """Comprehensive allergen classification based on FDA and EU regulations"""
    # Major allergens (FDA Top 9)
    MILK = "milk"
    EGGS = "eggs"
    FISH = "fish"
    SHELLFISH = "shellfish"
    TREE_NUTS = "tree_nuts"
    PEANUTS = "peanuts"
    WHEAT = "wheat"
    SOYBEANS = "soybeans"
    SESAME = "sesame"
    
    # Additional common allergens
    GLUTEN = "gluten"
    SULFITES = "sulfites"
    CELERY = "celery"
    MUSTARD = "mustard"
    LUPIN = "lupin"
    MOLLUSCS = "molluscs"

class DietaryTag(Enum):
    """Dietary restriction and preference tags"""
    VEGETARIAN = "vegetarian"
    VEGAN = "vegan"
    GLUTEN_FREE = "gluten_free"
    DAIRY_FREE = "dairy_free"
    NUT_FREE = "nut_free"
    KETO = "keto"
    PALEO = "paleo"
    LOW_CARB = "low_carb"
    LOW_SODIUM = "low_sodium"
    ORGANIC = "organic"
    HALAL = "halal"
    KOSHER = "kosher"
    SPICY = "spicy"
    HEALTHY = "healthy"

@dataclass
class AllergenAnalysis:
    """Detailed allergen analysis for a menu item"""
    detected_allergens: List[AllergenType]
    confidence_scores: Dict[str, float]
    dietary_tags: List[DietaryTag]
    risk_level: str  # "high", "medium", "low", "unknown"
    analysis_method: str
    warnings: List[str]
    safe_for_allergies: List[AllergenType]

@dataclass
class EnhancedMenuItem:
    """Enhanced menu item with comprehensive allergen and dietary information"""
    name: str
    description: str
    price: Optional[str]
    category: str
    allergen_analysis: AllergenAnalysis
    nutritional_hints: Dict[str, Any]
    ingredients_detected: List[str]
    preparation_methods: List[str]
    confidence_score: float
    source_url: Optional[str]

class AdvancedAllergenDetector:
    """Advanced allergen detection system with ML-inspired pattern matching"""
    
    def __init__(self):
        # Comprehensive allergen keyword database with confidence weights
        self.allergen_database = {
            AllergenType.MILK: {
                'primary': {
                    'milk': 1.0, 'dairy': 1.0, 'lactose': 1.0, 'casein': 1.0, 'whey': 1.0,
                    'cheese': 0.9, 'butter': 0.9, 'cream': 0.9, 'yogurt': 0.9
                },
                'secondary': {
                    'mozzarella': 0.8, 'parmesan': 0.8, 'cheddar': 0.8, 'brie': 0.8,
                    'feta': 0.8, 'ricotta': 0.8, 'mascarpone': 0.8, 'goat cheese': 0.8,
                    'ice cream': 0.7, 'gelato': 0.7, 'custard': 0.7, 'pudding': 0.6
                },
                'dishes': {
                    'alfredo': 0.9, 'carbonara': 0.9, 'mac and cheese': 1.0,
                    'cheeseburger': 0.8, 'pizza': 0.7, 'lasagna': 0.8
                }
            },
            AllergenType.EGGS: {
                'primary': {
                    'egg': 1.0, 'eggs': 1.0, 'albumin': 1.0, 'lecithin': 0.8
                },
                'secondary': {
                    'mayonnaise': 0.9, 'mayo': 0.9, 'aioli': 0.8, 'hollandaise': 0.9,
                    'custard': 0.7, 'meringue': 1.0, 'eggnog': 1.0
                },
                'dishes': {
                    'omelet': 1.0, 'frittata': 1.0, 'quiche': 1.0, 'carbonara': 0.9,
                    'caesar salad': 0.6, 'fried rice': 0.5
                }
            },
            AllergenType.WHEAT: {
                'primary': {
                    'wheat': 1.0, 'flour': 0.9, 'gluten': 1.0, 'semolina': 1.0,
                    'bulgur': 1.0, 'couscous': 1.0, 'farro': 1.0, 'spelt': 1.0
                },
                'secondary': {
                    'bread': 0.9, 'pasta': 0.9, 'noodles': 0.8, 'pizza': 0.8,
                    'sandwich': 0.8, 'burger': 0.7, 'wrap': 0.6
                },
                'dishes': {
                    'spaghetti': 0.9, 'linguine': 0.9, 'penne': 0.9, 'ravioli': 0.9,
                    'gnocchi': 0.7, 'dumplings': 0.8, 'tempura': 0.8
                }
            },
            AllergenType.TREE_NUTS: {
                'primary': {
                    'almond': 1.0, 'walnut': 1.0, 'pecan': 1.0, 'cashew': 1.0,
                    'pistachio': 1.0, 'hazelnut': 1.0, 'macadamia': 1.0, 'brazil nut': 1.0,
                    'pine nut': 1.0, 'tree nuts': 1.0
                },
                'secondary': {
                    'marzipan': 0.9, 'nougat': 0.8, 'praline': 0.8, 'amaretto': 0.7
                },
                'dishes': {
                    'pesto': 0.8, 'baklava': 0.9, 'pecan pie': 1.0, 'almond cake': 1.0
                }
            },
            AllergenType.PEANUTS: {
                'primary': {
                    'peanut': 1.0, 'peanuts': 1.0, 'groundnut': 1.0, 'arachis': 1.0
                },
                'secondary': {
                    'peanut butter': 1.0, 'peanut oil': 0.8, 'peanut sauce': 1.0
                },
                'dishes': {
                    'satay': 0.9, 'pad thai': 0.7, 'kung pao': 0.8, 'african stew': 0.6
                }
            },
            AllergenType.FISH: {
                'primary': {
                    'fish': 1.0, 'salmon': 1.0, 'tuna': 1.0, 'cod': 1.0, 'halibut': 1.0,
                    'trout': 1.0, 'bass': 1.0, 'anchovy': 1.0, 'sardine': 1.0, 'mackerel': 1.0
                },
                'secondary': {
                    'worcestershire': 0.6, 'caesar dressing': 0.5
                },
                'dishes': {
                    'sushi': 0.9, 'sashimi': 1.0, 'fish and chips': 1.0, 'ceviche': 1.0,
                    'bouillabaisse': 0.9, 'fish tacos': 1.0
                }
            },
            AllergenType.SHELLFISH: {
                'primary': {
                    'shrimp': 1.0, 'crab': 1.0, 'lobster': 1.0, 'prawns': 1.0,
                    'crayfish': 1.0, 'scallops': 1.0, 'mussels': 1.0, 'clams': 1.0,
                    'oysters': 1.0, 'shellfish': 1.0
                },
                'secondary': {
                    'seafood': 0.7, 'crustacean': 1.0, 'mollusk': 1.0
                },
                'dishes': {
                    'paella': 0.8, 'jambalaya': 0.7, 'bisque': 0.9, 'cioppino': 0.9,
                    'shrimp scampi': 1.0, 'crab cakes': 1.0
                }
            },
            AllergenType.SOYBEANS: {
                'primary': {
                    'soy': 1.0, 'soya': 1.0, 'soybean': 1.0, 'tofu': 1.0, 'tempeh': 1.0,
                    'miso': 1.0, 'edamame': 1.0
                },
                'secondary': {
                    'soy sauce': 1.0, 'tamari': 1.0, 'teriyaki': 0.8, 'hoisin': 0.7
                },
                'dishes': {
                    'miso soup': 1.0, 'teriyaki': 0.8, 'asian stir fry': 0.6
                }
            },
            AllergenType.SESAME: {
                'primary': {
                    'sesame': 1.0, 'tahini': 1.0, 'sesame oil': 1.0, 'sesame seed': 1.0
                },
                'secondary': {
                    'hummus': 0.7, 'halva': 0.9, 'za\'atar': 0.6
                },
                'dishes': {
                    'everything bagel': 0.8, 'sesame chicken': 0.8, 'middle eastern': 0.5
                }
            }
        }
        
        # Dietary tag patterns with confidence scoring
        self.dietary_patterns = {
            DietaryTag.VEGETARIAN: {
                'positive': [r'\bvegetarian\b', r'\bveggie\b', r'\bplant.based\b', r'\bmeatless\b'],
                'negative': [r'\bmeat\b', r'\bbeef\b', r'\bpork\b', r'\bchicken\b', r'\bfish\b'],
                'weight': 1.0
            },
            DietaryTag.VEGAN: {
                'positive': [r'\bvegan\b', r'\bplant.based\b', r'\bdairy.free\b'],
                'negative': [r'\bmeat\b', r'\bdairy\b', r'\begg\b', r'\bhoney\b'],
                'weight': 1.0
            },
            DietaryTag.GLUTEN_FREE: {
                'positive': [r'\bgluten.free\b', r'\bgf\b', r'\bceliac.friendly\b'],
                'negative': [r'\bwheat\b', r'\bgluten\b', r'\bbread\b', r'\bpasta\b'],
                'weight': 1.0
            },
            DietaryTag.KETO: {
                'positive': [r'\bketo\b', r'\bketogenic\b', r'\blow.carb\b'],
                'negative': [r'\bbread\b', r'\bpasta\b', r'\brice\b', r'\bpotato\b'],
                'weight': 0.8
            },
            DietaryTag.SPICY: {
                'positive': [r'\bspicy\b', r'\bhot\b', r'\bjalapeño\b', r'\bhabanero\b', r'\bsriracha\b', r'\bchili\b'],
                'negative': [],
                'weight': 0.9
            }
        }
        
        # Preparation method detection
        self.preparation_methods = {
            'fried': [r'\bfried\b', r'\bdeep.fried\b', r'\bpan.fried\b', r'\btempura\b'],
            'grilled': [r'\bgrilled\b', r'\bbbq\b', r'\bbarbecue\b', r'\bcharred\b'],
            'baked': [r'\bbaked\b', r'\broasted\b', r'\boven.baked\b'],
            'steamed': [r'\bsteamed\b', r'\bsteam\b'],
            'sautéed': [r'\bsautéed\b', r'\bsauteed\b', r'\bpan.seared\b'],
            'raw': [r'\braw\b', r'\bsashimi\b', r'\bceviche\b', r'\btartare\b']
        }
    
    def analyze_allergens(self, text: str, item_name: str = "") -> AllergenAnalysis:
        """Comprehensive allergen analysis with confidence scoring"""
        text_lower = text.lower()
        name_lower = item_name.lower()
        combined_text = f"{name_lower} {text_lower}"
        
        detected_allergens = []
        confidence_scores = {}
        warnings = []
        
        # Analyze each allergen type
        for allergen_type, patterns in self.allergen_database.items():
            max_confidence = 0.0
            detection_reasons = []
            
            # Check primary keywords
            for keyword, weight in patterns['primary'].items():
                if keyword in combined_text:
                    confidence = weight * 0.9  # Primary keywords get high confidence
                    max_confidence = max(max_confidence, confidence)
                    detection_reasons.append(f"Primary: {keyword}")
            
            # Check secondary keywords
            for keyword, weight in patterns['secondary'].items():
                if keyword in combined_text:
                    confidence = weight * 0.7  # Secondary keywords get medium confidence
                    max_confidence = max(max_confidence, confidence)
                    detection_reasons.append(f"Secondary: {keyword}")
            
            # Check dish-based detection
            for keyword, weight in patterns['dishes'].items():
                if keyword in combined_text:
                    confidence = weight * 0.6  # Dish-based gets lower confidence
                    max_confidence = max(max_confidence, confidence)
                    detection_reasons.append(f"Dish: {keyword}")
            
            # Store results if confidence threshold met
            if max_confidence > 0.3:  # Confidence threshold
                detected_allergens.append(allergen_type)
                confidence_scores[allergen_type.value] = max_confidence
                
                if max_confidence < 0.6:
                    warnings.append(f"Low confidence detection for {allergen_type.value}: {', '.join(detection_reasons)}")
        
        # Detect dietary tags
        dietary_tags = self._detect_dietary_tags(combined_text)
        
        # Determine risk level
        risk_level = self._calculate_risk_level(detected_allergens, confidence_scores)
        
        # Determine safe allergens (those explicitly marked as free)
        safe_for_allergies = self._detect_allergen_free_claims(combined_text)
        
        return AllergenAnalysis(
            detected_allergens=detected_allergens,
            confidence_scores=confidence_scores,
            dietary_tags=dietary_tags,
            risk_level=risk_level,
            analysis_method="advanced_pattern_matching",
            warnings=warnings,
            safe_for_allergies=safe_for_allergies
        )
    
    def _detect_dietary_tags(self, text: str) -> List[DietaryTag]:
        """Detect dietary tags with pattern matching"""
        detected_tags = []
        
        for tag, patterns in self.dietary_patterns.items():
            positive_score = 0
            negative_score = 0
            
            # Check positive patterns
            for pattern in patterns['positive']:
                if re.search(pattern, text, re.IGNORECASE):
                    positive_score += 1
            
            # Check negative patterns
            for pattern in patterns['negative']:
                if re.search(pattern, text, re.IGNORECASE):
                    negative_score += 1
            
            # Decide based on scores
            if positive_score > 0 and negative_score == 0:
                detected_tags.append(tag)
            elif positive_score > negative_score:
                detected_tags.append(tag)
        
        return detected_tags
    
    def _detect_allergen_free_claims(self, text: str) -> List[AllergenType]:
        """Detect explicit allergen-free claims"""
        safe_allergens = []
        
        free_patterns = {
            AllergenType.GLUTEN: [r'gluten.free', r'\bgf\b', r'celiac.friendly'],
            AllergenType.MILK: [r'dairy.free', r'lactose.free', r'milk.free'],
            AllergenType.TREE_NUTS: [r'nut.free', r'tree.nut.free'],
            AllergenType.PEANUTS: [r'peanut.free'],
            AllergenType.EGGS: [r'egg.free'],
            AllergenType.SOYBEANS: [r'soy.free'],
            AllergenType.FISH: [r'fish.free'],
            AllergenType.SHELLFISH: [r'shellfish.free']
        }
        
        for allergen, patterns in free_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    safe_allergens.append(allergen)
                    break
        
        return safe_allergens
    
    def _calculate_risk_level(self, allergens: List[AllergenType], confidence_scores: Dict[str, float]) -> str:
        """Calculate overall allergen risk level"""
        if not allergens:
            return "low"
        
        high_confidence_allergens = [a for a in allergens if confidence_scores.get(a.value, 0) > 0.8]
        medium_confidence_allergens = [a for a in allergens if 0.5 < confidence_scores.get(a.value, 0) <= 0.8]
        
        if high_confidence_allergens:
            return "high"
        elif medium_confidence_allergens:
            return "medium"
        else:
            return "unknown"
    
    def detect_preparation_methods(self, text: str) -> List[str]:
        """Detect cooking/preparation methods"""
        detected_methods = []
        text_lower = text.lower()
        
        for method, patterns in self.preparation_methods.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    detected_methods.append(method)
                    break
        
        return detected_methods

class EnhancedMenuAnalyzer:
    """Enhanced menu analyzer that processes existing restaurant data"""
    
    def __init__(self):
        self.allergen_detector = AdvancedAllergenDetector()
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)
    
    async def enhance_chicago_restaurants(self, input_file: str = "chicago_restaurants_optimized_yelp.json") -> Dict[str, Any]:
        """Enhance existing Chicago restaurant data with allergen analysis"""
        print("🔬 ENHANCED ALLERGEN ANALYZER & MENU DATA ENHANCEMENT")
        print("=" * 60)
        print(f"📊 Processing: {input_file}")
        print(f"🎯 Focus: Comprehensive allergen analysis and health data")
        print()
        
        # Load existing data
        input_path = self.output_dir / input_file
        if not input_path.exists():
            print(f"❌ Input file not found: {input_path}")
            return {}
        
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle different data structures
        restaurants_data = []
        if 'restaurants' in data:
            restaurants_data = data['restaurants']
        elif 'summary' in data and 'restaurants' in data['summary']:
            restaurants_data = data['summary']['restaurants']
        else:
            print(f"❌ No restaurants found in data structure")
            return {}
        
        enhanced_restaurants = []
        total_restaurants = len(restaurants_data)
        processed_count = 0
        
        print(f"📈 Processing {total_restaurants} restaurants...")
        
        for restaurant in restaurants_data:
            enhanced_restaurant = await self._enhance_restaurant(restaurant)
            enhanced_restaurants.append(enhanced_restaurant)
            processed_count += 1
            
            if processed_count % 50 == 0:
                print(f"✅ Processed {processed_count}/{total_restaurants} restaurants")
        
        # Generate comprehensive analysis
        analysis_summary = self._generate_analysis_summary(enhanced_restaurants)
        
        # Create enhanced dataset
        enhanced_data = {
            "enhancement_summary": {
                "original_file": input_file,
                "enhancement_date": datetime.now().isoformat(),
                "total_restaurants_processed": processed_count,
                "enhancement_features": [
                    "Advanced allergen detection",
                    "Dietary tag classification",
                    "Risk level assessment",
                    "Preparation method detection",
                    "Nutritional hints extraction",
                    "Health-focused categorization"
                ],
                "allergen_coverage": analysis_summary["allergen_coverage"],
                "dietary_distribution": analysis_summary["dietary_distribution"],
                "risk_level_distribution": analysis_summary["risk_level_distribution"]
            },
            "restaurants": enhanced_restaurants,
            "analysis_summary": analysis_summary
        }
        
        # Save enhanced data
        output_file = f"chicago_restaurants_enhanced_allergen_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        output_path = self.output_dir / output_file
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(enhanced_data, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n✅ Enhanced data saved to: {output_file}")
        print(f"📊 Analysis Summary:")
        print(f"   • Restaurants processed: {processed_count}")
        print(f"   • Allergen detections: {analysis_summary['total_allergen_detections']}")
        print(f"   • High-risk items: {analysis_summary['high_risk_count']}")
        print(f"   • Dietary tags found: {analysis_summary['total_dietary_tags']}")
        
        return enhanced_data
    
    async def _enhance_restaurant(self, restaurant: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance individual restaurant with allergen analysis"""
        enhanced_restaurant = restaurant.copy()
        
        # Analyze restaurant name and categories for allergen hints
        restaurant_text = f"{restaurant.get('name', '')} {' '.join(restaurant.get('categories', []))}"
        restaurant_analysis = self.allergen_detector.analyze_allergens(restaurant_text)
        
        # Add restaurant-level allergen analysis
        enhanced_restaurant['restaurant_allergen_analysis'] = {
            'potential_allergens': [a.value for a in restaurant_analysis.detected_allergens],
            'dietary_friendly': [tag.value for tag in restaurant_analysis.dietary_tags],
            'risk_assessment': restaurant_analysis.risk_level,
            'confidence_scores': restaurant_analysis.confidence_scores
        }
        
        # Process menu items if available
        if 'menu_items' in restaurant and restaurant['menu_items']:
            enhanced_menu_items = []
            for item in restaurant['menu_items']:
                enhanced_item = await self._enhance_menu_item(item)
                enhanced_menu_items.append(enhanced_item)
            enhanced_restaurant['menu_items'] = enhanced_menu_items
        
        # Add health score
        enhanced_restaurant['health_score'] = self._calculate_health_score(enhanced_restaurant)
        
        return enhanced_restaurant
    
    async def _enhance_menu_item(self, menu_item: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance individual menu item with comprehensive analysis"""
        item_text = f"{menu_item.get('name', '')} {menu_item.get('description', '')}"
        
        # Perform allergen analysis
        allergen_analysis = self.allergen_detector.analyze_allergens(
            item_text, 
            menu_item.get('name', '')
        )
        
        # Detect preparation methods
        prep_methods = self.allergen_detector.detect_preparation_methods(item_text)
        
        # Extract nutritional hints
        nutritional_hints = self._extract_nutritional_hints(item_text)
        
        # Create enhanced menu item
        enhanced_item = EnhancedMenuItem(
            name=menu_item.get('name', ''),
            description=menu_item.get('description', ''),
            price=menu_item.get('price'),
            category=menu_item.get('category', 'unknown'),
            allergen_analysis=allergen_analysis,
            nutritional_hints=nutritional_hints,
            ingredients_detected=self._extract_ingredients(item_text),
            preparation_methods=prep_methods,
            confidence_score=self._calculate_item_confidence(allergen_analysis),
            source_url=menu_item.get('source_url')
        )
        
        return asdict(enhanced_item)
    
    def _extract_nutritional_hints(self, text: str) -> Dict[str, Any]:
        """Extract nutritional information hints from text"""
        text_lower = text.lower()
        
        hints = {
            'likely_high_protein': bool(re.search(r'\b(protein|chicken|beef|fish|tofu|beans|lentils)\b', text_lower)),
            'likely_high_fat': bool(re.search(r'\b(fried|butter|oil|cream|cheese|avocado)\b', text_lower)),
            'likely_high_carb': bool(re.search(r'\b(pasta|rice|bread|potato|noodles)\b', text_lower)),
            'likely_high_fiber': bool(re.search(r'\b(beans|lentils|quinoa|oats|vegetables)\b', text_lower)),
            'likely_low_calorie': bool(re.search(r'\b(salad|steamed|grilled|light|fresh)\b', text_lower)),
            'contains_vegetables': bool(re.search(r'\b(vegetables|veggie|lettuce|tomato|onion|pepper)\b', text_lower)),
            'contains_fruits': bool(re.search(r'\b(apple|banana|berry|citrus|fruit)\b', text_lower))
        }
        
        return hints
    
    def _extract_ingredients(self, text: str) -> List[str]:
        """Extract likely ingredients from menu item text"""
        # Common ingredient patterns
        ingredient_patterns = [
            r'\b(chicken|beef|pork|fish|salmon|tuna|shrimp|crab|lobster)\b',
            r'\b(cheese|mozzarella|parmesan|cheddar|feta|goat cheese)\b',
            r'\b(tomato|onion|garlic|pepper|mushroom|spinach|lettuce)\b',
            r'\b(rice|pasta|noodles|bread|quinoa|couscous)\b',
            r'\b(olive oil|butter|cream|milk|yogurt)\b',
            r'\b(herbs|basil|oregano|thyme|rosemary|cilantro|parsley)\b'
        ]
        
        ingredients = []
        text_lower = text.lower()
        
        for pattern in ingredient_patterns:
            matches = re.findall(pattern, text_lower)
            ingredients.extend(matches)
        
        return list(set(ingredients))  # Remove duplicates
    
    def _calculate_item_confidence(self, allergen_analysis: AllergenAnalysis) -> float:
        """Calculate confidence score for menu item analysis"""
        if not allergen_analysis.confidence_scores:
            return 0.5  # Neutral confidence when no allergens detected
        
        avg_confidence = sum(allergen_analysis.confidence_scores.values()) / len(allergen_analysis.confidence_scores)
        
        # Adjust based on risk level
        risk_multiplier = {
            'high': 1.0,
            'medium': 0.8,
            'low': 0.6,
            'unknown': 0.4
        }
        
        return avg_confidence * risk_multiplier.get(allergen_analysis.risk_level, 0.5)
    
    def _calculate_health_score(self, restaurant: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall health score for restaurant"""
        score_components = {
            'allergen_transparency': 0,
            'dietary_options': 0,
            'menu_variety': 0,
            'preparation_methods': 0
        }
        
        # Allergen transparency score
        if 'menu_items' in restaurant:
            total_items = len(restaurant['menu_items'])
            if total_items > 0:
                items_with_allergen_info = sum(1 for item in restaurant['menu_items'] 
                                             if item.get('allergen_analysis', {}).get('detected_allergens'))
                score_components['allergen_transparency'] = (items_with_allergen_info / total_items) * 100
        
        # Dietary options score
        dietary_tags = restaurant.get('restaurant_allergen_analysis', {}).get('dietary_friendly', [])
        score_components['dietary_options'] = min(len(dietary_tags) * 20, 100)
        
        # Menu variety score (based on categories)
        if 'menu_items' in restaurant:
            categories = set(item.get('category', 'unknown') for item in restaurant['menu_items'])
            score_components['menu_variety'] = min(len(categories) * 15, 100)
        
        # Overall health score
        overall_score = sum(score_components.values()) / len(score_components)
        
        return {
            'overall_score': round(overall_score, 2),
            'components': score_components,
            'rating': 'excellent' if overall_score >= 80 else 
                     'good' if overall_score >= 60 else 
                     'fair' if overall_score >= 40 else 'poor'
        }
    
    def _generate_analysis_summary(self, restaurants: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive analysis summary"""
        total_restaurants = len(restaurants)
        total_allergen_detections = 0
        total_dietary_tags = 0
        risk_distribution = {'high': 0, 'medium': 0, 'low': 0, 'unknown': 0}
        allergen_counts = {}
        dietary_counts = {}
        
        for restaurant in restaurants:
            # Count restaurant-level allergens
            restaurant_allergens = restaurant.get('restaurant_allergen_analysis', {}).get('potential_allergens', [])
            total_allergen_detections += len(restaurant_allergens)
            
            for allergen in restaurant_allergens:
                allergen_counts[allergen] = allergen_counts.get(allergen, 0) + 1
            
            # Count dietary tags
            dietary_tags = restaurant.get('restaurant_allergen_analysis', {}).get('dietary_friendly', [])
            total_dietary_tags += len(dietary_tags)
            
            for tag in dietary_tags:
                dietary_counts[tag] = dietary_counts.get(tag, 0) + 1
            
            # Count risk levels
            risk_level = restaurant.get('restaurant_allergen_analysis', {}).get('risk_assessment', 'unknown')
            risk_distribution[risk_level] = risk_distribution.get(risk_level, 0) + 1
        
        return {
            'total_restaurants': total_restaurants,
            'total_allergen_detections': total_allergen_detections,
            'total_dietary_tags': total_dietary_tags,
            'high_risk_count': risk_distribution['high'],
            'allergen_coverage': {
                'restaurants_with_allergen_info': sum(1 for r in restaurants 
                                                    if r.get('restaurant_allergen_analysis', {}).get('potential_allergens')),
                'coverage_percentage': round((sum(1 for r in restaurants 
                                                if r.get('restaurant_allergen_analysis', {}).get('potential_allergens')) / total_restaurants) * 100, 2) if total_restaurants > 0 else 0
            },
            'dietary_distribution': dietary_counts,
            'risk_level_distribution': risk_distribution,
            'top_allergens': sorted(allergen_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        }

async def main():
    """Main function to run enhanced allergen analysis"""
    analyzer = EnhancedMenuAnalyzer()
    
    # Enhance Chicago restaurant data
    enhanced_data = await analyzer.enhance_chicago_restaurants()
    
    if enhanced_data:
        print("\n🎉 Enhanced allergen analysis completed successfully!")
        print("\n📋 Key Features Added:")
        print("   ✅ Advanced allergen detection with confidence scoring")
        print("   ✅ Dietary tag classification (vegetarian, vegan, gluten-free, etc.)")
        print("   ✅ Risk level assessment (high, medium, low, unknown)")
        print("   ✅ Preparation method detection")
        print("   ✅ Nutritional hints extraction")
        print("   ✅ Health score calculation")
        print("   ✅ Comprehensive analysis summary")
        
        print("\n🏥 Health App Integration Ready:")
        print("   • Allergen filtering and warnings")
        print("   • Dietary preference matching")
        print("   • Risk-based recommendations")
        print("   • Nutritional guidance")
        print("   • Restaurant health scoring")
    else:
        print("❌ Enhancement failed. Please check input file.")

if __name__ == "__main__":
    asyncio.run(main())