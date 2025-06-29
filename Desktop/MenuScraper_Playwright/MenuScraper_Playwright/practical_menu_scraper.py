from playwright.sync_api import sync_playwright
import json
import os
import time
import re

os.makedirs("output", exist_ok=True)

def extract_allergen_info(text):
    """Extract potential allergen information from menu item text"""
    common_allergens = {
        'dairy': ['milk', 'cheese', 'butter', 'cream', 'yogurt', 'dairy', 'mozzarella', 'cheddar', 'parmesan'],
        'eggs': ['egg', 'eggs', 'mayonnaise', 'mayo'],
        'fish': ['fish', 'salmon', 'tuna', 'cod', 'halibut', 'sea bass', 'mahi'],
        'shellfish': ['shrimp', 'crab', 'lobster', 'oyster', 'mussel', 'clam', 'scallop'],
        'tree_nuts': ['almond', 'walnut', 'pecan', 'cashew', 'pistachio', 'hazelnut', 'pine nut'],
        'peanuts': ['peanut', 'peanuts'],
        'wheat': ['wheat', 'flour', 'bread', 'pasta', 'noodles', 'croutons', 'bun', 'roll'],
        'soy': ['soy', 'tofu', 'edamame', 'miso'],
        'sesame': ['sesame', 'tahini']
    }
    
    detected_allergens = []
    text_lower = text.lower()
    
    for allergen, keywords in common_allergens.items():
        if any(keyword in text_lower for keyword in keywords):
            detected_allergens.append(allergen)
    
    return detected_allergens

def extract_dietary_info(text):
    """Extract dietary information from menu item text"""
    dietary_keywords = {
        'vegetarian': ['vegetarian', 'veggie'],
        'vegan': ['vegan'],
        'gluten-free': ['gluten-free', 'gluten free', 'gf'],
        'dairy-free': ['dairy-free', 'dairy free', 'lactose-free'],
        'keto': ['keto', 'ketogenic', 'low-carb'],
        'paleo': ['paleo'],
        'organic': ['organic']
    }
    
    dietary_info = []
    text_lower = text.lower()
    
    for diet, keywords in dietary_keywords.items():
        if any(keyword in text_lower for keyword in keywords):
            dietary_info.append(diet)
    
    return dietary_info

def scrape_simple_restaurant_menu(page, restaurant_name, restaurant_url):
    """Scrape menu from accessible restaurant websites"""
    try:
        print(f"  Scraping: {restaurant_name}")
        page.goto(restaurant_url, timeout=30000)
        page.wait_for_load_state('networkidle', timeout=10000)
        
        # Get all text content
        page_text = page.inner_text('body')
        
        # Extract menu items using price patterns
        menu_items = []
        
        # Pattern 1: Description followed by price
        price_patterns = [
            r'([A-Z][^$\n]{20,120})\s*\$([0-9]+(?:\.[0-9]{2})?)',
            r'([^$\n]{15,100}(?:chicken|beef|fish|pasta|salad|soup|pizza|burger|sandwich|steak|seafood|vegetarian|dessert|appetizer|wings|fries|rice|noodles)[^$\n]{0,50})\s*\$([0-9]+(?:\.[0-9]{2})?)',
        ]
        
        for pattern in price_patterns:
            matches = re.findall(pattern, page_text, re.MULTILINE | re.IGNORECASE)
            for description, price in matches:
                description = description.strip()
                
                # Filter out non-food items
                exclude_words = ['copyright', 'privacy', 'terms', 'contact', 'about', 'login', 'sign', 'reservation', 'table', 'delivery', 'pickup', 'order online']
                include_words = ['chicken', 'beef', 'fish', 'pasta', 'salad', 'soup', 'pizza', 'burger', 'sandwich', 'steak', 'seafood', 'vegetarian', 'dessert', 'appetizer', 'wings', 'fries', 'rice', 'noodles', 'cheese', 'bacon', 'served', 'grilled', 'fried', 'baked', 'roasted']
                
                if (len(description) > 10 and 
                    not any(word in description.lower() for word in exclude_words) and
                    any(word in description.lower() for word in include_words)):
                    
                    # Extract name (first part before comma or period)
                    name_parts = re.split(r'[,\.]', description)
                    item_name = name_parts[0].strip()[:60]
                    
                    # Extract allergens and dietary info
                    allergens = extract_allergen_info(description)
                    dietary = extract_dietary_info(description)
                    
                    # Extract ingredients (words between common prepositions)
                    ingredient_pattern = r'(?:with|topped|served|includes|contains)\s+([^,\.\n]+)'
                    ingredient_matches = re.findall(ingredient_pattern, description, re.IGNORECASE)
                    ingredients = [ing.strip() for ing in ingredient_matches if len(ing.strip()) > 2]
                    
                    menu_items.append({
                        'name': item_name,
                        'description': description,
                        'price': f'${price}',
                        'potential_allergens': allergens,
                        'dietary_info': dietary,
                        'ingredients': ingredients[:5],  # Limit to 5 ingredients
                        'section': 'Menu'
                    })
        
        # Remove duplicates based on name
        seen_names = set()
        unique_items = []
        for item in menu_items:
            if item['name'].lower() not in seen_names:
                seen_names.add(item['name'].lower())
                unique_items.append(item)
        
        return unique_items[:15]  # Limit to 15 items
        
    except Exception as e:
        print(f"    Error: {str(e)}")
        return []

