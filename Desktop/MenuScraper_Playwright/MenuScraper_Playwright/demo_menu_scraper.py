from playwright.sync_api import sync_playwright
import json
import os
import time
import re

os.makedirs("output", exist_ok=True)

def demo_menu_extraction():
    """Demo script showing menu extraction capabilities"""
    
    print("=== MENU SCRAPING DEMO ===")
    print("This demo shows how to extract menu information from restaurant websites.")
    print("\nCapabilities:")
    print("✅ Extract menu items with prices")
    print("✅ Identify menu sections/categories")
    print("✅ Get restaurant details (cuisine, price range)")
    print("✅ Handle multiple website structures")
    print("✅ Save structured JSON data")
    
    # Create sample data to demonstrate the structure
    sample_results = [
        {
            "restaurant_name": "Alinea",
            "restaurant_url": "https://example.com/alinea",
            "cuisine_type": "Contemporary American",
            "price_range": "$$$$",
            "menu_sections": [
                "Tasting Menu",
                "Wine Pairings",
                "Desserts"
            ],
            "menu_items": [
                {
                    "text": "Multi-course tasting menu featuring seasonal ingredients",
                    "price": "$285",
                    "section": "Tasting Menu"
                },
                {
                    "text": "Wine pairing with sommelier selection",
                    "price": "$150",
                    "section": "Wine Pairings"
                },
                {
                    "text": "Chocolate, hazelnut, and coffee dessert experience",
                    "price": "$45",
                    "section": "Desserts"
                }
            ],
            "extraction_method": "dedicated_menu_page",
            "menu_url": "https://example.com/alinea/menu",
            "index": 1
        },
        {
            "restaurant_name": "Girl & the Goat",
            "restaurant_url": "https://example.com/girl-and-goat",
            "cuisine_type": "Contemporary American",
            "price_range": "$$$",
            "menu_sections": [
                "Small Plates",
                "Large Plates",
                "Sides",
                "Desserts"
            ],
            "menu_items": [
                {
                    "text": "Wood-fired pig face with tamarind, cilantro, mint",
                    "price": "$18",
                    "section": "Small Plates"
                },
                {
                    "text": "Goat empanadas with olive tapenade",
                    "price": "$16",
                    "section": "Small Plates"
                },
                {
                    "text": "Seared scallops with cauliflower, raisins, pine nuts",
                    "price": "$32",
                    "section": "Large Plates"
                },
                {
                    "text": "Roasted bone marrow with herbs and sea salt",
                    "price": "$14",
                    "section": "Sides"
                },
                {
                    "text": "Chocolate mousse with salted caramel",
                    "price": "$12",
                    "section": "Desserts"
                }
            ],
            "extraction_method": "main_page_extraction",
            "menu_url": None,
            "index": 2
        },
        {
            "restaurant_name": "Au Cheval",
            "restaurant_url": "https://example.com/au-cheval",
            "cuisine_type": "American Diner",
            "price_range": "$$",
            "menu_sections": [
                "Burgers",
                "Entrees",
                "Sides",
                "Breakfast"
            ],
            "menu_items": [
                {
                    "text": "Cheeseburger with American cheese, pickles, onion",
                    "price": "$18",
                    "section": "Burgers"
                },
                {
                    "text": "Bone-in ribeye steak with garlic butter",
                    "price": "$65",
                    "section": "Entrees"
                },
                {
                    "text": "Duck heart with onions and peppers",
                    "price": "$14",
                    "section": "Entrees"
                },
                {
                    "text": "Hash browns with herbs",
                    "price": "$8",
                    "section": "Sides"
                },
                {
                    "text": "Scrambled eggs with chives",
                    "price": "$12",
                    "section": "Breakfast"
                }
            ],
            "extraction_method": "structured_menu_items",
            "menu_url": "https://example.com/au-cheval/menu",
            "index": 3
        }
    ]
    
    # Save demo results
    output_file = "output/demo_menu_extraction.json"
    with open(output_file, "w") as f:
        json.dump(sample_results, f, indent=2)
    
    print(f"\n=== DEMO RESULTS ===")
    print(f"Created sample data showing menu extraction capabilities")
    print(f"File saved: {output_file}")
    
    # Print summary statistics
    total_restaurants = len(sample_results)
    total_menu_items = sum(len(r['menu_items']) for r in sample_results)
    total_sections = sum(len(r['menu_sections']) for r in sample_results)
    
    print(f"\n=== STATISTICS ===")
    print(f"Restaurants: {total_restaurants}")
    print(f"Total menu items: {total_menu_items}")
    print(f"Total menu sections: {total_sections}")
    
    # Show sample menu items
    print(f"\n=== SAMPLE MENU ITEMS ===")
    for restaurant in sample_results:
        print(f"\n{restaurant['restaurant_name']} ({restaurant['cuisine_type']})")
        for item in restaurant['menu_items'][:2]:  # Show first 2 items
            print(f"  • {item['text']} - {item['price']}")
    
    print(f"\n=== HOW IT WORKS ===")
    print("The menu scraper uses multiple extraction strategies:")
    print("1. 🔍 Searches for dedicated menu pages/links")
    print("2. 📋 Identifies structured menu items with CSS selectors")
    print("3. 💰 Extracts prices using regex patterns")
    print("4. 🏷️  Categorizes items into menu sections")
    print("5. 📊 Saves structured data in JSON format")
    
    print(f"\n=== REAL IMPLEMENTATION ===")
    print("To scrape real restaurant menus:")
    print("• The scripts visit each restaurant's individual page")
    print("• They look for menu links and navigate to menu pages")
    print("• Multiple CSS selectors are tried to find menu content")
    print("• Text is cleaned and prices are extracted")
    print("• Results are saved with detailed metadata")
    
    return sample_results

