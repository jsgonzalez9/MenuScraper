#!/usr/bin/env python3
"""
Optimized Yelp API Chicago Restaurant Scraper
Uses geographic grid and category-based searches for comprehensive coverage
"""

import json
import time
import re
from datetime import datetime
import os
from typing import Dict, List, Any, Optional
import math
import requests
from playwright.sync_api import sync_playwright
from urllib.parse import urljoin, urlparse

# Yelp API Configuration
YELP_API_KEY = "Bearer zU4pq53bDewtRNwTweR_mJ2iJDjdsIJ-_iFXYfdE03-VwhJOka86zLJJMHzuKsPWpLl6QTsa2a9U6k0MuHtOoTHO796Hlw8uKIYLuRLsgw5huQAer6_1rGfcLcteaHYx"
YELP_CLIENT_ID = "sp7S-eWCMScZAacAvwz4kA"
YELP_BASE_URL = "https://api.yelp.com/v3"

# Chicago geographic boundaries
CHICAGO_BOUNDS = {
    "north": 42.0230,
    "south": 41.6445,
    "east": -87.5240,
    "west": -87.9400
}

# Restaurant categories to search
RESTAURANT_CATEGORIES = [
    "restaurants",
    "food",
    "bars",
    "cafes",
    "pizza",
    "chinese",
    "mexican",
    "italian",
    "indian",
    "thai",
    "japanese",
    "american",
    "mediterranean",
    "fastfood",
    "breakfast_brunch",
    "delis",
    "bakeries",
    "seafood",
    "steakhouses",
    "vegetarian",
    "vegan"
]

# Common allergens to look for
COMMON_ALLERGENS = [
    "peanuts", "tree nuts", "milk", "eggs", "wheat", "soy", "fish", "shellfish",
    "sesame", "gluten", "dairy", "nuts", "lactose", "casein", "whey"
]

def extract_allergen_info(text: str) -> List[str]:
    """
    Extract potential allergen information from text
    """
    if not text:
        return []
    
    common_allergens = {
        'dairy': ['milk', 'cheese', 'butter', 'cream', 'yogurt', 'dairy'],
        'eggs': ['egg', 'eggs', 'mayonnaise', 'mayo'],
        'fish': ['fish', 'salmon', 'tuna', 'cod', 'halibut', 'sea bass'],
        'shellfish': ['shrimp', 'crab', 'lobster', 'oyster', 'mussel', 'clam', 'scallop'],
        'tree_nuts': ['almond', 'walnut', 'pecan', 'cashew', 'pistachio', 'hazelnut', 'pine nut'],
        'peanuts': ['peanut', 'peanuts'],
        'wheat': ['wheat', 'flour', 'bread', 'pasta', 'noodles', 'croutons'],
        'soy': ['soy', 'tofu', 'edamame', 'miso'],
        'sesame': ['sesame', 'tahini']
    }
    
    detected_allergens = []
    text_lower = text.lower()
    
    for allergen, keywords in common_allergens.items():
        if any(keyword in text_lower for keyword in keywords):
            detected_allergens.append(allergen)
    
    return detected_allergens

def extract_ingredients(text: str) -> List[str]:
    """
    Extract ingredients from menu item description
    """
    ingredient_patterns = [
        r'with ([^,\.]+)',
        r'served with ([^,\.]+)',
        r'topped with ([^,\.]+)',
        r'includes ([^,\.]+)',
        r'contains ([^,\.]+)'
    ]
    
    ingredients = []
    for pattern in ingredient_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        ingredients.extend(matches)
    
    cleaned_ingredients = []
    for ingredient in ingredients:
        ingredient = ingredient.strip()
        if len(ingredient) > 2 and len(ingredient) < 50:
            cleaned_ingredients.append(ingredient)
    
    return cleaned_ingredients

