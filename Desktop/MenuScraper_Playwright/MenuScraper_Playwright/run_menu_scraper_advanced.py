from playwright.sync_api import sync_playwright
import json
import os
import time
import re
from urllib.parse import urljoin, urlparse

os.makedirs("output", exist_ok=True)

def extract_menu_from_page(page, restaurant_url, restaurant_name):
    """Advanced menu extraction that tries multiple strategies"""
    menu_data = {
        "restaurant_name": restaurant_name,
        "restaurant_url": restaurant_url,
        "menu_items": [],
        "menu_sections": [],
        "price_range": None,
        "cuisine_type": None,
        "menu_url": None,
        "extraction_method": None,
        "error": None
    }
    
    try:
        print(f"  Visiting: {restaurant_url}")
        page.goto(restaurant_url, timeout=45000)
        page.wait_for_load_state("domcontentloaded")
        time.sleep(3)
        
        # Strategy 1: Look for dedicated menu links
        menu_link_selectors = [
            'a[href*="menu"]',
            'a:has-text("Menu")',
            'a:has-text("View Menu")',
            'button:has-text("Menu")',
            '[data-test*="menu"]'
        ]
        
        menu_page_found = False
        for selector in menu_link_selectors:
            try:
                menu_links = page.locator(selector).all()
                for link in menu_links:
                    if link.is_visible():
                        href = link.get_attribute('href')
                        if href and 'menu' in href.lower():
                            print(f"  Found menu link: {href}")
                            # Navigate to menu page
                            if href.startswith('/'):
                                base_url = f"{urlparse(restaurant_url).scheme}://{urlparse(restaurant_url).netloc}"
                                menu_url = urljoin(base_url, href)
                            else:
                                menu_url = href
                            
                            page.goto(menu_url, timeout=30000)
                            page.wait_for_load_state("domcontentloaded")
                            time.sleep(2)
                            menu_data["menu_url"] = menu_url
                            menu_data["extraction_method"] = "dedicated_menu_page"
                            menu_page_found = True
                            break
                if menu_page_found:
                    break
            except Exception as e:
                print(f"  Error with menu link selector {selector}: {e}")
                continue
        
        if not menu_page_found:
            menu_data["extraction_method"] = "main_page_extraction"
        
        # Strategy 2: Extract menu items using various selectors
        menu_extraction_strategies = [
            # Strategy A: Look for structured menu items
            {
                "name": "structured_menu_items",
                "selectors": [
                    '[class*="menu-item"]',
                    '[data-test*="menu-item"]',
                    '.menu-item',
                    '[class*="dish"]'
                ]
            },
            # Strategy B: Look for price-containing elements
            {
                "name": "price_based_extraction",
                "selectors": [
                    'div:has-text("$"):visible',
                    'span:has-text("$"):visible',
                    'p:has-text("$"):visible'
                ]
            },
            # Strategy C: Look for food-related content
            {
                "name": "food_content_extraction",
                "selectors": [
                    '[class*="food"]',
                    '[class*="item"]',
                    '[class*="product"]'
                ]
            }
        ]
        
        for strategy in menu_extraction_strategies:
            if menu_data["menu_items"]:  # Stop if we already found items
                break
                
            print(f"  Trying strategy: {strategy['name']}")
            
            for selector in strategy["selectors"]:
                try:
                    elements = page.locator(selector).all()
                    print(f"    Found {len(elements)} elements with selector: {selector}")
                    
                    for element in elements[:20]:  # Limit to prevent overwhelming
                        try:
                            if not element.is_visible():
                                continue
                                
                            text = element.inner_text().strip()
                            
                            # Filter for likely menu items
                            if (len(text) > 10 and len(text) < 300 and 
                                not text.lower().startswith(('copyright', 'privacy', 'terms', 'about')) and
                                '\n' not in text[:50]):  # Avoid multi-line headers
                                
                                # Extract price
                                price_match = re.search(r'\$[\d,]+(?:\.\d{2})?', text)
                                price = price_match.group() if price_match else None
                                
                                # Clean text
                                clean_text = re.sub(r'\s+', ' ', text).strip()
                                
                                # Check if this looks like a menu item
                                food_keywords = ['chicken', 'beef', 'fish', 'pasta', 'pizza', 'salad', 
                                               'soup', 'sandwich', 'burger', 'steak', 'salmon', 'shrimp',
                                               'appetizer', 'entree', 'dessert', 'drink', 'wine', 'beer']
                                
                                has_food_keyword = any(keyword in clean_text.lower() for keyword in food_keywords)
                                has_price = price is not None
                                reasonable_length = 15 <= len(clean_text) <= 200
                                
                                if (has_price or has_food_keyword) and reasonable_length:
                                    menu_data["menu_items"].append({
                                        "text": clean_text,
                                        "price": price,
                                        "extraction_method": strategy["name"]
                                    })
                                    
                        except Exception as e:
                            continue
                    
                    if menu_data["menu_items"]:
                        print(f"    Successfully extracted {len(menu_data['menu_items'])} items")
                        break
                        
                except Exception as e:
                    print(f"    Error with selector {selector}: {e}")
                    continue
        
        # Extract menu sections
        section_selectors = ['h1', 'h2', 'h3', 'h4', '[class*="section"]', '[class*="category"]']
        
        for selector in section_selectors:
            try:
                sections = page.locator(selector).all()
                for section in sections[:10]:
                    try:
                        if section.is_visible():
                            text = section.inner_text().strip()
                            if (5 <= len(text) <= 50 and 
                                not '$' in text and 
                                not text.lower().startswith(('copyright', 'privacy', 'terms'))):
                                menu_data["menu_sections"].append(text)
                    except:
                        continue
                if menu_data["menu_sections"]:
                    break
            except:
                continue
        
        # Extract basic restaurant info
        try:
            # Look for cuisine type
            cuisine_patterns = [
                r'(Italian|Chinese|Mexican|American|French|Japanese|Thai|Indian|Mediterranean|Greek)\s*(Restaurant|Cuisine|Food)?',
                r'(Contemporary|Modern|Traditional)\s*(American|Italian|Asian)'
            ]
            
            page_text = page.inner_text()
            for pattern in cuisine_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    menu_data["cuisine_type"] = match.group().strip()
                    break
        except:
            pass
        
        print(f"  Extracted {len(menu_data['menu_items'])} menu items, {len(menu_data['menu_sections'])} sections")
        
    except Exception as e:
        menu_data["error"] = str(e)
        print(f"  Error: {e}")
    
    return menu_data

