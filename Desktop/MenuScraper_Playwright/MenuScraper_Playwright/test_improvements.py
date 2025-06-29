#!/usr/bin/env python3
"""
Quick Test of Improved Menu Scraper
Demonstrates the enhanced capabilities with key improvements
"""

import json
import time
from datetime import datetime
from playwright.sync_api import sync_playwright
from improved_menu_scraper import ImprovedMenuScraper
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_improved_scraper():
    """Test the improved scraper on a small sample to demonstrate enhancements"""
    
    # Load restaurant data
    data_file = "c:\\Users\\cliff\\Desktop\\MenuScraper_Playwright\\MenuScraper_Playwright\\output\\chicago_restaurants_with_menus.json"
    
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        restaurants = data.get('restaurants', [])
        if not restaurants:
            print("❌ No restaurants found in data file")
            return
        
        # Test with a focused sample of 10 restaurants
        restaurants_with_urls = [r for r in restaurants if r.get('url')]
        test_restaurants = restaurants_with_urls[:10]
        
        print(f"🧪 Testing Improved Scraper on {len(test_restaurants)} restaurants")
        print("=" * 60)
        
        scraper = ImprovedMenuScraper()
        results = {
            'test_info': {
                'timestamp': datetime.now().isoformat(),
                'sample_size': len(test_restaurants),
                'scraper_version': 'improved_v1',
            },
            'results': [],
            'summary': {
                'total_tested': 0,
                'successful_extractions': 0,
                'total_items': 0,
                'ocr_usage': 0,
                'menu_pages_found': 0,
                'avg_processing_time': 0
            }
        }
        
        processing_times = []
        
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            
            try:
                for i, restaurant in enumerate(test_restaurants, 1):
                    start_time = time.time()
                    
                    print(f"\n🏪 [{i}/{len(test_restaurants)}] Testing: {restaurant.get('name', 'Unknown')}")
                    print(f"🔗 URL: {restaurant.get('url', 'No URL')}")
                    
                    page = browser.new_page()
                    
                    try:
                        # Set page timeout
                        page.set_default_timeout(30000)
                        
                        # Test the restaurant
                        menu_data = scraper.improved_menu_detection(page, restaurant['url'])
                        
                        processing_time = time.time() - start_time
                        processing_times.append(processing_time)
                        
                        # Compile result
                        restaurant_result = {
                            'restaurant_info': {
                                'name': restaurant.get('name', 'Unknown'),
                                'url': restaurant.get('url', ''),
                                'rating': restaurant.get('rating', 0),
                                'categories': restaurant.get('categories', [])
                            },
                            'menu_data': menu_data,
                            'processing_time': round(processing_time, 2)
                        }
                        
                        results['results'].append(restaurant_result)
                        
                        # Update summary
                        results['summary']['total_tested'] += 1
                        
                        if menu_data.get('scraping_success', False):
                            results['summary']['successful_extractions'] += 1
                            results['summary']['total_items'] += menu_data.get('total_items', 0)
                            
                            if menu_data.get('ocr_used', False):
                                results['summary']['ocr_usage'] += 1
                            
                            if menu_data.get('menu_page_found', False):
                                results['summary']['menu_pages_found'] += 1
                            
                            print(f"✅ Success! Found {menu_data.get('total_items', 0)} items in {processing_time:.1f}s")
                            
                            # Show key improvements
                            if menu_data.get('menu_page_found', False):
                                print(f"   🔗 Found dedicated menu page")
                            if menu_data.get('ocr_used', False):
                                print(f"   📸 OCR successfully used")
                            
                            # Show sample items with categories
                            sample_items = menu_data.get('menu_items', [])[:3]
                            for item in sample_items:
                                name = item.get('name', 'Unknown')
                                category = item.get('category', 'other')
                                confidence = item.get('confidence', 0)
                                sources = ', '.join(item.get('sources', []))
                                print(f"   📋 {name} [{category}] (conf: {confidence:.2f}, sources: {sources})")
                        else:
                            print(f"❌ No menu items found in {processing_time:.1f}s")
                            if 'error' in menu_data:
                                print(f"   Error: {menu_data['error']}")
                    
                    except Exception as e:
                        processing_time = time.time() - start_time
                        processing_times.append(processing_time)
                        
                        print(f"❌ Error processing restaurant: {e}")
                        
                        error_result = {
                            'restaurant_info': {
                                'name': restaurant.get('name', 'Unknown'),
                                'url': restaurant.get('url', '')
                            },
                            'menu_data': {
                                'scraping_success': False,
                                'total_items': 0,
                                'error': str(e)
                            },
                            'processing_time': round(processing_time, 2)
                        }
                        
                        results['results'].append(error_result)
                        results['summary']['total_tested'] += 1
                    
                    finally:
                        page.close()
                    
                    # Brief pause
                    time.sleep(1)
            
            finally:
                browser.close()
        
        # Calculate final statistics
        if processing_times:
            results['summary']['avg_processing_time'] = round(sum(processing_times) / len(processing_times), 2)
        
        # Save results
        output_file = "c:\\Users\\cliff\\Desktop\\MenuScraper_Playwright\\MenuScraper_Playwright\\output\\improved_scraper_test_results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Results saved to: {output_file}")
        
        # Print summary
        print_improvement_summary(results)
        
    except FileNotFoundError:
        print(f"❌ Data file not found: {data_file}")
    except Exception as e:
        print(f"❌ Error: {e}")