def make_yelp_request(endpoint: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Make a request to the Yelp API with error handling
    """
    headers = {
        "Authorization": YELP_API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(f"{YELP_BASE_URL}/{endpoint}", headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error making Yelp API request: {e}")
        return None

def search_restaurants_by_location(latitude: float, longitude: float, radius: int = 5000, 
                                 category: str = "restaurants", limit: int = 50, offset: int = 0) -> Optional[Dict[str, Any]]:
    """
    Search for restaurants at a specific location
    """
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "radius": radius,
        "categories": category,
        "limit": limit,
        "offset": offset,
        "sort_by": "best_match"
    }
    
    return make_yelp_request("businesses/search", params)

def get_business_details(business_id: str) -> Optional[Dict[str, Any]]:
    """
    Get detailed information about a specific business
    """
    return make_yelp_request(f"businesses/{business_id}", {})

def generate_grid_coordinates(bounds: Dict[str, float], grid_size: int = 10) -> List[tuple]:
    """
    Generate a grid of coordinates to search within Chicago bounds
    """
    lat_step = (bounds["north"] - bounds["south"]) / grid_size
    lng_step = (bounds["east"] - bounds["west"]) / grid_size
    
    coordinates = []
    for i in range(grid_size):
        for j in range(grid_size):
            lat = bounds["south"] + (i + 0.5) * lat_step
            lng = bounds["west"] + (j + 0.5) * lng_step
            coordinates.append((lat, lng))
    
    return coordinates

def scrape_restaurant_menu(page, restaurant_url: str, restaurant_name: str, max_retries: int = 2) -> Dict[str, Any]:
    """
    Scrape menu information from a restaurant's website
    """
    for attempt in range(max_retries):
        try:
            print(f"    Scraping menu from: {restaurant_url}")
            
            # Navigate to restaurant page
            page.goto(restaurant_url, timeout=30000)
            page.wait_for_load_state('networkidle', timeout=15000)
            
            # Look for menu links and navigate to menu page
            menu_url = None
            menu_selectors = [
                'a[href*="menu"]',
                'a:has-text("Menu")',
                'a:has-text("View Menu")',
                'button:has-text("Menu")',
                '[data-test*="menu"]'
            ]
            
            for selector in menu_selectors:
                try:
                    menu_link = page.locator(selector).first
                    if menu_link.is_visible():
                        menu_url = menu_link.get_attribute('href')
                        if menu_url:
                            menu_url = urljoin(restaurant_url, menu_url)
                            page.goto(menu_url, timeout=20000)
                            page.wait_for_load_state('networkidle', timeout=10000)
                            break
                except:
                    continue
            
            # Extract menu items using multiple strategies
            menu_items = []
            
            # Strategy 1: Look for structured menu items
            menu_item_selectors = [
                '[class*="menu-item"]',
                '[data-test*="menu-item"]',
                '.menu-item',
                '.dish',
                '.food-item',
                '[class*="dish"]',
                '[class*="item"][class*="food"]'
            ]
            
            for selector in menu_item_selectors:
                try:
                    items = page.locator(selector).all()
                    if len(items) > 0:
                        for item in items[:15]:  # Limit to 15 items
                            try:
                                item_text = item.inner_text().strip()
                                if len(item_text) > 10:
                                    # Extract price
                                    price_match = re.search(r'\$([0-9]+(?:\.[0-9]{2})?)', item_text)
                                    price = f"${price_match.group(1)}" if price_match else None
                                    
                                    # Clean description
                                    description = re.sub(r'\$[0-9]+(?:\.[0-9]{2})?', '', item_text).strip()
                                    
                                    # Extract allergens and ingredients
                                    allergens = extract_allergen_info(description)
                                    ingredients = extract_ingredients(description)
                                    
                                    menu_items.append({
                                        'name': description.split('.')[0].strip()[:50],
                                        'description': description,
                                        'price': price,
                                        'potential_allergens': allergens,
                                        'ingredients': ingredients
                                    })
                            except:
                                continue
                        break
                except:
                    continue
            
            # Strategy 2: Price-based extraction if no structured items found
            if len(menu_items) == 0:
                page_text = page.inner_text('body')
                price_patterns = [
                    r'([A-Z][^$\n]{15,100})\s*\$([0-9]+(?:\.[0-9]{2})?)',
                    r'([^$\n]{20,80}(?:chicken|beef|fish|pasta|salad|soup|pizza|burger|sandwich|steak|seafood|vegetarian|dessert|appetizer)[^$\n]{0,30})\s*\$([0-9]+(?:\.[0-9]{2})?)'
                ]
                
                for pattern in price_patterns:
                    matches = re.findall(pattern, page_text, re.MULTILINE | re.IGNORECASE)
                    for description, price in matches[:10]:
                        description = description.strip()
                        
                        if (len(description) > 15 and 
                            not any(word in description.lower() for word in ['copyright', 'privacy', 'terms', 'contact']) and
                            any(word in description.lower() for word in ['chicken', 'beef', 'fish', 'pasta', 'salad', 'soup', 'pizza', 'burger', 'sandwich', 'steak', 'seafood'])):
                            
                            allergens = extract_allergen_info(description)
                            ingredients = extract_ingredients(description)
                            
                            menu_items.append({
                                'name': description.split('.')[0].strip()[:50],
                                'description': description,
                                'price': f'${price}',
                                'potential_allergens': allergens,
                                'ingredients': ingredients
                            })
                    
                    if len(menu_items) > 0:
                        break
            
            return {
                'menu_items': menu_items,
                'menu_url': menu_url,
                'total_items': len(menu_items),
                'scraping_success': len(menu_items) > 0
            }
            
        except Exception as e:
            print(f"    Menu scraping attempt {attempt + 1} failed: {str(e)}")
            if attempt == max_retries - 1:
                return {
                    'menu_items': [],
                    'menu_url': None,
                    'total_items': 0,
                    'scraping_success': False,
                    'error': str(e)
                }
            time.sleep(2)

def scrape_all_chicago_restaurants_optimized(max_restaurants: int = 10000) -> Dict[str, Any]:
    """
    Optimized scraping of Chicago restaurants using multiple strategies
    """
    print("Starting optimized Chicago restaurant scraping...")
    start_time = datetime.now()
    
    all_restaurants = {}
    api_calls_used = 0
    
    # Strategy 1: Grid-based search
    print("\n=== Strategy 1: Grid-based Geographic Search ===")
    grid_coordinates = generate_grid_coordinates(CHICAGO_BOUNDS, grid_size=8)
    
    for i, (lat, lng) in enumerate(grid_coordinates):
        if len(all_restaurants) >= max_restaurants:
            break
            
        print(f"Searching grid point {i+1}/{len(grid_coordinates)}: ({lat:.4f}, {lng:.4f})")
        
        # Search with pagination
        offset = 0
        while offset < 1000:  # Yelp limit
            result = search_restaurants_by_location(lat, lng, radius=3000, limit=50, offset=offset)
            api_calls_used += 1
            
            if not result or "businesses" not in result:
                break
                
            businesses = result["businesses"]
            if not businesses:
                break
                
            for business in businesses:
                business_id = business.get("id")
                if business_id and business_id not in all_restaurants:
                    # Extract basic info
                    restaurant_data = {
                        "id": business_id,
                        "name": business.get("name", ""),
                        "rating": business.get("rating", 0),
                        "review_count": business.get("review_count", 0),
                        "price": business.get("price", ""),
                        "phone": business.get("phone", ""),
                        "url": business.get("url", ""),
                        "image_url": business.get("image_url", ""),
                        "categories": [cat.get("title", "") for cat in business.get("categories", [])],
                        "location": business.get("location", {}),
                        "coordinates": business.get("coordinates", {}),
                        "transactions": business.get("transactions", []),
                        "is_closed": business.get("is_closed", False),
                        "potential_allergens": extract_allergen_info(business.get("name", "") + " " + " ".join([cat.get("title", "") for cat in business.get("categories", [])]))
                    }
                    
                    all_restaurants[business_id] = restaurant_data
                    
            if len(businesses) < 50:
                break
                
            offset += 50
            time.sleep(0.1)  # Rate limiting
            
        print(f"  Found {len(all_restaurants)} unique restaurants so far")
        time.sleep(0.2)  # Rate limiting between grid points
    
    # Strategy 2: Category-based search
    print("\n=== Strategy 2: Category-based Search ===")
    chicago_center = (41.8781, -87.6298)  # Chicago downtown
    
    for category in RESTAURANT_CATEGORIES:
        if len(all_restaurants) >= max_restaurants:
            break
            
        print(f"Searching category: {category}")
        
        offset = 0
        while offset < 1000:  # Yelp limit
            result = search_restaurants_by_location(
                chicago_center[0], chicago_center[1], 
                radius=25000,  # 25km radius to cover most of Chicago
                category=category, 
                limit=50, 
                offset=offset
            )
            api_calls_used += 1
            
            if not result or "businesses" not in result:
                break
                
            businesses = result["businesses"]
            if not businesses:
                break
                
            new_restaurants = 0
            for business in businesses:
                business_id = business.get("id")
                if business_id and business_id not in all_restaurants:
                    restaurant_data = {
                        "id": business_id,
                        "name": business.get("name", ""),
                        "rating": business.get("rating", 0),
                        "review_count": business.get("review_count", 0),
                        "price": business.get("price", ""),
                        "phone": business.get("phone", ""),
                        "url": business.get("url", ""),
                        "image_url": business.get("image_url", ""),
                        "categories": [cat.get("title", "") for cat in business.get("categories", [])],
                        "location": business.get("location", {}),
                        "coordinates": business.get("coordinates", {}),
                        "transactions": business.get("transactions", []),
                        "is_closed": business.get("is_closed", False),
                        "potential_allergens": extract_allergen_info(business.get("name", "") + " " + " ".join([cat.get("title", "") for cat in business.get("categories", [])]))
                    }
                    
                    all_restaurants[business_id] = restaurant_data
                    new_restaurants += 1
                    
            if len(businesses) < 50 or new_restaurants == 0:
                break
                
            offset += 50
            time.sleep(0.1)  # Rate limiting
            
        print(f"  Category {category}: {len(all_restaurants)} total restaurants")
        time.sleep(0.2)  # Rate limiting between categories
    
    # Calculate statistics
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    # Rating distribution
    ratings = [r["rating"] for r in all_restaurants.values() if r["rating"] > 0]
    avg_rating = sum(ratings) / len(ratings) if ratings else 0
    
    # Price distribution
    price_counts = {}
    for restaurant in all_restaurants.values():
        price = restaurant.get("price", "Unknown")
        price_counts[price] = price_counts.get(price, 0) + 1
    
    # Category distribution (top 10)
    category_counts = {}
    for restaurant in all_restaurants.values():
        for category in restaurant.get("categories", []):
            category_counts[category] = category_counts.get(category, 0) + 1
    
    top_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # Prepare summary
    summary = {
        "scraping_summary": {
            "total_restaurants": len(all_restaurants),
            "location": "Chicago, Illinois",
            "scraping_method": "Optimized Yelp Fusion API (Grid + Category)",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
            "api_calls_used": api_calls_used,
            "estimated_daily_limit_remaining": 5000 - api_calls_used,
            "estimated_chicago_coverage_percent": min(100, (len(all_restaurants) / 8000) * 100)
        },
        "data_quality": {
            "average_rating": round(avg_rating, 2),
            "restaurants_with_ratings": len(ratings),
            "price_distribution": price_counts,
            "top_categories": top_categories
        },
        "restaurants": list(all_restaurants.values())[:5]  # Sample of first 5 restaurants
    }
    
    # Save to file
    os.makedirs("output", exist_ok=True)
    output_file = "output/chicago_restaurants_optimized_yelp.json"
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "summary": summary,
            "all_restaurants": list(all_restaurants.values())
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n=== Scraping Complete ===")
    print(f"Total restaurants collected: {len(all_restaurants)}")
    print(f"API calls used: {api_calls_used}")
    print(f"Duration: {duration:.1f} seconds")
    print(f"Average rating: {avg_rating:.2f}")
    print(f"Data saved to: {output_file}")
    
    return {
        "summary": summary,
        "restaurants": list(all_restaurants.values())
    }

def scrape_chicago_restaurants_with_menus(max_restaurants: int = 100, max_menu_scrapes: int = 20) -> Dict[str, Any]:
    """
    Enhanced scraping that combines Yelp API data with menu scraping
    """
    print("Starting enhanced Chicago restaurant scraping with menu data...")
    start_time = datetime.now()
    
    # First, get restaurant data from Yelp API
    print("\n=== Phase 1: Collecting Restaurant Data from Yelp API ===")
    yelp_data = scrape_all_chicago_restaurants_optimized(max_restaurants)
    restaurants = yelp_data["restaurants"]
    
    print(f"\n=== Phase 2: Scraping Menus from Restaurant Websites ===")
    print(f"Attempting to scrape menus from {min(max_menu_scrapes, len(restaurants))} restaurants...")
    
    enhanced_restaurants = []
    menu_scraping_stats = {
        "attempted": 0,
        "successful": 0,
        "total_menu_items": 0,
        "restaurants_with_allergen_data": 0
    }
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            for i, restaurant in enumerate(restaurants[:max_menu_scrapes]):
                print(f"\nRestaurant {i+1}/{min(max_menu_scrapes, len(restaurants))}: {restaurant['name']}")
                
                # Try to scrape menu from restaurant's website
                restaurant_url = restaurant.get('url', '')
                if restaurant_url and 'yelp.com' in restaurant_url:
                    menu_scraping_stats["attempted"] += 1
                    
                    menu_data = scrape_restaurant_menu(page, restaurant_url, restaurant['name'])
                    
                    # Enhance restaurant data with menu information
                    enhanced_restaurant = restaurant.copy()
                    enhanced_restaurant.update({
                        'menu_data': menu_data,
                        'has_menu': menu_data['scraping_success'],
                        'menu_items_count': menu_data['total_items']
                    })
                    
                    if menu_data['scraping_success']:
                        menu_scraping_stats["successful"] += 1
                        menu_scraping_stats["total_menu_items"] += menu_data['total_items']
                        
                        # Check if any menu items have allergen data
                        has_allergen_data = any(
                            item.get('potential_allergens') 
                            for item in menu_data['menu_items']
                        )
                        if has_allergen_data:
                            menu_scraping_stats["restaurants_with_allergen_data"] += 1
                        
                        print(f"    ✅ Successfully scraped {menu_data['total_items']} menu items")
                    else:
                        print(f"    ❌ Menu scraping failed")
                    
                    enhanced_restaurants.append(enhanced_restaurant)
                    time.sleep(2)  # Rate limiting
                else:
                    # Add restaurant without menu data
                    enhanced_restaurant = restaurant.copy()
                    enhanced_restaurant.update({
                        'menu_data': {'menu_items': [], 'total_items': 0, 'scraping_success': False},
                        'has_menu': False,
                        'menu_items_count': 0
                    })
                    enhanced_restaurants.append(enhanced_restaurant)
        
        finally:
            browser.close()
    
    # Add remaining restaurants without menu scraping
    for restaurant in restaurants[max_menu_scrapes:]:
        enhanced_restaurant = restaurant.copy()
        enhanced_restaurant.update({
            'menu_data': {'menu_items': [], 'total_items': 0, 'scraping_success': False},
            'has_menu': False,
            'menu_items_count': 0
        })
        enhanced_restaurants.append(enhanced_restaurant)
    
    # Calculate enhanced statistics
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    # Update summary with menu scraping stats
    enhanced_summary = yelp_data["summary"].copy()
    enhanced_summary["menu_scraping"] = {
        "restaurants_attempted": menu_scraping_stats["attempted"],
        "restaurants_successful": menu_scraping_stats["successful"],
        "success_rate_percent": round((menu_scraping_stats["successful"] / max(menu_scraping_stats["attempted"], 1)) * 100, 1),
        "total_menu_items_collected": menu_scraping_stats["total_menu_items"],
        "restaurants_with_allergen_data": menu_scraping_stats["restaurants_with_allergen_data"],
        "enhanced_scraping_duration_seconds": duration
    }
    
    return {
        "summary": enhanced_summary,
        "restaurants": enhanced_restaurants
    }

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--with-menus":
        print("Starting enhanced Chicago restaurant scraping with menu data...")
        result = scrape_chicago_restaurants_with_menus(max_restaurants=100, max_menu_scrapes=20)
        output_file = "output/chicago_restaurants_with_menus.json"
        
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2)
        
        print(f"\n=== ENHANCED SCRAPING COMPLETE ===")
        print(f"Results saved to: {output_file}")
        print(f"Total restaurants: {len(result['restaurants'])}")
        print(f"Restaurants with menus: {result['summary']['menu_scraping']['restaurants_successful']}")
        print(f"Total menu items: {result['summary']['menu_scraping']['total_menu_items_collected']}")
        print(f"Menu scraping success rate: {result['summary']['menu_scraping']['success_rate_percent']}%")
    else:
        # Update API key before running
        if "YOUR_YELP_API_KEY_HERE" in YELP_API_KEY:
            print("Please update YELP_API_KEY with your actual API key")
            print("Get your API key from: https://www.yelp.com/developers/v3/manage_app")
        else:
            result = scrape_all_chicago_restaurants_optimized(max_restaurants=5000)
            print("\nScraping completed successfully!")
            print(f"Collected {result['summary']['scraping_summary']['total_restaurants']} restaurants")
            print(f"\nTo scrape with menu data, run: python yelp_optimized_chicago_scraper.py --with-menus")