def scrape_restaurants_with_menus(base_url, site_name, restaurant_selector, limit=3):
    """Generic function to scrape restaurants and their menus"""
    results = []
    print(f"Starting {site_name} scraper with advanced menu extraction...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=500)
        page = browser.new_page()
        
        # Set a longer timeout for navigation
        page.set_default_timeout(60000)
        
        try:
            print(f"Navigating to {base_url}...")
            page.goto(base_url, timeout=60000)
            page.wait_for_load_state("networkidle")
            time.sleep(5)
            
            print("Searching for restaurant links...")
            restaurant_links = page.locator(restaurant_selector).all()
            
            print(f"Found {len(restaurant_links)} restaurant links")
            
            processed = 0
            for i, link in enumerate(restaurant_links):
                if processed >= limit:
                    break
                    
                try:
                    href = link.get_attribute('href')
                    if not href:
                        continue
                        
                    # Convert relative URLs to absolute
                    if href.startswith('/'):
                        base_domain = f"{urlparse(base_url).scheme}://{urlparse(base_url).netloc}"
                        href = urljoin(base_domain, href)
                    
                    # Extract restaurant name
                    try:
                        restaurant_name = link.inner_text().strip().split('\n')[0]
                        restaurant_name = re.sub(r'^(Promoted\s*|Icon\s*)', '', restaurant_name).strip()
                    except:
                        restaurant_name = f"Restaurant {processed + 1}"
                    
                    if not restaurant_name:
                        restaurant_name = f"Restaurant {processed + 1}"
                    
                    print(f"\n--- Processing {processed + 1}/{limit}: {restaurant_name} ---")
                    
                    # Extract menu data
                    menu_data = extract_menu_from_page(page, href, restaurant_name)
                    menu_data["index"] = processed + 1
                    menu_data["source_site"] = site_name
                    
                    results.append(menu_data)
                    processed += 1
                    
                    # Delay between requests
                    time.sleep(3)
                    
                except Exception as e:
                    print(f"Error processing restaurant {i + 1}: {e}")
                    continue
            
        except Exception as e:
            print(f"Error during scraping: {e}")
        finally:
            browser.close()
    
    return results

def main():
    """Main function to run the advanced menu scraper"""
    
    # Test with OpenTable (usually more reliable)
    print("=== TESTING OPENTABLE ===")
    opentable_results = scrape_restaurants_with_menus(
        base_url="https://www.opentable.com/chicago-restaurants",
        site_name="OpenTable",
        restaurant_selector='a[href*="/r/"]',
        limit=3
    )
    
    # Save OpenTable results
    with open("output/advanced_opentable_menus.json", "w") as f:
        json.dump(opentable_results, f, indent=2)
    
    # Print summary
    total_items = sum(len(r.get('menu_items', [])) for r in opentable_results)
    successful_extractions = sum(1 for r in opentable_results if r.get('menu_items'))
    
    print(f"\n=== SUMMARY ===")
    print(f"Restaurants processed: {len(opentable_results)}")
    print(f"Successful menu extractions: {successful_extractions}")
    print(f"Total menu items found: {total_items}")
    print(f"Results saved to: output/advanced_opentable_menus.json")
    
    return opentable_results

if __name__ == "__main__":
    main()