def show_extraction_methods():
    """Demonstrate different extraction methods"""
    
    print(f"\n=== EXTRACTION METHODS EXPLAINED ===")
    
    methods = {
        "dedicated_menu_page": {
            "description": "Finds and navigates to a separate menu page",
            "selectors": ['a[href*="menu"]', 'a:has-text("Menu")', 'button:has-text("Menu")'],
            "success_rate": "High - Most reliable when available"
        },
        "structured_menu_items": {
            "description": "Extracts from structured HTML menu elements",
            "selectors": ['[class*="menu-item"]', '.menu-item', '[data-test*="menu-item"]'],
            "success_rate": "High - Works well with modern websites"
        },
        "price_based_extraction": {
            "description": "Finds elements containing price information",
            "selectors": ['div:has-text("$")', 'span:has-text("$")', 'p:has-text("$")'],
            "success_rate": "Medium - Can capture non-menu prices"
        },
        "main_page_extraction": {
            "description": "Extracts menu info directly from restaurant page",
            "selectors": ['[class*="food"]', '[class*="item"]', '[class*="product"]'],
            "success_rate": "Medium - Depends on page structure"
        }
    }
    
    for method, details in methods.items():
        print(f"\n📋 {method.replace('_', ' ').title()}")
        print(f"   Description: {details['description']}")
        print(f"   Success Rate: {details['success_rate']}")
        print(f"   Example Selectors: {', '.join(details['selectors'][:2])}")

if __name__ == "__main__":
    demo_menu_extraction()
    show_extraction_methods()
    
    print(f"\n=== NEXT STEPS ===")
    print("To run live menu scraping:")
    print("1. Use run_tripadvisor_menus.py for TripAdvisor")
    print("2. Use run_opentable_menus.py for OpenTable")
    print("3. Use run_menu_scraper_advanced.py for advanced extraction")
    print("\nNote: Live scraping may encounter rate limits or anti-bot measures.")
    print("The demo shows the data structure and capabilities.")