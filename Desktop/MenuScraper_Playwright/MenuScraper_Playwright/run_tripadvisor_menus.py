from playwright.sync_api import sync_playwright
import json
import os
import time
import re

os.makedirs("output", exist_ok=True)

def scrape_restaurant_menu(page, restaurant_url):
    """Scrape menu information from a specific restaurant page"""
    menu_data = {
        "restaurant_url": restaurant_url,
        "menu_items": [],
        "menu_sections": [],
        "error": None
    }
    
    try:
        print(f"  Visiting restaurant page...")
        page.goto(restaurant_url, timeout=30000)
        page.wait_for_load_state("networkidle", timeout=10000)
        time.sleep(2)
        
        # Try to find menu section or menu button
        menu_selectors = [
            'a[href*="menu"]',
            'button:has-text("Menu")',
            'div:has-text("Menu")',
            '[data-test*="menu"]',
            '.menu',
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
                        menu_elements[0].click()
                        time.sleep(2)
                    menu_found = True
                    break
            except:
                continue
        
        # Extract menu items and prices
        menu_item_selectors = [
            '[class*="menu"] [class*="item"]',
            '[class*="dish"]',
            '[class*="food"]',
            'div:has-text("$"):visible',
            'span:has-text("$"):visible'
        ]
        
        for selector in menu_item_selectors:
            try:
                items = page.locator(selector).all()
                for item in items[:10]:  # Limit to first 10 items
                    try:
                        text = item.inner_text().strip()
                        if text and len(text) > 5 and '$' in text:
                            # Extract price using regex
                            price_match = re.search(r'\$[\d,]+\.?\d*', text)
                            price = price_match.group() if price_match else None
                            
                            menu_data["menu_items"].append({
                                "text": text,
                                "price": price
                            })
                    except:
                        continue
                        
                if menu_data["menu_items"]:
                    break
            except:
                continue
        
        # Extract menu sections
        section_selectors = [
            'h2, h3, h4',
            '[class*="section"]',
            '[class*="category"]'
        ]
        
        for selector in section_selectors:
            try:
                sections = page.locator(selector).all()
                for section in sections[:5]:  # Limit to first 5 sections
                    try:
                        text = section.inner_text().strip()
                        if text and len(text) < 50 and not '$' in text:
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

def scrape_tripadvisor_with_menus():
    results = []
    print("Starting TripAdvisor scraper with menu extraction...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=1000)
        page = browser.new_page()
        
        try:
            print("Navigating to TripAdvisor...")
            page.goto("https://www.tripadvisor.com/Restaurants-g35805-Chicago_Illinois.html", timeout=60000)
            
            # Wait for page to load
            page.wait_for_load_state("networkidle")
            time.sleep(3)
            
            print("Searching for restaurant links...")
            restaurant_links = page.locator('a[href*="/Restaurant_Review"]').all()
            
            print(f"Found {len(restaurant_links)} restaurant links")
            
            # Limit to first 5 restaurants for testing
            for i, link in enumerate(restaurant_links[:5]):
                try:
                    href = link.get_attribute('href')
                    if href:
                        # Convert relative URLs to absolute
                        if href.startswith('/'):
                            href = 'https://www.tripadvisor.com' + href
                        
                        print(f"\nProcessing restaurant {i + 1}: {href}")
                        
                        # Scrape menu from this restaurant
                        menu_data = scrape_restaurant_menu(page, href)
                        menu_data["index"] = i + 1
                        
                        results.append(menu_data)
                        
                        # Small delay between requests
                        time.sleep(2)
                        
                except Exception as e:
                    print(f"Error processing restaurant {i + 1}: {e}")
                    continue
            
        except Exception as e:
            print(f"Error during scraping: {e}")
        finally:
            browser.close()
    
    # Save results
    output_file = "output/tripadvisor_menus_detailed.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nScraping completed! Processed {len(results)} restaurants.")
    print(f"Results saved to {output_file}")
    
    # Print summary
    total_menu_items = sum(len(r.get('menu_items', [])) for r in results)
    print(f"Total menu items found: {total_menu_items}")
    
    return results

if __name__ == "__main__":
    scrape_tripadvisor_with_menus()