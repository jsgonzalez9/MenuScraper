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

def scrape_chicago_restaurants_opentable(page, max_pages=10):
    """Scrape Chicago restaurants from OpenTable with pagination"""
    
    print("=== SCRAPING CHICAGO RESTAURANTS FROM OPENTABLE ===")
    
    restaurants = []
    base_url = "https://www.opentable.com/chicago-restaurant-listings"
    
    for page_num in range(1, max_pages + 1):
        try:
            # Navigate to Chicago restaurant listings with pagination
            if page_num == 1:
                url = base_url
            else:
                url = f"{base_url}?page={page_num}"
            
            print(f"\nScraping page {page_num}: {url}")
            page.goto(url, timeout=45000)
            page.wait_for_load_state('networkidle', timeout=20000)
            
            # Find restaurant links on this page
            restaurant_selectors = [
                'a[href*="/r/"]',
                '[data-test*="restaurant-link"]',
                '.restaurant-link'
            ]
            
            page_restaurants = []
            for selector in restaurant_selectors:
                try:
                    links = page.locator(selector).all()
                    if len(links) > 0:
                        print(f"  Found {len(links)} restaurant links with selector: {selector}")
                        
                        for link in links:
                            try:
                                href = link.get_attribute('href')
                                if href and '/r/' in href:
                                    full_url = urljoin(base_url, href)
                                    
                                    # Try to get restaurant name from link text or nearby elements
                                    restaurant_name = "Unknown"
                                    try:
                                        restaurant_name = link.inner_text().strip()
                                        if not restaurant_name or len(restaurant_name) > 100:
                                            # Try parent element
                                            restaurant_name = link.locator('..').inner_text().strip().split('\n')[0]
                                    except:
                                        pass
                                    
                                    page_restaurants.append({
                                        'name': restaurant_name,
                                        'url': full_url,
                                        'source': 'OpenTable',
                                        'page': page_num
                                    })
                            except Exception as e:
                                continue
                        break
                except:
                    continue
            
            if len(page_restaurants) == 0:
                print(f"  No restaurants found on page {page_num}, stopping pagination")
                break
            
            restaurants.extend(page_restaurants)
            print(f"  Added {len(page_restaurants)} restaurants from page {page_num}")
            
            # Check if there's a next page
            try:
                next_button = page.locator('a:has-text("Next")', 'button:has-text("Next")', '[aria-label*="next"]').first
                if not next_button.is_visible():
                    print(f"  No next page button found, stopping at page {page_num}")
                    break
            except:
                pass
            
            # Brief pause between pages
            time.sleep(2)
            
        except Exception as e:
            print(f"  Error on page {page_num}: {str(e)}")
            break
    
    return restaurants

def scrape_chicago_restaurants_tripadvisor(page, max_pages=10):
    """Scrape Chicago restaurants from TripAdvisor with pagination"""
    
    print("\n=== SCRAPING CHICAGO RESTAURANTS FROM TRIPADVISOR ===")
    
    restaurants = []
    base_url = "https://www.tripadvisor.com/Restaurants-g35805-Chicago_Illinois.html"
    
    for page_num in range(max_pages):
        try:
            # TripAdvisor uses offset-based pagination
            if page_num == 0:
                url = base_url
            else:
                offset = page_num * 30  # TripAdvisor typically shows 30 per page
                url = f"https://www.tripadvisor.com/Restaurants-g35805-oa{offset}-Chicago_Illinois.html"
            
            print(f"\nScraping page {page_num + 1}: {url}")
            page.goto(url, timeout=45000)
            page.wait_for_load_state('networkidle', timeout=20000)
            
            # Find restaurant links
            restaurant_selectors = [
                'a[href*="Restaurant_Review"]',
                '[data-test*="restaurant"]',
                '.restaurant-link'
            ]
            
            page_restaurants = []
            for selector in restaurant_selectors:
                try:
                    links = page.locator(selector).all()
                    if len(links) > 0:
                        print(f"  Found {len(links)} restaurant links with selector: {selector}")
                        
                        for link in links:
                            try:
                                href = link.get_attribute('href')
                                if href and 'Restaurant_Review' in href:
                                    full_url = urljoin(base_url, href)
                                    
                                    # Get restaurant name
                                    restaurant_name = "Unknown"
                                    try:
                                        restaurant_name = link.inner_text().strip()
                                        if not restaurant_name:
                                            # Try aria-label or title
                                            restaurant_name = link.get_attribute('aria-label') or link.get_attribute('title') or "Unknown"
                                    except:
                                        pass
                                    
                                    page_restaurants.append({
                                        'name': restaurant_name,
                                        'url': full_url,
                                        'source': 'TripAdvisor',
                                        'page': page_num + 1
                                    })
                            except Exception as e:
                                continue
                        break
                except:
                    continue
            
            if len(page_restaurants) == 0:
                print(f"  No restaurants found on page {page_num + 1}, stopping pagination")
                break
            
            restaurants.extend(page_restaurants)
            print(f"  Added {len(page_restaurants)} restaurants from page {page_num + 1}")
            
            # Brief pause between pages
            time.sleep(2)
            
        except Exception as e:
            print(f"  Error on page {page_num + 1}: {str(e)}")
            break
    
    return restaurants

