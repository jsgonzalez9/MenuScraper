#!/usr/bin/env python3
"""
Comprehensive Menu & Allergen Scraper
Extracts actual menu data from Chicago restaurants and applies advanced allergen analysis
Builds upon existing restaurant data to create a complete health-focused menu database
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

class ComprehensiveMenuScraper:
    """Comprehensive menu scraper with advanced allergen analysis"""
    
    def __init__(self, headless: bool = True, timeout: int = 30000):
        self.headless = headless
        self.timeout = timeout
        self.browser: Optional[Browser] = None
        self.context = None
        self.allergen_detector = AdvancedAllergenDetector()
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)
        
        # Enhanced menu detection selectors
        self.menu_selectors = [
            # Yelp-specific selectors
            'div[data-testid="menu-item"]',
            'div.menu-item',
            'div.menu-section-item',
            'div[class*="menu"][class*="item"]',
            
            # Generic menu selectors
            '.menu-item', '.food-item', '.dish-item', '.product-item',
            '[class*="menu-item"]', '[class*="food-item"]', '[class*="dish"]',
            
            # Price-based detection
            'div:has-text("$")', 'li:has-text("$")', 'span:has-text("$")',
            
            # List-based patterns
            'ul li', 'ol li', '.list-item',
            
            # Table-based patterns
            'table tr', 'tbody tr',
            
            # Content patterns
            'p:has-text("$")', 'div[class*="price"]'
        ]
        
        # Menu navigation patterns
        self.menu_link_patterns = [
            r'menu', r'food', r'order', r'dine', r'eat', r'cuisine',
            r'breakfast', r'lunch', r'dinner', r'specials'
        ]
        
        # Price extraction patterns
        self.price_patterns = [
            r'\$\d+(?:\.\d{2})?',
            r'\d+(?:\.\d{2})?\s*(?:dollars?|usd|\$)',
            r'\b\d{1,3}(?:,\d{3})*(?:\.\d{2})?\b'
        ]
    
    async def setup_browser(self) -> bool:
        """Setup browser with stealth configuration"""
        try:
            playwright = await async_playwright().start()
            
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
    
    async def scrape_comprehensive_menus(self, input_file: str = "chicago_restaurants_optimized_yelp.json", max_restaurants: int = 20) -> Dict[str, Any]:
        """Scrape comprehensive menu data with allergen analysis"""
        print("🍽️ COMPREHENSIVE MENU & ALLERGEN SCRAPER")
        print("=" * 60)
        print(f"📊 Input: {input_file}")
        print(f"🎯 Target: {max_restaurants} restaurants")
        print(f"🔬 Focus: Complete menu extraction + allergen analysis")
        print()
        
        # Load restaurant data
        input_path = self.output_dir / input_file
        if not input_path.exists():
            print(f"❌ Input file not found: {input_path}")
            return {}
        
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract restaurants
        restaurants_data = []
        if 'restaurants' in data:
            restaurants_data = data['restaurants']
        elif 'summary' in data and 'restaurants' in data['summary']:
            restaurants_data = data['summary']['restaurants']
        else:
            print(f"❌ No restaurants found in data structure")
            return {}
        
        # Setup browser
        if not await self.setup_browser():
            return {}
        
        try:
            enhanced_restaurants = []
            processed_count = 0
            success_count = 0
            total_menu_items = 0
            
            # Process restaurants
            for i, restaurant in enumerate(restaurants_data[:max_restaurants]):
                print(f"\n🏪 [{i+1}/{min(max_restaurants, len(restaurants_data))}] Processing: {restaurant.get('name', 'Unknown')}")
                
                enhanced_restaurant = await self._scrape_restaurant_menu(restaurant)
                enhanced_restaurants.append(enhanced_restaurant)
                processed_count += 1
                
                if enhanced_restaurant.get('menu_extraction_success', False):
                    success_count += 1
                    menu_items = enhanced_restaurant.get('enhanced_menu_items', [])
                    total_menu_items += len(menu_items)
                    print(f"   ✅ Success: {len(menu_items)} menu items extracted")
                else:
                    print(f"   ❌ Failed: {enhanced_restaurant.get('extraction_error', 'Unknown error')}")
                
                # Add delay between requests
                await asyncio.sleep(random.uniform(2, 4))
            
            # Generate comprehensive analysis
            analysis_summary = self._generate_comprehensive_analysis(enhanced_restaurants)
            
            # Create final dataset
            comprehensive_data = {
                "scraping_summary": {
                    "scraping_date": datetime.now().isoformat(),
                    "input_file": input_file,
                    "restaurants_processed": processed_count,
                    "successful_extractions": success_count,
                    "success_rate_percent": round((success_count / processed_count) * 100, 2) if processed_count > 0 else 0,
                    "total_menu_items_extracted": total_menu_items,
                    "average_items_per_restaurant": round(total_menu_items / success_count, 2) if success_count > 0 else 0,
                    "features": [
                        "Real menu data extraction",
                        "Advanced allergen detection",
                        "Dietary classification",
                        "Risk assessment",
                        "Nutritional analysis",
                        "Health scoring"
                    ]
                },
                "restaurants": enhanced_restaurants,
                "allergen_analysis": analysis_summary["allergen_analysis"],
                "dietary_analysis": analysis_summary["dietary_analysis"],
                "health_insights": analysis_summary["health_insights"]
            }
            
            # Save comprehensive data
            output_file = f"chicago_comprehensive_menu_allergen_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            output_path = self.output_dir / output_file
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(comprehensive_data, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"\n✅ Comprehensive menu data saved to: {output_file}")
            print(f"\n📊 FINAL SUMMARY:")
            print(f"   • Restaurants processed: {processed_count}")
            print(f"   • Successful extractions: {success_count} ({round((success_count / processed_count) * 100, 2)}%)")
            print(f"   • Total menu items: {total_menu_items}")
            print(f"   • Allergen detections: {analysis_summary['allergen_analysis']['total_allergen_detections']}")
            print(f"   • High-risk items: {analysis_summary['allergen_analysis']['high_risk_items']}")
            print(f"   • Dietary options: {analysis_summary['dietary_analysis']['total_dietary_tags']}")
            
            return comprehensive_data
            
        finally:
            if self.browser:
                await self.browser.close()
    
    async def _scrape_restaurant_menu(self, restaurant: Dict[str, Any]) -> Dict[str, Any]:
        """Scrape menu from individual restaurant"""
        enhanced_restaurant = restaurant.copy()
        
        try:
            page = await self.context.new_page()
            
            # Try to navigate to restaurant page
            restaurant_url = restaurant.get('url', '')
            if not restaurant_url:
                enhanced_restaurant.update({
                    'menu_extraction_success': False,
                    'extraction_error': 'No URL available',
                    'enhanced_menu_items': []
                })
                return enhanced_restaurant
            
            print(f"   🌐 Navigating to: {restaurant_url}")
            await page.goto(restaurant_url, wait_until='networkidle', timeout=self.timeout)
            
            # Look for menu section or navigate to menu page
            menu_items = await self._extract_menu_items(page, restaurant_url)
            
            if not menu_items:
                # Try to find and navigate to menu page
                menu_url = await self._find_menu_page(page, restaurant_url)
                if menu_url:
                    print(f"   📋 Found menu page: {menu_url}")
                    await page.goto(menu_url, wait_until='networkidle', timeout=self.timeout)
                    menu_items = await self._extract_menu_items(page, menu_url)
            
            # Process extracted menu items
            enhanced_menu_items = []
            for item in menu_items:
                enhanced_item = await self._enhance_menu_item(item, restaurant)
                enhanced_menu_items.append(enhanced_item)
            
            # Add restaurant-level analysis
            restaurant_analysis = self._analyze_restaurant_allergens(restaurant, enhanced_menu_items)
            
            enhanced_restaurant.update({
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
        """Find menu page link"""
        try:
            # Look for menu links
            for pattern in self.menu_link_patterns:
                selectors = [
                    f'a[href*="{pattern}"]',
                    f'a:has-text("{pattern}")',
                    f'button:has-text("{pattern}")',
                    f'[class*="{pattern}"] a'
                ]
                
                for selector in selectors:
                    try:
                        element = await page.query_selector(selector)
                        if element:
                            href = await element.get_attribute('href')
                            if href:
                                return urljoin(base_url, href)
                    except:
                        continue
            
            return None
            
        except Exception as e:
            print(f"   ⚠️ Error finding menu page: {e}")
            return None
    
    async def _extract_menu_items(self, page: Page, url: str) -> List[Dict[str, Any]]:
        """Extract menu items from page"""
        menu_items = []
        
        try:
            # Wait for content to load
            await asyncio.sleep(2)
            
            # Try different menu extraction strategies
            for selector in self.menu_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements and len(elements) >= 3:  # Minimum threshold for valid menu
                        print(f"   📋 Found {len(elements)} items with selector: {selector}")
                        
                        for element in elements[:50]:  # Limit to prevent overwhelming data
                            item_data = await self._extract_item_data(element)
                            if item_data and item_data.get('name'):
                                menu_items.append(item_data)
                        
                        if menu_items:
                            break  # Use first successful extraction
                            
                except Exception as e:
                    continue
            
            # If no structured menu found, try text-based extraction
            if not menu_items:
                menu_items = await self._extract_text_based_menu(page)
            
            return menu_items[:30]  # Limit to 30 items per restaurant
            
        except Exception as e:
            print(f"   ❌ Error extracting menu items: {e}")
            return []
    
    async def _extract_item_data(self, element) -> Dict[str, Any]:
        """Extract data from individual menu item element"""
        try:
            # Get text content
            text_content = await element.text_content()
            if not text_content or len(text_content.strip()) < 3:
                return {}
            
            # Extract name (usually first line or before price)
            lines = [line.strip() for line in text_content.split('\n') if line.strip()]
            if not lines:
                return {}
            
            # Find price
            price = None
            for line in lines:
                for pattern in self.price_patterns:
                    match = re.search(pattern, line)
                    if match:
                        price = match.group()
                        break
                if price:
                    break
            
            # Extract name and description
            name = lines[0]
            description = ' '.join(lines[1:]) if len(lines) > 1 else ''
            
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
            
            for match in matches[:20]:  # Limit to 20 items
                price = match.group()
                start = max(0, match.start() - 100)
                end = min(len(page_text), match.end() + 100)
                context = page_text[start:end]
                
                # Extract potential item name (text before price)
                before_price = context[:context.find(price)]
                lines = [line.strip() for line in before_price.split('\n') if line.strip()]
                
                if lines:
                    name = lines[-1]  # Last line before price is likely the name
                    if len(name) > 3 and len(name) < 80:  # Reasonable name length
                        menu_items.append({
                            'name': name,
                            'description': '',
                            'price': price,
                            'raw_text': context
                        })
            
            return menu_items
            
        except Exception as e:
            print(f"   ❌ Error in text-based extraction: {e}")
            return []
    
    async def _enhance_menu_item(self, item: Dict[str, Any], restaurant: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance menu item with allergen analysis"""
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
            'likely_high_protein': bool(re.search(r'\b(protein|chicken|beef|fish|tofu|beans|lentils|quinoa)\b', text_lower)),
            'likely_high_fat': bool(re.search(r'\b(fried|butter|oil|cream|cheese|avocado|nuts)\b', text_lower)),
            'likely_high_carb': bool(re.search(r'\b(pasta|rice|bread|potato|noodles|flour)\b', text_lower)),
            'likely_high_fiber': bool(re.search(r'\b(beans|lentils|quinoa|oats|vegetables|whole grain)\b', text_lower)),
            'likely_low_calorie': bool(re.search(r'\b(salad|steamed|grilled|light|fresh|raw)\b', text_lower)),
            'contains_vegetables': bool(re.search(r'\b(vegetables|veggie|lettuce|tomato|onion|pepper|spinach|kale)\b', text_lower)),
            'contains_fruits': bool(re.search(r'\b(apple|banana|berry|citrus|fruit|orange|strawberry)\b', text_lower)),
            'spicy_level': len(re.findall(r'\b(spicy|hot|jalapeño|habanero|sriracha|chili|pepper)\b', text_lower))
        }
    
    def _calculate_confidence_score(self, allergen_analysis, item: Dict[str, Any]) -> float:
        """Calculate confidence score for menu item analysis"""
        base_score = 0.5
        
        # Boost confidence if we have good text data
        if item.get('description') and len(item['description']) > 20:
            base_score += 0.2
        
        if item.get('name') and len(item['name']) > 5:
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
                'health_app_readiness': 'excellent' if total_menu_items > 100 and total_allergen_detections > 50 else 
                                       'good' if total_menu_items > 50 and total_allergen_detections > 20 else 
                                       'fair' if total_menu_items > 20 else 'poor'
            }
        }

async def main():
    """Main function to run comprehensive menu scraping"""
    scraper = ComprehensiveMenuScraper(headless=False)  # Set to False to see browser
    
    print("🚀 Starting Comprehensive Menu & Allergen Analysis...")
    print("This will extract real menu data and apply advanced allergen detection.\n")
    
    # Run comprehensive scraping
    result = await scraper.scrape_comprehensive_menus(
        input_file="chicago_restaurants_optimized_yelp.json",
        max_restaurants=15  # Start with 15 restaurants
    )
    
    if result:
        print("\n🎉 Comprehensive menu scraping completed successfully!")
        print("\n🏥 Health App Features Ready:")
        print("   ✅ Real menu data with allergen analysis")
        print("   ✅ Risk-based filtering and warnings")
        print("   ✅ Dietary preference matching")
        print("   ✅ Nutritional guidance hints")
        print("   ✅ Restaurant health scoring")
        print("   ✅ Comprehensive allergen database")
    else:
        print("❌ Comprehensive scraping failed.")

if __name__ == "__main__":
    asyncio.run(main())