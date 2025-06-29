from playwright.sync_api import sync_playwright
import json
import os
import time

os.makedirs("output", exist_ok=True)

def scrape_tripadvisor():
    results = []
    print("Starting TripAdvisor scraper...")
    
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
            # Look for restaurant links more effectively
            restaurant_links = page.locator('a[href*="/Restaurant_Review"]').all()
            
            print(f"Found {len(restaurant_links)} restaurant links")
            
            for i, link in enumerate(restaurant_links[:20]):  # Limit to first 20 for testing
                try:
                    href = link.get_attribute('href')
                    if href:
                        # Convert relative URLs to absolute
                        if href.startswith('/'):
                            href = 'https://www.tripadvisor.com' + href
                        
                        results.append({
                            "restaurant_url": href,
                            "index": i + 1
                        })
                        print(f"Added restaurant {i + 1}: {href}")
                except Exception as e:
                    print(f"Error processing link {i + 1}: {e}")
                    continue
            
        except Exception as e:
            print(f"Error during scraping: {e}")
        finally:
            browser.close()
    
    # Save results
    output_file = "output/tripadvisor_menus.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"Scraping completed! Found {len(results)} restaurants.")
    print(f"Results saved to {output_file}")
    return results

if __name__ == "__main__":
    scrape_tripadvisor()