def scrape_practical_menus():
    """Scrape menus from accessible restaurant chains"""
    
    print("=== PRACTICAL MENU SCRAPER FOR HEALTH APP ===")
    print("Extracting real menu data with allergen information\n")
    
    # Test with accessible restaurant websites
    test_restaurants = [
        {
            'name': 'Chipotle Mexican Grill',
            'url': 'https://chipotle.com/menu',
            'cuisine': 'Mexican'
        },
        {
            'name': 'Panera Bread',
            'url': 'https://www.panerabread.com/en-us/menu.html',
            'cuisine': 'American Bakery'
        },
        {
            'name': 'Subway',
            'url': 'https://www.subway.com/en-us/menunutrition/menu',
            'cuisine': 'Sandwiches'
        }
    ]
    
    all_results = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=1000)
        page = browser.new_page()
        
        for i, restaurant in enumerate(test_restaurants, 1):
            print(f"Restaurant {i}/{len(test_restaurants)}: {restaurant['name']}")
            
            try:
                menu_items = scrape_simple_restaurant_menu(page, restaurant['name'], restaurant['url'])
                
                if menu_items:
                    # Calculate allergen summary
                    allergen_counts = {}
                    dietary_counts = {}
                    
                    for item in menu_items:
                        for allergen in item['potential_allergens']:
                            allergen_counts[allergen] = allergen_counts.get(allergen, 0) + 1
                        for dietary in item['dietary_info']:
                            dietary_counts[dietary] = dietary_counts.get(dietary, 0) + 1
                    
                    restaurant_data = {
                        'restaurant_name': restaurant['name'],
                        'restaurant_url': restaurant['url'],
                        'cuisine_type': restaurant['cuisine'],
                        'menu_items': menu_items,
                        'total_items': len(menu_items),
                        'allergen_summary': allergen_counts,
                        'dietary_summary': dietary_counts,
                        'extraction_method': 'practical_text_extraction',
                        'index': i
                    }
                    
                    all_results.append(restaurant_data)
                    print(f"  ✅ Extracted {len(menu_items)} menu items")
                else:
                    print(f"  ❌ No menu items found")
                
                time.sleep(3)  # Pause between requests
                
            except Exception as e:
                print(f"  ❌ Failed: {str(e)}")
        
        browser.close()
    
    # Save results
    output_file = "output/practical_menu_data.json"
    
    # Create comprehensive output
    total_items = sum(r['total_items'] for r in all_results)
    all_allergens = {}
    all_dietary = {}
    
    for result in all_results:
        for allergen, count in result['allergen_summary'].items():
            all_allergens[allergen] = all_allergens.get(allergen, 0) + count
        for dietary, count in result['dietary_summary'].items():
            all_dietary[dietary] = all_dietary.get(dietary, 0) + count
    
    final_output = {
        'extraction_summary': {
            'date': '2024-01-15',
            'total_restaurants': len(all_results),
            'total_menu_items': total_items,
            'overall_allergen_analysis': all_allergens,
            'overall_dietary_options': all_dietary
        },
        'restaurants': all_results
    }
    
    with open(output_file, 'w') as f:
        json.dump(final_output, f, indent=2)
    
    # Print summary
    print(f"\n=== PRACTICAL EXTRACTION RESULTS ===")
    print(f"Restaurants processed: {len(all_results)}")
    print(f"Total menu items extracted: {total_items}")
    print(f"Results saved to: {output_file}")
    
    if all_allergens:
        print(f"\n=== ALLERGEN DETECTION ===")
        for allergen, count in sorted(all_allergens.items(), key=lambda x: x[1], reverse=True):
            print(f"  {allergen.replace('_', ' ').title()}: {count} items")
    
    if all_dietary:
        print(f"\n=== DIETARY OPTIONS ===")
        for dietary, count in sorted(all_dietary.items(), key=lambda x: x[1], reverse=True):
            print(f"  {dietary.replace('_', ' ').title()}: {count} items")
    
    # Show sample items
    if all_results:
        print(f"\n=== SAMPLE EXTRACTED ITEMS ===")
        for result in all_results[:2]:
            print(f"\n{result['restaurant_name']} ({result['cuisine_type']})")
            for item in result['menu_items'][:3]:
                allergens = ', '.join(item['potential_allergens']) if item['potential_allergens'] else 'None detected'
                dietary = ', '.join(item['dietary_info']) if item['dietary_info'] else 'None'
                print(f"  • {item['name']} - {item['price']}")
                print(f"    Allergens: {allergens}")
                print(f"    Dietary: {dietary}")
    
    print(f"\n=== READY FOR HEALTH APP INTEGRATION ===")
    print("This practical data includes:")
    print("✅ Real menu items from actual restaurants")
    print("✅ Allergen detection and analysis")
    print("✅ Dietary restriction identification")
    print("✅ Price and ingredient information")
    print("✅ Structured JSON for app development")
    
    return final_output

if __name__ == "__main__":
    print("Starting practical menu scraper for health/allergy app...\n")
    
    results = scrape_practical_menus()
    
    print(f"\n=== SCRAPING COMPLETE ===")
    print("Data is now ready for your health-based allergy app!")
    print("\nNext steps for your app:")
    print("1. Import the JSON data into your app database")
    print("2. Create allergen filtering functionality")
    print("3. Build user preference profiles")
    print("4. Implement restaurant recommendations based on dietary needs")
    print("5. Add allergen warnings and safe menu suggestions")