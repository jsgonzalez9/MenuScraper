#!/usr/bin/env python3
"""
Comprehensive Menu Scraping Session
Runs multiple scrapers to collect maximum menu data
"""

import asyncio
import json
import time
from datetime import datetime
from practical_ml_scraper import PracticalMLScraper
from priority1_balanced_scraper import Priority1BalancedScraper
from enhanced_dynamic_scraper import EnhancedDynamicScraper

# Extended restaurant list for comprehensive scraping
RESTAURANTS = [
    "Alinea Chicago",
    "Girl & the Goat Chicago", 
    "Au Cheval Chicago",
    "The Purple Pig Chicago",
    "Gibsons Bar & Steakhouse Chicago",
    "Lou Malnati's Pizzeria Chicago",
    "Portillo's Chicago",
    "Wildberry Pancakes & Cafe Chicago",
    "Smoque BBQ Chicago",
    "Kuma's Corner Chicago",
    "The Gage Chicago",
    "RPM Italian Chicago",
    "Bavette's Bar & Boeuf Chicago",
    "The Publican Chicago",
    "Frontera Grill Chicago",
    "Blackbird Chicago",
    "Next Restaurant Chicago",
    "Oriole Chicago",
    "Boka Chicago",
    "Topolobampo Chicago",
    "Pequod's Pizza Chicago",
    "Chicago Pizza & Oven Grinder Chicago",
    "Xoco Chicago",
    "Cafe Spiaggia Chicago",
    "Everest Chicago",
    "Maple & Ash Chicago",
    "Roister Chicago",
    "Dusek's Chicago",
    "Longman & Eagle Chicago",
    "Big Star Chicago",
    "Hopleaf Chicago",
    "Revolution Brewing Chicago",
    "Half Acre Beer Company Chicago",
    "Goose Island Brewery Chicago",
    "Lagunitas Brewing Chicago",
    "Piece Brewery Chicago",
    "Metropolitan Brewing Chicago",
    "Off Color Brewing Chicago",
    "Begyle Brewing Chicago",
    "Dovetail Brewery Chicago",
    "Maplewood Brewery Chicago",
    "Spiteful Brewing Chicago",
    "Urban Chestnut Brewing Chicago",
    "Cruz Blanca Brewery Chicago",
    "Forbidden Root Restaurant Chicago",
    "Band of Bohemia Chicago",
    "Haymarket Pub & Brewery Chicago",
    "Motor Row Brewing Chicago",
    "Burnt City Brewing Chicago",
    "Great Central Brewing Chicago"
]

async def run_comprehensive_scraping():
    """
    Run comprehensive scraping session with multiple scrapers
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results = {
        "session_info": {
            "timestamp": timestamp,
            "total_restaurants": len(RESTAURANTS),
            "scrapers_used": ["PracticalMLScraper", "Priority1BalancedScraper", "EnhancedDynamicScraper"]
        },
        "scraper_results": {},
        "combined_metrics": {
            "total_successful_extractions": 0,
            "total_menu_items": 0,
            "best_performing_scraper": None,
            "overall_success_rate": 0.0
        }
    }
    
    scrapers = {
        "PracticalMLScraper": PracticalMLScraper(),
        "Priority1BalancedScraper": Priority1BalancedScraper(),
        "EnhancedDynamicScraper": EnhancedDynamicScraper()
    }
    
    print(f"🚀 Starting comprehensive scraping session at {timestamp}")
    print(f"📊 Testing {len(RESTAURANTS)} restaurants with {len(scrapers)} scrapers")
    
    for scraper_name, scraper in scrapers.items():
        print(f"\n🔄 Running {scraper_name}...")
        start_time = time.time()
        
        scraper_results = {
            "successful_scrapes": 0,
            "total_items": 0,
            "processing_time": 0,
            "restaurant_results": []
        }
        
        for i, restaurant in enumerate(RESTAURANTS, 1):
            print(f"  📍 [{i}/{len(RESTAURANTS)}] {restaurant}")
            
            try:
                if scraper_name == "PracticalMLScraper":
                    result = await scraper.scrape_restaurant_menu(restaurant)
                elif scraper_name == "Priority1BalancedScraper":
                    result = await scraper.scrape_restaurant_menu(restaurant)
                else:  # EnhancedDynamicScraper
                    result = await scraper.scrape_restaurant_menu(restaurant)
                
                if result and result.get('success', False) and result.get('items'):
                    scraper_results["successful_scrapes"] += 1
                    scraper_results["total_items"] += len(result['items'])
                    print(f"    ✅ Success: {len(result['items'])} items")
                else:
                    print(f"    ❌ Failed: {result.get('error', 'Unknown error')}")
                
                scraper_results["restaurant_results"].append({
                    "restaurant": restaurant,
                    "result": result
                })
                
            except Exception as e:
                print(f"    💥 Exception: {str(e)}")
                scraper_results["restaurant_results"].append({
                    "restaurant": restaurant,
                    "result": {"success": False, "error": str(e)}
                })
        
        scraper_results["processing_time"] = time.time() - start_time
        scraper_results["success_rate"] = (scraper_results["successful_scrapes"] / len(RESTAURANTS)) * 100
        
        results["scraper_results"][scraper_name] = scraper_results
        
        print(f"  📈 {scraper_name} Results:")
        print(f"    Success Rate: {scraper_results['success_rate']:.1f}%")
        print(f"    Successful Scrapes: {scraper_results['successful_scrapes']}/{len(RESTAURANTS)}")
        print(f"    Total Items: {scraper_results['total_items']}")
        print(f"    Processing Time: {scraper_results['processing_time']:.1f}s")
    
    # Calculate combined metrics
    best_scraper = None
    best_success_rate = 0
    total_successful = 0
    total_items = 0
    
    for scraper_name, scraper_data in results["scraper_results"].items():
        if scraper_data["success_rate"] > best_success_rate:
            best_success_rate = scraper_data["success_rate"]
            best_scraper = scraper_name
        
        total_successful += scraper_data["successful_scrapes"]
        total_items += scraper_data["total_items"]
    
    results["combined_metrics"]["total_successful_extractions"] = total_successful
    results["combined_metrics"]["total_menu_items"] = total_items
    results["combined_metrics"]["best_performing_scraper"] = best_scraper
    results["combined_metrics"]["overall_success_rate"] = (total_successful / (len(RESTAURANTS) * len(scrapers))) * 100
    
    # Save results
    output_file = f"comprehensive_scraping_results_{timestamp}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n🎯 COMPREHENSIVE SCRAPING COMPLETE")
    print(f"📊 Overall Results:")
    print(f"  Best Performing Scraper: {best_scraper} ({best_success_rate:.1f}%)")
    print(f"  Total Successful Extractions: {total_successful}")
    print(f"  Total Menu Items Collected: {total_items}")
    print(f"  Overall Success Rate: {results['combined_metrics']['overall_success_rate']:.1f}%")
    print(f"  Results saved to: {output_file}")
    
    return results

if __name__ == "__main__":
    asyncio.run(run_comprehensive_scraping())