def scrape_restaurant_menu_chicago(page, restaurant_data):
    """Scrape menu from a Chicago restaurant"""
    
    try:
        print(f"    Scraping menu for: {restaurant_data['name']}")
        page.goto(restaurant_data['url'], timeout=30000)
        page.wait_for_load_state('networkidle', timeout=15000)
        
        # Look for menu links first
        menu_selectors = [
            'a[href*="menu"]',
            'a:has-text("Menu")',
            'a:has-text("View Menu")',
            'button:has-text("Menu")',
            '[data-test*="menu"]'
        ]
        
        menu_found = False
        for selector in menu_selectors:
            try:
                menu_link = page.locator(selector).first
                if menu_link.is_visible():
                    menu_url = menu_link.get_attribute('href')
                    if menu_url:
                        menu_url = urljoin(restaurant_data['url'], menu_url)
                        page.goto(menu_url, timeout=30000)
                        page.wait_for_load_state('networkidle', timeout=10000)
                        menu_found = True
                        break
            except:
                continue
        
        # Extract menu items
        menu_items = []
        page_text = page.inner_text('body')
        
        # Look for items with prices
        price_patterns = [
            r'([A-Z][^$\n]{15,100})\s*\$([0-9]+(?:\.[0-9]{2})?)',
            r'([^$\n]{20,80}(?:chicken|beef|fish|pasta|salad|soup|pizza|burger|sandwich|steak|seafood|vegetarian|dessert|appetizer)[^$\n]{0,40})\s*\$([0-9]+(?:\.[0-9]{2})?)',
        ]
        
        for pattern in price_patterns:
            matches = re.findall(pattern, page_text, re.MULTILINE | re.IGNORECASE)
            for description, price in matches[:10]:  # Limit to 10 items per restaurant
                description = description.strip()
                
                # Filter food items
                if (len(description) > 10 and 
                    not any(word in description.lower() for word in ['copyright', 'privacy', 'terms', 'contact', 'about', 'reservation']) and
                    any(word in description.lower() for word in ['chicken', 'beef', 'fish', 'pasta', 'salad', 'soup', 'pizza', 'burger', 'sandwich', 'steak', 'served', 'grilled', 'fried'])):
                    
                    allergens = extract_allergen_info(description)
                    
                    menu_items.append({
                        'name': description.split('.')[0].strip()[:50],
                        'description': description,
                        'price': f'${price}',
                        'potential_allergens': allergens
                    })
            
            if len(menu_items) > 0:
                break
        
        return menu_items
        
    except Exception as e:
        print(f"      Error extracting menu: {str(e)}")
        return []

