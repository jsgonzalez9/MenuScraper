from playwright.sync_api import sync_playwright
import json
import os
import time
import re

os.makedirs("output", exist_ok=True)

def extract_menu_items_from_text(page_text):
    """Extract potential menu items from page text using patterns"""
    menu_items = []
    
    # Look for price patterns with food descriptions
    price_patterns = [
        r'([A-Z][^$]*?)\s*\$([0-9]+(?:\.[0-9]{2})?)',  # Description $price
        r'([^$\n]{10,80})\s*\$([0-9]+(?:\.[0-9]{2})?)',  # Longer description $price
    ]
    
    for pattern in price_patterns:
        matches = re.findall(pattern, page_text, re.MULTILINE | re.IGNORECASE)
        for description, price in matches:
            description = description.strip()
            # Filter out non-food items
            if (len(description) > 5 and 
                not any(word in description.lower() for word in ['copyright', 'privacy', 'terms', 'contact', 'about', 'login', 'sign']) and
                any(word in description.lower() for word in ['chicken', 'beef', 'fish', 'pasta', 'salad', 'soup', 'pizza', 'burger', 'sandwich', 'steak', 'seafood', 'vegetarian', 'dessert', 'appetizer'])):
                
                menu_items.append({
                    'text': description,
                    'price': f'${price}',
                    'section': 'Menu'
                })
    
    return menu_items[:10]  # Limit to 10 items

def scrape_restaurant_menu_simple(page, restaurant_url):
    """Simple menu extraction from a restaurant page"""
    try:
        print(f"  Visiting: {restaurant_url}")
        page.goto(restaurant_url, timeout=30000)
        page.wait_for_load_state('networkidle', timeout=15000)
        
        # Get page text content
        page_text = page.inner_text('body')
        
        # Extract menu items
        menu_items = extract_menu_items_from_text(page_text)
        
        # Try to get restaurant name from title or h1
        restaurant_name = None
        try:
            restaurant_name = page.title()
            if not restaurant_name or len(restaurant_name) > 100:
                restaurant_name = page.inner_text('h1').strip()
        except:
            restaurant_name = "Unknown Restaurant"
        
        # Try to detect cuisine type from page content
        cuisine_keywords = {
            'italian': ['pasta', 'pizza', 'italian', 'risotto', 'gelato'],
            'mexican': ['tacos', 'burrito', 'mexican', 'salsa', 'guacamole'],
            'asian': ['sushi', 'ramen', 'asian', 'noodles', 'rice'],
            'american': ['burger', 'steak', 'bbq', 'american', 'fries'],
            'french': ['french', 'croissant', 'baguette', 'wine', 'cheese']
        }
        
        cuisine_type = "Unknown"
        page_text_lower = page_text.lower()
        for cuisine, keywords in cuisine_keywords.items():
            if sum(1 for keyword in keywords if keyword in page_text_lower) >= 2:
                cuisine_type = cuisine.title()
                break
        
        return {
            'restaurant_name': restaurant_name,
            'restaurant_url': restaurant_url,
            'cuisine_type': cuisine_type,
            'menu_items': menu_items,
            'menu_sections': list(set(item['section'] for item in menu_items)) if menu_items else [],
            'extraction_method': 'text_pattern_matching'
        }
        
    except Exception as e:
        print(f"  Error extracting menu: {str(e)}")
        return {
            'restaurant_name': 'Unknown',
            'restaurant_url': restaurant_url,
            'cuisine_type': 'Unknown',
            'menu_items': [],
            'menu_sections': [],
            'extraction_method': 'failed',
            'error': str(e)
        }

def scrape_simple_menus():
    """Simple menu scraper that works with basic restaurant websites"""
    
    print("=== SIMPLE MENU SCRAPER ===")
    print("This scraper demonstrates menu extraction from restaurant websites.")
    
    # Test with a few well-known restaurant websites that are likely to work
    test_restaurants = [
        "https://www.mcdonalds.com/us/en-us/full-menu.html",
        "https://www.subway.com/en-us/menunutrition/menu",
        "https://www.dominos.com/en/pages/order/menu"
    ]
    
    results = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=1000)
        page = browser.new_page()
        
        for i, url in enumerate(test_restaurants, 1):
            print(f"\nProcessing restaurant {i}/{len(test_restaurants)}")
            
            try:
                result = scrape_restaurant_menu_simple(page, url)
                result['index'] = i
                results.append(result)
                
                print(f"  ✅ Found {len(result['menu_items'])} menu items")
                
                # Brief pause between requests
                time.sleep(2)
                
            except Exception as e:
                print(f"  ❌ Failed to process: {str(e)}")
                results.append({
                    'restaurant_name': 'Failed',
                    'restaurant_url': url,
                    'error': str(e),
                    'index': i
                })
        
        browser.close()
    
    # Save results
    output_file = "output/simple_menu_scraping.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    successful = [r for r in results if 'error' not in r and r.get('menu_items')]
    total_items = sum(len(r.get('menu_items', [])) for r in successful)
    
    print(f"\n=== RESULTS SUMMARY ===")
    print(f"Restaurants processed: {len(results)}")
    print(f"Successful extractions: {len(successful)}")
    print(f"Total menu items found: {total_items}")
    print(f"Results saved to: {output_file}")
    
    # Show sample items
    if successful:
        print(f"\n=== SAMPLE MENU ITEMS ===")
        for result in successful[:2]:  # Show first 2 successful restaurants
            print(f"\n{result['restaurant_name']} ({result['cuisine_type']})")
            for item in result['menu_items'][:3]:  # Show first 3 items
                print(f"  • {item['text']} - {item['price']}")
    
    return results

if __name__ == "__main__":
    print("Starting simple menu scraper...")
    print("This will attempt to extract menu information from restaurant websites.")
    print("Note: Some sites may block automated access or have anti-bot measures.\n")
    
    results = scrape_simple_menus()
    
    print(f"\n=== MENU SCRAPING COMPLETE ===")
    print("Check the output/simple_menu_scraping.json file for detailed results.")
    print("\nThis demonstrates the concept of menu extraction.")
    print("For production use, you would need to handle:")
    print("• Rate limiting and respectful scraping")
    print("• Website-specific selectors and patterns")
    print("• Anti-bot detection and captchas")
    print("• Dynamic content loading")