#!/usr/bin/env python3
"""
Test script for the enhanced menu scraper using real Chicago restaurant data
"""

import json
from enhanced_menu_scraper import EnhancedMenuScraper

def test_enhanced_scraper():
    """Test the enhanced scraper with real restaurant data"""
    
    # Load existing Chicago restaurant data
    try:
        with open('MenuScraper_Playwright/output/chicago_restaurants_with_menus.json', 'r') as f:
            data = json.load(f)
        restaurants = data.get('restaurants', [])
        print(f"📊 Loaded {len(restaurants)} restaurants from existing data")
    except FileNotFoundError:
        print("❌ Chicago restaurants data not found. Please run the basic scraper first.")
        return
    
    # Initialize enhanced scraper
    scraper = EnhancedMenuScraper()
    
    # Test with first 5 restaurants that have URLs
    test_restaurants = []
    for restaurant in restaurants:
        if restaurant.get('url') and len(test_restaurants) < 5:
            test_restaurants.append(restaurant)
    
    if not test_restaurants:
        print("❌ No restaurants with URLs found in the dataset")
        return
    
    print(f"\n🧪 Testing enhanced scraper with {len(test_restaurants)} restaurants...\n")
    
    results = []
    success_count = 0
    
    for i, restaurant in enumerate(test_restaurants, 1):
        print(f"\n{'='*60}")
        print(f"🏪 [{i}/{len(test_restaurants)}] Testing: {restaurant['name']}")
        print(f"🌐 URL: {restaurant.get('url', 'N/A')}")
        print(f"⭐ Rating: {restaurant.get('rating', 'N/A')}")
        print(f"💰 Price: {restaurant.get('price', 'N/A')}")
        print(f"📍 Location: {restaurant.get('location', {}).get('address1', 'N/A')}")
        
        try:
            # Use Playwright to scrape menu using enhanced method
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                
                # Scrape menu using enhanced method
                menu_data = scraper.enhanced_menu_detection(page, restaurant.get('url'))
                
                # Update restaurant data with menu information
                restaurant.update(menu_data)
                results.append(restaurant)
                
                browser.close()
            
            if menu_data.get('scraping_success'):
                success_count += 1
                print(f"✅ Success! Found {menu_data.get('total_items', 0)} menu items")
                if menu_data.get('ocr_used'):
                    print(f"📸 OCR was used for extraction")
            else:
                print(f"❌ No menu items found")
                
        except Exception as e:
            print(f"💥 Error scraping {restaurant['name']}: {str(e)}")
            restaurant['scraping_success'] = False
            restaurant['error'] = str(e)
            results.append(restaurant)
    
    # Calculate and display results
    success_rate = (success_count / len(test_restaurants)) * 100
    total_menu_items = sum(r.get('total_items', 0) for r in results)
    
    print(f"\n{'='*60}")
    print(f"📊 ENHANCED SCRAPER TEST RESULTS")
    print(f"{'='*60}")
    print(f"🏪 Restaurants tested: {len(test_restaurants)}")
    print(f"✅ Successful extractions: {success_count}")
    print(f"📈 Success rate: {success_rate:.1f}%")
    print(f"🍽️ Total menu items found: {total_menu_items}")
    print(f"📊 Average items per successful restaurant: {total_menu_items/success_count if success_count > 0 else 0:.1f}")
    
    # Show OCR usage statistics
    ocr_used_count = sum(1 for r in results if r.get('ocr_used'))
    print(f"📸 OCR used in: {ocr_used_count} extractions")
    
    # Save enhanced results
    output_file = 'MenuScraper_Playwright/output/enhanced_scraper_test_results.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n💾 Results saved to: {output_file}")
    
    # Show sample menu items from successful extractions
    print(f"\n🍽️ SAMPLE MENU ITEMS:")
    print(f"{'='*60}")
    for restaurant in results:
        if restaurant.get('scraping_success') and restaurant.get('menu_items'):
            print(f"\n🏪 {restaurant['name']}:")
            for item in restaurant['menu_items'][:3]:  # Show first 3 items
                name = item.get('name', 'Unknown')
                price = item.get('price', 'N/A')
                description = item.get('description', '')[:50] + '...' if len(item.get('description', '')) > 50 else item.get('description', '')
                print(f"  • {name} - {price}")
                if description:
                    print(f"    {description}")
    
    print(f"\n🎉 Enhanced scraper test completed!")

if __name__ == "__main__":
    test_enhanced_scraper()