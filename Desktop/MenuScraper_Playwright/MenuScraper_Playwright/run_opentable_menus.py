from playwright.sync_api import sync_playwright
import json
import os
import time
import re

os.makedirs("output", exist_ok=True)

def scrape_restaurant_menu(page, restaurant_url, restaurant_name):
    """Scrape menu information from a specific OpenTable restaurant page"""
    menu_data = {
        "restaurant_name": restaurant_name,
        "restaurant_url": restaurant_url,
        "menu_items": [],
        "menu_sections": [],
        "price_range": None,
        "cuisine_type": None,
        "error": None
    }
    
    try:
        print(f"  Visiting restaurant page...")
        page.goto(restaurant_url, timeout=30000)
        page.wait_for_load_state("networkidle", timeout=10000)
        time.sleep(2)
        
        # Extract basic restaurant info
        try:
            # Get cuisine type
            cuisine_selectors = [
                '[data-test="restaurant-cuisine"]',
                '.cuisine-type',
                '[class*="cuisine"]'
            ]
            
            for selector in cuisine_selectors:
                try:
                    cuisine_element = page.locator(selector).first
                    if cuisine_element.is_visible():
                        menu_data["cuisine_type"] = cuisine_element.inner_text().strip()
                        break
                except:
                    continue
            
            # Get price range
            price_selectors = [
                '[data-test="restaurant-price"]',
                '.price-range',
                '[class*="price"]',
                'span:has-text("$$$")',
                'span:has-text("$$")'
            ]
            
            for selector in price_selectors:
                try:
                    price_element = page.locator(selector).first
                    if price_element.is_visible():
                        price_text = price_element.inner_text().strip()
                        if '$' in price_text:
                            menu_data["price_range"] = price_text
                            break
                except:
                    continue
                    
        except Exception as e:
            print(f"  Error extracting basic info: {e}")
        
        # Look for menu section or menu link
        menu_selectors = [
            'a[href*="menu"]',
            'button:has-text("Menu")',
            'div:has-text("Menu")',
            '[data-test*="menu"]',
            '.menu-section',
            '#menu'
        ]
        
        menu_found = False
        for selector in menu_selectors:
            try:
                menu_elements = page.locator(selector).all()
                if menu_elements:
                    print(f"  Found menu elements with selector: {selector}")
                    # Click on menu if it's clickable
                    if 'button' in selector or 'a' in selector:
                        try:
                            menu_elements[0].click()
                            time.sleep(3)
                            menu_found = True
                        except:
                            pass
                    break
            except:
                continue
        
        # Extract menu items and prices
        menu_item_selectors = [
            '[class*="menu-item"]',
            '[class*="dish"]',
            '[data-test*="menu-item"]',
            '.menu-item',
            'div:has-text("$"):visible',
            '[class*="food-item"]'
        ]
        
        for selector in menu_item_selectors:
            try:
                items = page.locator(selector).all()
                print(f"  Trying selector {selector}, found {len(items)} items")
                
                for item in items[:15]:  # Limit to first 15 items
                    try:
                        text = item.inner_text().strip()
                        if text and len(text) > 5:
                            # Extract price using regex
                            price_match = re.search(r'\$[\d,]+\.?\d*', text)
                            price = price_match.group() if price_match else None
                            
                            # Clean up the text
                            clean_text = re.sub(r'\s+', ' ', text).strip()
                            
                            if len(clean_text) < 200:  # Reasonable menu item length
                                menu_data["menu_items"].append({
                                    "text": clean_text,
                                    "price": price
                                })
                    except Exception as item_error:
                        print(f"    Error processing item: {item_error}")
                        continue
                        
                if menu_data["menu_items"]:
                    print(f"  Successfully extracted {len(menu_data['menu_items'])} items")
                    break
            except Exception as selector_error:
                print(f"  Error with selector {selector}: {selector_error}")
                continue
        
        # Extract menu sections/categories
        section_selectors = [
            'h2, h3, h4',
            '[class*="section-title"]',
            '[class*="category"]',
            '[data-test*="section"]',
            '.menu-section-title'
        ]
        
        for selector in section_selectors:
            try:
                sections = page.locator(selector).all()
                for section in sections[:8]:  # Limit to first 8 sections
                    try:
                        text = section.inner_text().strip()
                        if text and len(text) < 100 and not '$' in text and len(text) > 2:
                            menu_data["menu_sections"].append(text)
                    except:
                        continue
                        
                if menu_data["menu_sections"]:
                    break
            except:
                continue
        
        print(f"  Found {len(menu_data['menu_items'])} menu items and {len(menu_data['menu_sections'])} sections")
        
    except Exception as e:
        menu_data["error"] = str(e)
        print(f"  Error scraping menu: {e}")
    
    return menu_data

def scrape_opentable_with_menus():
    results = []
    print("Starting OpenTable scraper with menu extraction...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=1000)
        page = browser.new_page()
        
        try:
            print("Navigating to OpenTable...")
            page.goto("https://www.opentable.com/chicago-restaurants", timeout=60000)
            
            # Wait for page to load
            page.wait_for_load_state("networkidle")
            time.sleep(3)
            
            print("Searching for restaurant links...")
            restaurant_links = page.locator('a[href*="/r/"]').all()
            
            print(f"Found {len(restaurant_links)} restaurant links")
            
            # Limit to first 5 restaurants for testing
            for i, link in enumerate(restaurant_links[:5]):
                try:
                    href = link.get_attribute('href')
                    text = link.inner_text().strip()
                    
                    if href and text:
                        # Convert relative URLs to absolute
                        if href.startswith('/'):
                            href = 'https://www.opentable.com' + href
                        
                        # Extract restaurant name (first line usually)
                        restaurant_name = text.split('\n')[0] if '\n' in text else text
                        restaurant_name = re.sub(r'^(Promoted\s*|Icon\s*)', '', restaurant_name).strip()
                        
                        print(f"\nProcessing restaurant {i + 1}: {restaurant_name}")
                        print(f"URL: {href}")
                        
                        # Scrape menu from this restaurant
                        menu_data = scrape_restaurant_menu(page, href, restaurant_name)
                        menu_data["index"] = i + 1
                        
                        results.append(menu_data)
                        
                        # Small delay between requests
                        time.sleep(3)
                        
                except Exception as e:
                    print(f"Error processing restaurant {i + 1}: {e}")
                    continue
            
        except Exception as e:
            print(f"Error during scraping: {e}")
        finally:
            browser.close()
    
    # Save results
    output_file = "output/opentable_menus_detailed.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nScraping completed! Processed {len(results)} restaurants.")
    print(f"Results saved to {output_file}")
    
    # Print summary
    total_menu_items = sum(len(r.get('menu_items', [])) for r in results)
    restaurants_with_menus = sum(1 for r in results if r.get('menu_items'))
    print(f"Total menu items found: {total_menu_items}")
    print(f"Restaurants with menu data: {restaurants_with_menus}/{len(results)}")
    
    return results

if __name__ == "__main__":
    scrape_opentable_with_menus()