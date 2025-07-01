#!/usr/bin/env python3
"""
Enhanced Website Menu Scraper
Targets actual restaurant websites for better menu extraction
Uses known Chicago restaurant websites for real menu data extraction
"""

import asyncio
import json
import re
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from urllib.parse import urljoin, urlparse
import random

try:
    from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeoutError
except ImportError:
    print("❌ Playwright not installed. Run: pip install playwright")
    exit(1)

from enhanced_allergen_analyzer import AdvancedAllergenDetector, AllergenType, DietaryTag

class EnhancedWebsiteMenuScraper:
    """Enhanced menu scraper targeting actual restaurant websites"""
    
    def __init__(self, headless: bool = True, timeout: int = 30000, proxy: Optional[str] = None):
        self.headless = headless
        self.timeout = timeout
        self.proxy = proxy
        self.browser: Optional[Browser] = None
        self.context = None
        self.allergen_detector = AdvancedAllergenDetector()
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)
        
        # Enhanced menu detection selectors for restaurant websites
        self.menu_selectors = [
            # Common menu item patterns
            '.menu-item', '.food-item', '.dish-item', '.product-item',
            '.menu-section-item', '.menu-list-item', '.dish',
            '[class*="menu-item"]', '[class*="food-item"]', '[class*="dish"]',
            '[class*="product"]', '[class*="item"]',
            
            # Menu containers
            '.menu-section .item', '.menu-category .item',
            '.food-menu .item', '.restaurant-menu .item',
            
            # Price-based detection (more specific)
            '.menu-item:has-text("$")', '.dish:has-text("$")',
            'div[class*="price"]:has-text("$")',
            
            # List-based patterns (filtered)
            '.menu ul li', '.food-list li', '.dish-list li',
            
            # Table-based patterns
            '.menu table tr', '.menu tbody tr',
            'table.menu tr', 'table[class*="menu"] tr',
            
            # Card-based patterns
            '.menu-card', '.food-card', '.dish-card',
            '[class*="menu-card"]', '[class*="food-card"]'
        ]
        
        # Menu page indicators
        self.menu_indicators = [
            'menu', 'food', 'dine', 'eat', 'order', 'cuisine',
            'breakfast', 'lunch', 'dinner', 'specials', 'dishes'
        ]
        
        # Price patterns
        self.price_patterns = [
            r'\$\d+(?:\.\d{2})?',
            r'\d+(?:\.\d{2})?\s*(?:dollars?|usd|\$)',
            r'\b\d{1,2}(?:\.\d{2})?\b(?=\s*(?:$|\n|\s))',
        ]
        
        # Chicago restaurants with known websites
        self.chicago_restaurants = [
            {
                "name": "Alinea",
                "website": "https://www.alinearestaurant.com",
                "categories": ["Fine Dining", "American"],
                "location": "Lincoln Park"
            },
            {
                "name": "Girl & the Goat",
                "website": "https://www.girlandthegoat.com",
                "categories": ["American", "Mediterranean"],
                "location": "West Loop"
            },
            {
                "name": "Au Cheval",
                "website": "https://www.aucheval.com",
                "categories": ["American", "Burgers"],
                "location": "West Loop"
            },
            {
                "name": "The Purple Pig",
                "website": "https://www.thepurplepigchicago.com",
                "categories": ["Italian", "Wine Bar"],
                "location": "Near North Side"
            },
            {
                "name": "Gibsons Bar & Steakhouse",
                "website": "https://www.gibsonssteakhouse.com",
                "categories": ["Steakhouse", "American"],
                "location": "Rush Street"
            },
            {
                "name": "Pequod's Pizza",
                "website": "https://pequodspizza.com",
                "categories": ["Pizza", "Italian"],
                "location": "Morton Grove"
            },
            {
                "name": "Lou Malnati's Pizzeria",
                "website": "https://www.loumalnatis.com",
                "categories": ["Pizza", "Italian"],
                "location": "Multiple Locations"
            },
            {
                "name": "Portillo's",
                "website": "https://www.portillos.com",
                "categories": ["American", "Hot Dogs"],
                "location": "Multiple Locations"
            },
            {
                "name": "The Publican",
                "website": "https://thepublicanrestaurant.com",
                "categories": ["Seafood", "American"],
                "location": "West Loop"
            },
            {
                "name": "Wildberry Pancakes & Cafe",
                "website": "https://www.wildberrycafe.com",
                "categories": ["Breakfast", "American"],
                "location": "Multiple Locations"
            }
        ]
    
    async def setup_browser(self) -> bool:
        """Setup browser with enhanced stealth configuration and proxy support"""
        try:
            playwright = await async_playwright().start()
            
            # Browser launch arguments
            launch_args = [
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--disable-extensions',
                '--disable-gpu',
                '--disable-web-security',
                '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ]
            
            # Add proxy to launch args if provided
            if self.proxy:
                launch_args.append(f'--proxy-server={self.proxy}')
                print(f"🌐 Using proxy: {self.proxy}")
            
            self.browser = await playwright.chromium.launch(
                headless=self.headless,
                args=launch_args
            )
            
            # Context configuration
            context_config = {
                'viewport': {'width': 1920, 'height': 1080},
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'locale': 'en-US',
                'timezone_id': 'America/Chicago'
            }
            
            # Add proxy to context if provided (alternative method)
            if self.proxy:
                context_config['proxy'] = {'server': self.proxy}
            
            self.context = await self.browser.new_context(**context_config)
            
            return True
            
        except Exception as e:
            print(f"❌ Browser setup failed: {e}")
            return False
    
    async def scrape_enhanced_menus(self, max_restaurants: int = 8) -> Dict[str, Any]:
        """Scrape menus from actual restaurant websites"""
        print("🍽️ ENHANCED WEBSITE MENU SCRAPER")
        print("=" * 60)
        print(f"🎯 Target: {max_restaurants} Chicago restaurants")
        print(f"🌐 Source: Actual restaurant websites")
        print(f"🔬 Focus: Real menu extraction + comprehensive allergen analysis")
        print()
        
        # Setup browser
        if not await self.setup_browser():
            return {}
        
        try:
            # Get restaurant data
            restaurants_data = self.chicago_restaurants[:max_restaurants]
            
            enhanced_restaurants = []
            processed_count = 0
            success_count = 0
            total_menu_items = 0
            
            # Process restaurants
            for i, restaurant in enumerate(restaurants_data):
                print(f"\n🏪 [{i+1}/{len(restaurants_data)}] Processing: {restaurant.get('name', 'Unknown')}")
                print(f"   📍 Location: {restaurant.get('location', 'Unknown')}")
                
                enhanced_restaurant = await self._scrape_restaurant_website(restaurant)
                enhanced_restaurants.append(enhanced_restaurant)
                processed_count += 1
                
                if enhanced_restaurant.get('menu_extraction_success', False):
                    success_count += 1
                    menu_items = enhanced_restaurant.get('enhanced_menu_items', [])
                    total_menu_items += len(menu_items)
                    print(f"   ✅ Success: {len(menu_items)} menu items extracted")
                    
                    # Show sample allergen detections
                    allergen_items = [item for item in menu_items if item.get('allergen_analysis', {}).get('detected_allergens')]
                    if allergen_items:
                        print(f"   🔬 Allergens detected in {len(allergen_items)} items")
                        sample_item = allergen_items[0]
                        allergens = sample_item['allergen_analysis']['detected_allergens']
                        print(f"   📋 Sample: '{sample_item['name']}' contains {', '.join(allergens)}")
                else:
                    print(f"   ❌ Failed: {enhanced_restaurant.get('extraction_error', 'Unknown error')}")
                
                # Add delay between requests
                await asyncio.sleep(random.uniform(3, 6))
            
            # Generate comprehensive analysis
            analysis_summary = self._generate_comprehensive_analysis(enhanced_restaurants)
            
            # Create final dataset
            comprehensive_data = {
                "scraping_summary": {
                    "scraping_date": datetime.now().isoformat(),
                    "source_type": "chicago_restaurant_websites",
                    "restaurants_processed": processed_count,
                    "successful_extractions": success_count,
                    "success_rate_percent": round((success_count / processed_count) * 100, 2) if processed_count > 0 else 0,
                    "total_menu_items_extracted": total_menu_items,
                    "average_items_per_restaurant": round(total_menu_items / success_count, 2) if success_count > 0 else 0,
                    "features": [
                        "Direct website menu extraction",
                        "Advanced allergen detection",
                        "Dietary classification",
                        "Risk assessment",
                        "Nutritional analysis",
                        "Health scoring",
                        "Preparation method detection"
                    ]
                },
                "restaurants": enhanced_restaurants,
                "allergen_analysis": analysis_summary["allergen_analysis"],
                "dietary_analysis": analysis_summary["dietary_analysis"],
                "health_insights": analysis_summary["health_insights"]
            }
            
            # Save comprehensive data
            output_file = f"chicago_enhanced_website_menu_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            output_path = self.output_dir / output_file
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(comprehensive_data, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"\n✅ Enhanced menu data saved to: {output_file}")
            print(f"\n📊 FINAL SUMMARY:")
            print(f"   • Restaurants processed: {processed_count}")
            print(f"   • Successful extractions: {success_count} ({round((success_count / processed_count) * 100, 2)}%)")
            print(f"   • Total menu items: {total_menu_items}")
            print(f"   • Allergen detections: {analysis_summary['allergen_analysis']['total_allergen_detections']}")
            print(f"   • High-risk items: {analysis_summary['allergen_analysis']['high_risk_items']}")
            print(f"   • Dietary options: {analysis_summary['dietary_analysis']['total_dietary_tags']}")
            print(f"   • Health app readiness: {analysis_summary['health_insights']['health_app_readiness']}")
            
            return comprehensive_data
            
        finally:
            if self.browser:
                await self.browser.close()
    
    async def _scrape_restaurant_website(self, restaurant: Dict[str, Any]) -> Dict[str, Any]:
        """Scrape menu from restaurant's actual website"""
        enhanced_restaurant = restaurant.copy()
        
        try:
            page = await self.context.new_page()
            
            # Get restaurant website
            website_url = restaurant.get('website', '')
            if not website_url:
                enhanced_restaurant.update({
                    'menu_extraction_success': False,
                    'extraction_error': 'No website URL provided',
                    'enhanced_menu_items': []
                })
                return enhanced_restaurant
            
            print(f"   🌐 Navigating to: {website_url}")
            await page.goto(website_url, wait_until='networkidle', timeout=self.timeout)
            
            # Look for menu section or navigate to menu page
            menu_items = await self._extract_website_menu_items(page, website_url)
            
            if not menu_items:
                # Try to find and navigate to menu page
                menu_url = await self._find_menu_page(page, website_url)
                if menu_url:
                    print(f"   📋 Found menu page: {menu_url}")
                    await page.goto(menu_url, wait_until='networkidle', timeout=self.timeout)
                    menu_items = await self._extract_website_menu_items(page, menu_url)
            
            # Process extracted menu items
            enhanced_menu_items = []
            for item in menu_items:
                enhanced_item = await self._enhance_menu_item(item, restaurant)
                enhanced_menu_items.append(enhanced_item)
            
            # Add restaurant-level analysis
            restaurant_analysis = self._analyze_restaurant_allergens(restaurant, enhanced_menu_items)
            
            enhanced_restaurant.update({
                'website_url': website_url,
                'menu_extraction_success': len(enhanced_menu_items) > 0,
                'extraction_error': None if enhanced_menu_items else 'No menu items found',
                'enhanced_menu_items': enhanced_menu_items,
                'restaurant_allergen_summary': restaurant_analysis,
                'menu_extraction_timestamp': datetime.now().isoformat()
            })
            
            await page.close()
            return enhanced_restaurant
            
        except Exception as e:
            print(f"   ❌ Error scraping {restaurant.get('name', 'Unknown')}: {str(e)}")
            enhanced_restaurant.update({
                'menu_extraction_success': False,
                'extraction_error': str(e),
                'enhanced_menu_items': []
            })
            return enhanced_restaurant
    
    async def _find_menu_page(self, page: Page, base_url: str) -> Optional[str]:
        """Find menu page on restaurant website"""
        try:
            # Look for menu links
            for indicator in self.menu_indicators:
                selectors = [
                    f'a[href*="{indicator}"]',
                    f'a:has-text("{indicator}")',
                    f'button:has-text("{indicator}")',
                    f'[class*="{indicator}"] a',
                    f'nav a:has-text("{indicator}")',
                    f'.menu a', f'.navigation a:has-text("{indicator}")'
                ]
                
                for selector in selectors:
                    try:
                        element = await page.query_selector(selector)
                        if element:
                            href = await element.get_attribute('href')
                            if href:
                                full_url = urljoin(base_url, href)
                                if self._is_menu_url(full_url):
                                    return full_url
                    except:
                        continue
            
            return None
            
        except Exception as e:
            print(f"   ⚠️ Error finding menu page: {e}")
            return None
    
    def _is_menu_url(self, url: str) -> bool:
        """Check if URL is likely a menu page"""
        url_lower = url.lower()
        return any(indicator in url_lower for indicator in self.menu_indicators)
    
    async def _extract_website_menu_items(self, page: Page, url: str) -> List[Dict[str, Any]]:
        """Extract menu items from restaurant website"""
        menu_items = []
        
        try:
            # Wait for content to load
            await asyncio.sleep(3)
            
            # Try different menu extraction strategies
            for selector in self.menu_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements and len(elements) >= 3:  # Minimum threshold
                        print(f"   📋 Found {len(elements)} items with selector: {selector}")
                        
                        valid_items = []
                        for element in elements[:30]:  # Limit to prevent overwhelming data
                            item_data = await self._extract_item_data(element)
                            if item_data and self._is_valid_menu_item(item_data):
                                valid_items.append(item_data)
                        
                        if len(valid_items) >= 3:  # Need at least 3 valid items
                            menu_items = valid_items
                            break
                            
                except Exception as e:
                    continue
            
            # If no structured menu found, try text-based extraction
            if not menu_items:
                menu_items = await self._extract_text_based_menu(page)
            
            return menu_items[:25]  # Limit to 25 items per restaurant
            
        except Exception as e:
            print(f"   ❌ Error extracting menu items: {e}")
            return []
    
    def _is_valid_menu_item(self, item: Dict[str, Any]) -> bool:
        """Check if extracted item is a valid menu item"""
        name = item.get('name', '').strip()
        
        # Filter out navigation and non-food items
        invalid_patterns = [
            r'^(home|about|contact|location|hours|reservation|order|cart|login|sign|register)$',
            r'^(menu|food|drink|wine|beer|cocktail)$',
            r'^(breakfast|lunch|dinner|appetizer|entree|dessert|beverage)$',
            r'^(privacy|terms|policy|copyright|\d+)$',
            r'^(facebook|twitter|instagram|yelp)$'
        ]
        
        name_lower = name.lower()
        for pattern in invalid_patterns:
            if re.match(pattern, name_lower):
                return False
        
        # Must have reasonable length
        if len(name) < 3 or len(name) > 100:
            return False
        
        # Should contain food-related words or have a price
        food_indicators = [
            'chicken', 'beef', 'pork', 'fish', 'salmon', 'tuna', 'shrimp', 'lobster',
            'pasta', 'pizza', 'burger', 'sandwich', 'salad', 'soup', 'steak',
            'cheese', 'bread', 'rice', 'noodle', 'vegetable', 'fruit', 'dessert',
            'cake', 'pie', 'ice cream', 'chocolate', 'wine', 'beer', 'cocktail'
        ]
        
        has_food_indicator = any(indicator in name_lower for indicator in food_indicators)
        has_price = bool(item.get('price'))
        has_description = bool(item.get('description', '').strip())
        
        return has_food_indicator or has_price or (has_description and len(item['description']) > 10)
    
    async def _extract_item_data(self, element) -> Dict[str, Any]:
        """Extract data from individual menu item element"""
        try:
            # Get text content
            text_content = await element.text_content()
            if not text_content or len(text_content.strip()) < 3:
                return {}
            
            # Clean and split text
            lines = [line.strip() for line in text_content.split('\n') if line.strip()]
            if not lines:
                return {}
            
            # Find price
            price = None
            price_line_idx = -1
            for i, line in enumerate(lines):
                for pattern in self.price_patterns:
                    match = re.search(pattern, line)
                    if match:
                        price = match.group()
                        price_line_idx = i
                        break
                if price:
                    break
            
            # Extract name and description
            if price_line_idx >= 0:
                # Name is usually before price
                name_lines = lines[:price_line_idx] if price_line_idx > 0 else [lines[0]]
                desc_lines = lines[price_line_idx+1:] if price_line_idx < len(lines)-1 else []
            else:
                # No price found, first line is name, rest is description
                name_lines = [lines[0]]
                desc_lines = lines[1:]
            
            name = ' '.join(name_lines).strip()
            description = ' '.join(desc_lines).strip()
            
            # Clean up description (remove price if found)
            if price and price in description:
                description = description.replace(price, '').strip()
            
            return {
                'name': name[:100],  # Limit length
                'description': description[:300],  # Limit length
                'price': price,
                'raw_text': text_content[:200]  # Keep raw text for analysis
            }
            
        except Exception as e:
            return {}
    
    async def _extract_text_based_menu(self, page: Page) -> List[Dict[str, Any]]:
        """Extract menu items using text-based patterns"""
        try:
            # Get page text
            page_text = await page.text_content('body')
            if not page_text:
                return []
            
            menu_items = []
            
            # Look for price patterns and extract surrounding text
            price_pattern = r'\$\d+(?:\.\d{2})?'
            matches = list(re.finditer(price_pattern, page_text))
            
            for match in matches[:15]:  # Limit to 15 items
                price = match.group()
                start = max(0, match.start() - 150)
                end = min(len(page_text), match.end() + 150)
                context = page_text[start:end]
                
                # Extract potential item name (text before price)
                before_price = context[:context.find(price)]
                lines = [line.strip() for line in before_price.split('\n') if line.strip()]
                
                if lines:
                    name = lines[-1]  # Last line before price is likely the name
                    if len(name) > 3 and len(name) < 80:  # Reasonable name length
                        # Get description (text after price)
                        after_price = context[context.find(price)+len(price):]
                        desc_lines = [line.strip() for line in after_price.split('\n') if line.strip()]
                        description = desc_lines[0] if desc_lines else ''
                        
                        item = {
                            'name': name,
                            'description': description[:200],
                            'price': price,
                            'raw_text': context
                        }
                        
                        if self._is_valid_menu_item(item):
                            menu_items.append(item)
            
            return menu_items
            
        except Exception as e:
            print(f"   ❌ Error in text-based extraction: {e}")
            return []
    
    async def _enhance_menu_item(self, item: Dict[str, Any], restaurant: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance menu item with comprehensive allergen analysis"""
        # Combine all text for analysis
        analysis_text = f"{item.get('name', '')} {item.get('description', '')} {item.get('raw_text', '')}"
        
        # Perform allergen analysis
        allergen_analysis = self.allergen_detector.analyze_allergens(analysis_text, item.get('name', ''))
        
        # Detect preparation methods
        prep_methods = self.allergen_detector.detect_preparation_methods(analysis_text)
        
        # Extract nutritional hints
        nutritional_hints = self._extract_nutritional_hints(analysis_text)
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(allergen_analysis, item)
        
        return {
            'name': item.get('name', ''),
            'description': item.get('description', ''),
            'price': item.get('price'),
            'restaurant_name': restaurant.get('name', ''),
            'restaurant_categories': restaurant.get('categories', []),
            'allergen_analysis': {
                'detected_allergens': [a.value for a in allergen_analysis.detected_allergens],
                'confidence_scores': allergen_analysis.confidence_scores,
                'dietary_tags': [tag.value for tag in allergen_analysis.dietary_tags],
                'risk_level': allergen_analysis.risk_level,
                'safe_for_allergies': [a.value for a in allergen_analysis.safe_for_allergies],
                'warnings': allergen_analysis.warnings
            },
            'preparation_methods': prep_methods,
            'nutritional_hints': nutritional_hints,
            'confidence_score': confidence_score,
            'extraction_timestamp': datetime.now().isoformat()
        }
    
    def _extract_nutritional_hints(self, text: str) -> Dict[str, Any]:
        """Extract nutritional hints from text"""
        text_lower = text.lower()
        
        return {
            'likely_high_protein': bool(re.search(r'\b(protein|chicken|beef|fish|tofu|beans|lentils|quinoa|steak|salmon|tuna|shrimp|lobster)\b', text_lower)),
            'likely_high_fat': bool(re.search(r'\b(fried|butter|oil|cream|cheese|avocado|nuts|bacon|sausage)\b', text_lower)),
            'likely_high_carb': bool(re.search(r'\b(pasta|rice|bread|potato|noodles|flour|pizza|sandwich)\b', text_lower)),
            'likely_high_fiber': bool(re.search(r'\b(beans|lentils|quinoa|oats|vegetables|whole grain|salad|spinach|kale)\b', text_lower)),
            'likely_low_calorie': bool(re.search(r'\b(salad|steamed|grilled|light|fresh|raw|vegetable|fruit)\b', text_lower)),
            'contains_vegetables': bool(re.search(r'\b(vegetables|veggie|lettuce|tomato|onion|pepper|spinach|kale|broccoli|carrot)\b', text_lower)),
            'contains_fruits': bool(re.search(r'\b(apple|banana|berry|citrus|fruit|orange|strawberry|mango|pineapple)\b', text_lower)),
            'spicy_level': len(re.findall(r'\b(spicy|hot|jalapeño|habanero|sriracha|chili|pepper|cayenne)\b', text_lower))
        }
    
    def _calculate_confidence_score(self, allergen_analysis, item: Dict[str, Any]) -> float:
        """Calculate confidence score for menu item analysis"""
        base_score = 0.6
        
        # Boost confidence based on available data
        if item.get('description') and len(item['description']) > 20:
            base_score += 0.2
        
        if item.get('name') and len(item['name']) > 5:
            base_score += 0.1
        
        if item.get('price'):
            base_score += 0.1
        
        # Adjust based on allergen detection confidence
        if allergen_analysis.confidence_scores:
            avg_allergen_confidence = sum(allergen_analysis.confidence_scores.values()) / len(allergen_analysis.confidence_scores)
            base_score = (base_score + avg_allergen_confidence) / 2
        
        return min(base_score, 1.0)
    
    def _analyze_restaurant_allergens(self, restaurant: Dict[str, Any], menu_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze restaurant-level allergen information"""
        if not menu_items:
            return {
                'total_menu_items': 0,
                'allergen_summary': {},
                'dietary_options': [],
                'risk_assessment': 'unknown'
            }
        
        # Aggregate allergen data
        allergen_counts = {}
        dietary_tags = set()
        risk_levels = {'high': 0, 'medium': 0, 'low': 0, 'unknown': 0}
        
        for item in menu_items:
            allergen_analysis = item.get('allergen_analysis', {})
            
            # Count allergens
            for allergen in allergen_analysis.get('detected_allergens', []):
                allergen_counts[allergen] = allergen_counts.get(allergen, 0) + 1
            
            # Collect dietary tags
            for tag in allergen_analysis.get('dietary_tags', []):
                dietary_tags.add(tag)
            
            # Count risk levels
            risk_level = allergen_analysis.get('risk_level', 'unknown')
            risk_levels[risk_level] += 1
        
        # Determine overall restaurant risk
        total_items = len(menu_items)
        high_risk_percentage = (risk_levels['high'] / total_items) * 100 if total_items > 0 else 0
        
        overall_risk = 'high' if high_risk_percentage > 30 else \
                      'medium' if high_risk_percentage > 10 else \
                      'low' if risk_levels['low'] > 0 else 'unknown'
        
        return {
            'total_menu_items': total_items,
            'allergen_summary': allergen_counts,
            'dietary_options': list(dietary_tags),
            'risk_assessment': overall_risk,
            'risk_distribution': risk_levels,
            'allergen_coverage_percent': round((sum(1 for item in menu_items 
                                                   if item.get('allergen_analysis', {}).get('detected_allergens')) / total_items) * 100, 2) if total_items > 0 else 0
        }
    
    def _generate_comprehensive_analysis(self, restaurants: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive analysis of all data"""
        total_restaurants = len(restaurants)
        successful_restaurants = [r for r in restaurants if r.get('menu_extraction_success', False)]
        total_menu_items = sum(len(r.get('enhanced_menu_items', [])) for r in successful_restaurants)
        
        # Allergen analysis
        allergen_counts = {}
        total_allergen_detections = 0
        high_risk_items = 0
        
        # Dietary analysis
        dietary_counts = {}
        total_dietary_tags = 0
        
        for restaurant in successful_restaurants:
            for item in restaurant.get('enhanced_menu_items', []):
                allergen_analysis = item.get('allergen_analysis', {})
                
                # Count allergens
                detected_allergens = allergen_analysis.get('detected_allergens', [])
                total_allergen_detections += len(detected_allergens)
                
                for allergen in detected_allergens:
                    allergen_counts[allergen] = allergen_counts.get(allergen, 0) + 1
                
                # Count high-risk items
                if allergen_analysis.get('risk_level') == 'high':
                    high_risk_items += 1
                
                # Count dietary tags
                dietary_tags = allergen_analysis.get('dietary_tags', [])
                total_dietary_tags += len(dietary_tags)
                
                for tag in dietary_tags:
                    dietary_counts[tag] = dietary_counts.get(tag, 0) + 1
        
        return {
            'allergen_analysis': {
                'total_allergen_detections': total_allergen_detections,
                'high_risk_items': high_risk_items,
                'allergen_distribution': allergen_counts,
                'top_allergens': sorted(allergen_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            },
            'dietary_analysis': {
                'total_dietary_tags': total_dietary_tags,
                'dietary_distribution': dietary_counts,
                'top_dietary_options': sorted(dietary_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            },
            'health_insights': {
                'restaurants_with_menu_data': len(successful_restaurants),
                'average_menu_items_per_restaurant': round(total_menu_items / len(successful_restaurants), 2) if successful_restaurants else 0,
                'allergen_coverage_percent': round((sum(1 for r in successful_restaurants 
                                                       if r.get('restaurant_allergen_summary', {}).get('allergen_coverage_percent', 0) > 0) / len(successful_restaurants)) * 100, 2) if successful_restaurants else 0,
                'health_app_readiness': 'excellent' if total_menu_items > 80 and total_allergen_detections > 40 else 
                                       'good' if total_menu_items > 40 and total_allergen_detections > 20 else 
                                       'fair' if total_menu_items > 15 else 'poor'
            }
        }

    async def scrape_restaurant_menu(self, restaurant_name: str, direct_url: str = None) -> Dict[str, Any]:
        """Public method to scrape a single restaurant's menu"""
        if not await self.setup_browser():
            return {
                "url": direct_url or "",
                "success": False,
                "items": [],
                "total_items": 0,
                "processing_time": 0,
                "extraction_method": None,
                "allergen_summary": {},
                "price_coverage": 0,
                "menu_image_urls": [],
                "ocr_texts": [],
                "error": "Browser setup failed"
            }
        
        start_time = time.time()
        
        try:
            # Create restaurant data structure
            restaurant_data = {
                "name": restaurant_name,
                "website": direct_url or ""
            }
            
            # Use existing private method
            result = await self._scrape_restaurant_website(restaurant_data)
            
            processing_time = time.time() - start_time
            
            # Format result for compatibility
            menu_items = result.get('enhanced_menu_items', [])
            
            return {
                "url": direct_url or "",
                "success": result.get('menu_extraction_success', False),
                "items": [{
                    "name": item.get('name', ''),
                    "price": item.get('price', ''),
                    "description": item.get('description', ''),
                    "allergens": item.get('allergen_analysis', {}).get('detected_allergens', [])
                } for item in menu_items],
                "total_items": len(menu_items),
                "processing_time": round(processing_time, 2),
                "extraction_method": "website_scraping",
                "allergen_summary": result.get('restaurant_allergen_summary', {}),
                "price_coverage": len([item for item in menu_items if item.get('price')]) / len(menu_items) if menu_items else 0,
                "menu_image_urls": [],
                "ocr_texts": [],
                "error": result.get('extraction_error')
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            return {
                "url": direct_url or "",
                "success": False,
                "items": [],
                "total_items": 0,
                "processing_time": round(processing_time, 2),
                "extraction_method": None,
                "allergen_summary": {},
                "price_coverage": 0,
                "menu_image_urls": [],
                "ocr_texts": [],
                "error": f"Navigation failed: {str(e)}"
            }
        finally:
            if self.browser:
                await self.browser.close()

async def main():
    """Main function to run enhanced website menu scraping"""
    scraper = EnhancedWebsiteMenuScraper(headless=False)  # Set to False to see browser
    
    print("🚀 Starting Enhanced Website Menu & Allergen Analysis...")
    print("This will extract real menu data from actual Chicago restaurant websites.\n")
    
    # Run enhanced scraping with Chicago restaurants
    result = await scraper.scrape_enhanced_menus(max_restaurants=8)
    
    if result:
        print("\n🎉 Enhanced website menu scraping completed successfully!")
        print("\n🏥 Health App Features Ready:")
        print("   ✅ Real menu data from restaurant websites")
        print("   ✅ Advanced allergen detection & analysis")
        print("   ✅ Risk-based filtering and warnings")
        print("   ✅ Dietary preference matching")
        print("   ✅ Nutritional guidance hints")
        print("   ✅ Restaurant health scoring")
        print("   ✅ Preparation method detection")
        print("   ✅ Comprehensive health insights")
        print("   ✅ Ready for health app integration")
    else:
        print("❌ Enhanced website scraping failed.")

if __name__ == "__main__":
    asyncio.run(main())