def scrape_all_chicago_restaurants(max_restaurants_per_source=100, include_menus=True):
    """Comprehensive Chicago restaurant scraper"""
    
    print("=== COMPREHENSIVE CHICAGO RESTAURANT SCRAPER ===")
    print(f"Target: Up to {max_restaurants_per_source} restaurants per source")
    print(f"Include menus: {include_menus}\n")
    
    all_restaurants = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=1000)
        page = browser.new_page()
        
        try:
            # Scrape from OpenTable
            opentable_restaurants = scrape_chicago_restaurants_opentable(page, max_pages=10)
            all_restaurants.extend(opentable_restaurants[:max_restaurants_per_source])
            
            # Scrape from TripAdvisor
            tripadvisor_restaurants = scrape_chicago_restaurants_tripadvisor(page, max_pages=10)
            all_restaurants.extend(tripadvisor_restaurants[:max_restaurants_per_source])
            
            # Remove duplicates based on name similarity
            unique_restaurants = []
            seen_names = set()
            
            for restaurant in all_restaurants:
                name_key = restaurant['name'].lower().replace(' ', '').replace('-', '')
                if name_key not in seen_names and len(name_key) > 3:
                    seen_names.add(name_key)
                    unique_restaurants.append(restaurant)
            
            print(f"\n=== DEDUPLICATION COMPLETE ===")
            print(f"Total restaurants found: {len(all_restaurants)}")
            print(f"Unique restaurants: {len(unique_restaurants)}")
            
            # Extract menus if requested
            if include_menus:
                print(f"\n=== EXTRACTING MENUS ===")
                
                for i, restaurant in enumerate(unique_restaurants[:20], 1):  # Limit to first 20 for demo
                    print(f"\nRestaurant {i}/20: {restaurant['name']}")
                    
                    menu_items = scrape_restaurant_menu_chicago(page, restaurant)
                    restaurant['menu_items'] = menu_items
                    restaurant['menu_item_count'] = len(menu_items)
                    
                    # Calculate allergen summary
                    allergen_counts = {}
                    for item in menu_items:
                        for allergen in item.get('potential_allergens', []):
                            allergen_counts[allergen] = allergen_counts.get(allergen, 0) + 1
                    
                    restaurant['allergen_summary'] = allergen_counts
                    
                    print(f"    ✅ Found {len(menu_items)} menu items")
                    
                    # Brief pause
                    time.sleep(2)
            
        except Exception as e:
            print(f"Error during scraping: {str(e)}")
        
        finally:
            browser.close()
    
    # Save results
    output_file = "output/chicago_restaurants_complete.json"
    
    # Create summary statistics
    total_menu_items = sum(r.get('menu_item_count', 0) for r in unique_restaurants)
    sources = list(set(r['source'] for r in unique_restaurants))
    
    # Overall allergen analysis
    all_allergens = {}
    for restaurant in unique_restaurants:
        for allergen, count in restaurant.get('allergen_summary', {}).items():
            all_allergens[allergen] = all_allergens.get(allergen, 0) + count
    
    final_data = {
        'scraping_summary': {
            'date': '2024-01-15',
            'city': 'Chicago, Illinois',
            'total_restaurants': len(unique_restaurants),
            'total_menu_items': total_menu_items,
            'sources': sources,
            'include_menus': include_menus,
            'overall_allergen_analysis': all_allergens
        },
        'restaurants': unique_restaurants
    }
    
    with open(output_file, 'w') as f:
        json.dump(final_data, f, indent=2)
    
    # Print final summary
    print(f"\n=== CHICAGO RESTAURANT SCRAPING COMPLETE ===")
    print(f"Total unique restaurants: {len(unique_restaurants)}")
    print(f"Sources: {', '.join(sources)}")
    print(f"Total menu items: {total_menu_items}")
    print(f"Results saved to: {output_file}")
    
    if all_allergens:
        print(f"\n=== CHICAGO ALLERGEN ANALYSIS ===")
        for allergen, count in sorted(all_allergens.items(), key=lambda x: x[1], reverse=True):
            print(f"  {allergen.replace('_', ' ').title()}: {count} items")
    
    # Show sample restaurants
    print(f"\n=== SAMPLE CHICAGO RESTAURANTS ===")
    for restaurant in unique_restaurants[:5]:
        menu_count = restaurant.get('menu_item_count', 0)
        print(f"  • {restaurant['name']} ({restaurant['source']}) - {menu_count} menu items")
    
    print(f"\n=== SCALING TO ALL CHICAGO RESTAURANTS ===")
    print("To get ALL Chicago restaurants:")
    print("1. Increase max_pages in both scrapers (currently limited to 10 pages each)")
    print("2. Add more sources (Yelp, Google Places, Zomato, etc.)")
    print("3. Use restaurant APIs for comprehensive coverage")
    print("4. Implement geographic boundary scraping")
    print("5. Add neighborhood-specific searches")
    
    return final_data

if __name__ == "__main__":
    print("Starting comprehensive Chicago restaurant scraper...\n")
    
    # Scrape Chicago restaurants with menus
    results = scrape_all_chicago_restaurants(
        max_restaurants_per_source=50,  # Limit for demo
        include_menus=True
    )
    
    print(f"\n=== CHICAGO SCRAPING COMPLETE ===")
    print("This demonstrates how to collect all Chicago restaurants!")
    print("\nFor complete coverage, you would:")
    print("• Remove the restaurant limits")
    print("• Add more data sources")
    print("• Implement comprehensive pagination")
    print("• Use restaurant discovery APIs")
    print("• Perfect for your health-based allergy app!")