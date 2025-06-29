from playwright.sync_api import sync_playwright
import json
import os
import time
import re
from urllib.parse import urljoin, urlparse

os.makedirs("output", exist_ok=True)

def extract_allergen_info(text):
    """Extract potential allergen information from menu item text"""
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

def extract_ingredients(text):
    """Extract ingredients from menu item description"""
    # Common ingredient patterns
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
    
    # Clean and filter ingredients
    cleaned_ingredients = []
    for ingredient in ingredients:
        ingredient = ingredient.strip()
        if len(ingredient) > 2 and len(ingredient) < 50:
            cleaned_ingredients.append(ingredient)
    
    return cleaned_ingredients

def scrape_restaurant_menu_detailed(page, restaurant_url, max_retries=3):
    """Scrape detailed menu information from a restaurant page"""
    
    for attempt in range(max_retries):
        try:
            print(f"  Attempt {attempt + 1}: Visiting {restaurant_url}")
            
            # Navigate to restaurant page
            page.goto(restaurant_url, timeout=45000)
            page.wait_for_load_state('networkidle', timeout=20000)
            
            # Get restaurant name
            restaurant_name = "Unknown Restaurant"
            try:
                # Try multiple selectors for restaurant name
                name_selectors = ['h1', '[data-test="restaurant-name"]', '.restaurant-name', '.listing-title']
                for selector in name_selectors:
                    try:
                        name_element = page.locator(selector).first
                        if name_element.is_visible():
                            restaurant_name = name_element.inner_text().strip()
                            break
                    except:
                        continue
                        
                if restaurant_name == "Unknown Restaurant":
                    restaurant_name = page.title().split(' - ')[0].strip()
            except:
                pass
            
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
                            print(f"    Found menu link: {menu_url}")
                            page.goto(menu_url, timeout=30000)
                            page.wait_for_load_state('networkidle', timeout=15000)
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
                        print(f"    Found {len(items)} items with selector: {selector}")
                        for item in items[:20]:  # Limit to 20 items
                            try:
                                item_text = item.inner_text().strip()
                                if len(item_text) > 10:  # Filter out short/empty items
                                    
                                    # Extract price
                                    price_match = re.search(r'\$([0-9]+(?:\.[0-9]{2})?)', item_text)
                                    price = f"${price_match.group(1)}" if price_match else None
                                    
                                    # Clean description (remove price)
                                    description = re.sub(r'\$[0-9]+(?:\.[0-9]{2})?', '', item_text).strip()
                                    
                                    # Extract allergens and ingredients
                                    allergens = extract_allergen_info(description)
                                    ingredients = extract_ingredients(description)
                                    
                                    menu_items.append({
                                        'name': description.split('.')[0].strip(),  # First sentence as name
                                        'description': description,
                                        'price': price,
                                        'potential_allergens': allergens,
                                        'ingredients': ingredients,
                                        'section': 'Menu'
                                    })
                            except Exception as e:
                                continue
                        break
                except:
                    continue
            
            # Strategy 2: If no structured items found, look for price-based extraction
            if len(menu_items) == 0:
                print("    Trying price-based extraction...")
                page_text = page.inner_text('body')
                
                # Look for food items with prices
                price_patterns = [
                    r'([A-Z][^$\n]{15,100})\s*\$([0-9]+(?:\.[0-9]{2})?)',
                    r'([^$\n]{20,80}(?:chicken|beef|fish|pasta|salad|soup|pizza|burger|sandwich|steak|seafood|vegetarian|dessert|appetizer)[^$\n]{0,30})\s*\$([0-9]+(?:\.[0-9]{2})?)',
                ]
                
                for pattern in price_patterns:
                    matches = re.findall(pattern, page_text, re.MULTILINE | re.IGNORECASE)
                    for description, price in matches[:15]:  # Limit to 15 items
                        description = description.strip()
                        
                        # Filter out non-food items
                        if (len(description) > 15 and 
                            not any(word in description.lower() for word in ['copyright', 'privacy', 'terms', 'contact', 'about', 'login', 'sign', 'reservation', 'table']) and
                            any(word in description.lower() for word in ['chicken', 'beef', 'fish', 'pasta', 'salad', 'soup', 'pizza', 'burger', 'sandwich', 'steak', 'seafood', 'vegetarian', 'dessert', 'appetizer', 'served', 'grilled', 'fried', 'baked'])):
                            
                            allergens = extract_allergen_info(description)
                            ingredients = extract_ingredients(description)
                            
                            menu_items.append({
                                'name': description.split('.')[0].strip()[:50],  # First part as name
                                'description': description,
                                'price': f'${price}',
                                'potential_allergens': allergens,
                                'ingredients': ingredients,
                                'section': 'Menu'
                            })
                    
                    if len(menu_items) > 0:
                        break
            
            # Extract cuisine type
            cuisine_type = "Unknown"
            page_content = page.inner_text('body').lower()
            cuisine_keywords = {
                'Italian': ['italian', 'pasta', 'pizza', 'risotto', 'gelato', 'marinara'],
                'Mexican': ['mexican', 'tacos', 'burrito', 'salsa', 'guacamole', 'quesadilla'],
                'Asian': ['asian', 'sushi', 'ramen', 'noodles', 'rice', 'stir fry'],
                'American': ['american', 'burger', 'steak', 'bbq', 'fries', 'wings'],
                'French': ['french', 'croissant', 'baguette', 'wine', 'cheese', 'bistro'],
                'Indian': ['indian', 'curry', 'naan', 'tandoor', 'masala', 'biryani'],
                'Mediterranean': ['mediterranean', 'hummus', 'falafel', 'olive', 'pita', 'tzatziki']
            }
            
            for cuisine, keywords in cuisine_keywords.items():
                if sum(1 for keyword in keywords if keyword in page_content) >= 2:
                    cuisine_type = cuisine
                    break
            
            print(f"    ✅ Extracted {len(menu_items)} menu items")
            
            return {
                'restaurant_name': restaurant_name,
                'restaurant_url': restaurant_url,
                'menu_url': menu_url,
                'cuisine_type': cuisine_type,
                'menu_items': menu_items,
                'total_items': len(menu_items),
                'extraction_method': 'detailed_health_focused',
                'allergen_analysis': True
            }
            
        except Exception as e:
            print(f"    ❌ Attempt {attempt + 1} failed: {str(e)}")
            if attempt == max_retries - 1:
                return {
                    'restaurant_name': 'Failed',
                    'restaurant_url': restaurant_url,
                    'error': str(e),
                    'menu_items': [],
                    'total_items': 0
                }
            time.sleep(3)  # Wait before retry