def print_improvement_summary(results):
    """Print summary highlighting improvements"""
    
    summary = results['summary']
    
    print(f"\n📊 IMPROVED SCRAPER TEST RESULTS")
    print("=" * 60)
    
    # Calculate success rate
    success_rate = 0
    if summary['total_tested'] > 0:
        success_rate = (summary['successful_extractions'] / summary['total_tested']) * 100
    
    avg_items = 0
    if summary['successful_extractions'] > 0:
        avg_items = summary['total_items'] / summary['successful_extractions']
    
    print(f"🎯 Success Rate: {success_rate:.1f}% ({summary['successful_extractions']}/{summary['total_tested']})")
    print(f"📋 Total Menu Items: {summary['total_items']}")
    print(f"📈 Avg Items per Success: {avg_items:.1f}")
    print(f"⏱️ Avg Processing Time: {summary['avg_processing_time']}s")
    
    # Highlight key improvements
    print(f"\n🚀 KEY IMPROVEMENTS")
    print(f"   🔗 Menu Pages Found: {summary['menu_pages_found']} restaurants")
    print(f"   📸 OCR Successfully Used: {summary['ocr_usage']} restaurants")
    
    # Show successful extractions with details
    successful_results = [r for r in results['results'] if r['menu_data'].get('scraping_success', False)]
    
    if successful_results:
        print(f"\n🏆 SUCCESSFUL EXTRACTIONS WITH IMPROVEMENTS")
        for i, result in enumerate(successful_results[:5], 1):
            name = result['restaurant_info']['name']
            items_count = result['menu_data']['total_items']
            menu_page = result['menu_data'].get('menu_page_found', False)
            ocr_used = result['menu_data'].get('ocr_used', False)
            strategies = result['menu_data'].get('strategies_used', 0)
            
            improvements = []
            if menu_page:
                improvements.append("Menu Page")
            if ocr_used:
                improvements.append("OCR")
            if strategies > 1:
                improvements.append(f"{strategies} Strategies")
            
            improvement_text = f" [{', '.join(improvements)}]" if improvements else ""
            
            print(f"   {i}. {name}: {items_count} items{improvement_text}")
            
            # Show sample items with categories
            sample_items = result['menu_data'].get('menu_items', [])[:2]
            for item in sample_items:
                item_name = item.get('name', 'Unknown')
                category = item.get('category', 'other')
                if category and category != 'other':
                    print(f"      • {item_name} [{category}]")
                else:
                    print(f"      • {item_name}")
    
    print("\n" + "=" * 60)

def compare_all_versions():
    """Compare all scraper versions"""
    
    print(f"\n📈 SCRAPER VERSION COMPARISON")
    print("=" * 60)
    
    # This would load and compare results from all versions
    # For now, just show the concept
    
    versions = [
        {"name": "Enhanced Scraper", "file": "enhanced_scraper_test_results.json", "sample_size": 5},
        {"name": "Advanced Scraper", "file": "advanced_test_results_n10.json", "sample_size": 10},
        {"name": "Improved Scraper", "file": "improved_scraper_test_results.json", "sample_size": 10}
    ]
    
    print(f"{'Version':<20} {'Sample':<8} {'Success Rate':<12} {'Avg Items':<10} {'Key Features'}")
    print("-" * 80)
    
    for version in versions:
        try:
            file_path = f"c:\\Users\\cliff\\Desktop\\MenuScraper_Playwright\\MenuScraper_Playwright\\output\\{version['file']}"
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if 'overall_stats' in data:
                # Advanced scraper format
                success_rate = data['overall_stats'].get('success_rate', 0)
                avg_items = data['overall_stats'].get('avg_items_per_success', 0)
                ocr_usage = data['overall_stats'].get('ocr_usage_count', 0)
            else:
                # Other formats
                summary = data.get('summary', {})
                total = summary.get('total_tested', 1)
                successful = summary.get('successful_extractions', 0)
                success_rate = (successful / total) * 100 if total > 0 else 0
                avg_items = summary.get('total_items', 0) / successful if successful > 0 else 0
                ocr_usage = summary.get('ocr_usage', 0)
            
            features = []
            if version['name'] == "Enhanced Scraper":
                features = ["Multi-strategy"]
            elif version['name'] == "Advanced Scraper":
                features = ["ML confidence", "Categories"]
            elif version['name'] == "Improved Scraper":
                features = ["Menu navigation", "Enhanced OCR", "Modern CSS"]
            
            print(f"{version['name']:<20} {version['sample_size']:<8} {success_rate:<12.1f} {avg_items:<10.1f} {', '.join(features)}")
            
        except Exception as e:
            print(f"{version['name']:<20} {version['sample_size']:<8} {'Error':<12} {'Error':<10} {str(e)[:30]}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    print("🚀 Testing Improved Menu Scraper")
    print("=" * 60)
    
    # Run the improved scraper test
    test_improved_scraper()
    
    # Compare all versions
    compare_all_versions()
    
    print("\n✅ Improved scraper testing completed!")