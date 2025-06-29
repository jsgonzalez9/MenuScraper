#!/usr/bin/env python3
"""
Demo: Enhanced Chicago Restaurant Scraper with Menu Data

This script demonstrates the enhanced scraping capabilities that combine:
1. Yelp API restaurant data collection
2. Website menu scraping with allergen detection

Usage:
    python demo_menu_scraping.py
"""

import json
import os
from yelp_optimized_chicago_scraper import (
    scrape_all_chicago_restaurants_optimized,
    scrape_chicago_restaurants_with_menus
)

def demo_basic_scraping():
    """
    Demonstrate basic restaurant data collection from Yelp API
    """
    print("=== DEMO: Basic Restaurant Data Collection ===")
    print("Collecting restaurant data from Yelp API...\n")
    
    # Collect basic restaurant data (fast, API-only)
    result = scrape_all_chicago_restaurants_optimized(max_restaurants=50)
    
    print(f"✅ Collected {len(result['restaurants'])} restaurants")
    print(f"📊 API calls used: {result['summary']['scraping_summary']['api_calls_used']}")
    print(f"⭐ Average rating: {result['summary']['data_quality']['average_rating']}")
    
    # Show sample restaurant data
    sample_restaurant = result['restaurants'][0]
    print(f"\n📍 Sample Restaurant: {sample_restaurant['name']}")
    print(f"   Rating: {sample_restaurant['rating']} ({sample_restaurant['review_count']} reviews)")
    print(f"   Categories: {', '.join(sample_restaurant['categories'])}")
    print(f"   Location: {sample_restaurant['location']['display_address'][0]}")
    print(f"   Basic allergen detection: {sample_restaurant['potential_allergens']}")
    
    return result

def demo_enhanced_scraping():
    """
    Demonstrate enhanced scraping with menu data collection
    """
    print("\n=== DEMO: Enhanced Scraping with Menu Data ===")
    print("Collecting restaurant data + scraping menus...\n")
    
    # Enhanced scraping with menu data (slower, includes web scraping)
    result = scrape_chicago_restaurants_with_menus(
        max_restaurants=20,  # Smaller sample for demo
        max_menu_scrapes=5   # Only scrape 5 menus for demo
    )
    
    print(f"✅ Total restaurants: {len(result['restaurants'])}")
    print(f"🍽️ Restaurants with menus: {result['summary']['menu_scraping']['restaurants_successful']}")
    print(f"📋 Total menu items: {result['summary']['menu_scraping']['total_menu_items_collected']}")
    print(f"🥜 Restaurants with allergen data: {result['summary']['menu_scraping']['restaurants_with_allergen_data']}")
    print(f"📈 Menu scraping success rate: {result['summary']['menu_scraping']['success_rate_percent']}%")
    
    # Show restaurants with menu data
    restaurants_with_menus = [
        r for r in result['restaurants'] 
        if r.get('has_menu', False) and r.get('menu_items_count', 0) > 0
    ]
    
    if restaurants_with_menus:
        print(f"\n🎯 Restaurants with Successfully Scraped Menus:")
        for restaurant in restaurants_with_menus:
            print(f"\n📍 {restaurant['name']}")
            print(f"   Menu items: {restaurant['menu_items_count']}")
            
            # Show sample menu items
            menu_items = restaurant['menu_data']['menu_items'][:3]
            for item in menu_items:
                allergens = item.get('potential_allergens', [])
                allergen_str = f" (Allergens: {', '.join(allergens)})" if allergens else " (No allergens detected)"
                print(f"   • {item['name']} - {item.get('price', 'N/A')}{allergen_str}")
    else:
        print("\n⚠️ No menus were successfully scraped in this demo.")
        print("   This is common because:")
        print("   - Many restaurants don't have detailed menus on their Yelp pages")
        print("   - Some restaurants use external menu systems")
        print("   - Menu scraping requires visiting individual restaurant websites")
    
    return result

def show_data_structure():
    """
    Show the data structure of enhanced restaurant data
    """
    print("\n=== DATA STRUCTURE OVERVIEW ===")
    print("\nBasic Restaurant Data (from Yelp API):")
    print("├── id, name, rating, review_count")
    print("├── price, phone, url, image_url")
    print("├── categories (cuisine types)")
    print("├── location (address, coordinates)")
    print("├── transactions (delivery, pickup)")
    print("└── potential_allergens (basic detection from name/categories)")
    
    print("\nEnhanced Data (with menu scraping):")
    print("├── [All basic data above]")
    print("├── menu_data:")
    print("│   ├── menu_items[]")
    print("│   │   ├── name, description, price")
    print("│   │   ├── potential_allergens[] (detailed detection)")
    print("│   │   └── ingredients[]")
    print("│   ├── menu_url")
    print("│   ├── total_items")
    print("│   └── scraping_success")
    print("├── has_menu (boolean)")
    print("└── menu_items_count")

def show_usage_examples():
    """
    Show practical usage examples for health apps
    """
    print("\n=== USAGE EXAMPLES FOR HEALTH APPS ===")
    
    print("\n1. 🥜 Allergy-Safe Restaurant Finder:")
    print("   - Filter restaurants by allergen-free menu items")
    print("   - Alert users about potential allergens in dishes")
    print("   - Provide detailed ingredient information")
    
    print("\n2. 🍎 Nutritional Analysis:")
    print("   - Analyze menu descriptions for healthy options")
    print("   - Identify dishes with specific dietary requirements")
    print("   - Track ingredient trends across restaurants")
    
    print("\n3. 📊 Restaurant Intelligence:")
    print("   - Compare menu diversity across locations")
    print("   - Identify popular ingredients and allergens")
    print("   - Track pricing trends by cuisine type")
    
    print("\n4. 🔍 Smart Search & Recommendations:")
    print("   - Search by specific ingredients or allergens")
    print("   - Recommend restaurants based on dietary restrictions")
    print("   - Provide detailed menu previews before visiting")

def main():
    """
    Run the complete demonstration
    """
    print("🍽️ CHICAGO RESTAURANT SCRAPER DEMO")
    print("===================================\n")
    
    # Ensure output directory exists
    os.makedirs("output", exist_ok=True)
    
    # Demo 1: Basic scraping
    basic_result = demo_basic_scraping()
    
    # Demo 2: Enhanced scraping
    enhanced_result = demo_enhanced_scraping()
    
    # Show data structures
    show_data_structure()
    
    # Show usage examples
    show_usage_examples()
    
    print("\n=== DEMO COMPLETE ===")
    print("\n📁 Output Files:")
    print("   - output/chicago_restaurants_optimized_yelp.json (basic data)")
    print("   - output/chicago_restaurants_with_menus.json (enhanced data)")
    
    print("\n🚀 Next Steps:")
    print("   1. Run full collection: python yelp_optimized_chicago_scraper.py")
    print("   2. Run with menus: python yelp_optimized_chicago_scraper.py --with-menus")
    print("   3. Install Playwright: pip install playwright && playwright install")
    print("   4. Integrate data into your health app")
    
    return basic_result, enhanced_result

if __name__ == "__main__":
    main()