def scrape_health_focused_menus(base_url="https://www.opentable.com/new-york-restaurant-listings", max_restaurants=10):
    """Scrape menus with focus on health and allergen information"""
    
    print("=== HEALTH-FOCUSED MENU SCRAPER ===")
    print("Extracting detailed menu information for allergy/health analysis")
    print(f"Target: {max_restaurants} restaurants\n")
    
    results = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=1000)
        page = browser.new_page()
        
        try:
            # Navigate to restaurant listings
            print(f"Loading restaurant listings from: {base_url}")
            page.goto(base_url, timeout=45000)
            page.wait_for_load_state('networkidle', timeout=20000)
            
            # Find restaurant links
            restaurant_links = []
            link_selectors = [
                'a[href*="/r/"]',
                'a[data-test*="restaurant"]',
                '.restaurant-link'
            ]
            
            for selector in link_selectors:
                try:
                    links = page.locator(selector).all()
                    if len(links) > 0:
                        print(f"Found {len(links)} restaurant links")
                        for link in links[:max_restaurants]:
                            href = link.get_attribute('href')
                            if href:
                                full_url = urljoin(base_url, href)
                                restaurant_links.append(full_url)
                        break
                except:
                    continue
            
            print(f"Processing {len(restaurant_links)} restaurants...\n")
            
            # Process each restaurant
            for i, restaurant_url in enumerate(restaurant_links, 1):
                print(f"Restaurant {i}/{len(restaurant_links)}")
                
                result = scrape_restaurant_menu_detailed(page, restaurant_url)
                result['index'] = i
                results.append(result)
                
                # Brief pause between requests
                time.sleep(2)
                
                # Stop if we have enough successful results
                successful_results = [r for r in results if r.get('menu_items') and len(r['menu_items']) > 0]
                if len(successful_results) >= 5:  # Stop after 5 successful extractions
                    print(f"\n✅ Collected sufficient data from {len(successful_results)} restaurants")
                    break
        
        except Exception as e:
            print(f"Error during scraping: {str(e)}")
        
        finally:
            browser.close()
    
    # Save results
    output_file = "output/health_focused_menus.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    # Generate summary
    successful = [r for r in results if 'error' not in r and r.get('menu_items')]
    total_items = sum(len(r.get('menu_items', [])) for r in successful)
    
    # Allergen analysis
    all_allergens = set()
    allergen_counts = {}
    
    for result in successful:
        for item in result.get('menu_items', []):
            for allergen in item.get('potential_allergens', []):
                all_allergens.add(allergen)
                allergen_counts[allergen] = allergen_counts.get(allergen, 0) + 1
    
    print(f"\n=== HEALTH-FOCUSED RESULTS ===")
    print(f"Restaurants processed: {len(results)}")
    print(f"Successful extractions: {len(successful)}")
    print(f"Total menu items: {total_items}")
    print(f"Unique allergens detected: {len(all_allergens)}")
    print(f"Results saved to: {output_file}")
    
    if allergen_counts:
        print(f"\n=== ALLERGEN ANALYSIS ===")
        for allergen, count in sorted(allergen_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {allergen}: {count} items")
    
    # Show sample items
    if successful:
        print(f"\n=== SAMPLE MENU ITEMS ===")
        for result in successful[:2]:
            print(f"\n{result['restaurant_name']} ({result['cuisine_type']})")
            for item in result['menu_items'][:3]:
                allergens_str = ', '.join(item['potential_allergens']) if item['potential_allergens'] else 'None detected'
                print(f"  • {item['name']} - {item.get('price', 'N/A')}")
                print(f"    Allergens: {allergens_str}")
    
    return results

if __name__ == "__main__":
    print("Starting health-focused menu scraper for allergy analysis...\n")
    
    results = scrape_health_focused_menus(max_restaurants=15)
    
    print(f"\n=== SCRAPING COMPLETE ===")
    print("This scraper provides:")
    print("✅ Detailed menu items with descriptions")
    print("✅ Potential allergen detection")
    print("✅ Ingredient extraction")
    print("✅ Price information")
    print("✅ Cuisine type classification")
    print("\nPerfect for building health-focused apps with allergy considerations!")