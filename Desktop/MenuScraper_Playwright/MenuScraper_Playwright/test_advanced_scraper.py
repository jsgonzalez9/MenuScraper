#!/usr/bin/env python3
"""
Advanced Menu Scraper Test - Large Sample Size
Tests the advanced scraper on a larger dataset to measure improvements
"""

import json
import time
from datetime import datetime
import os
from typing import Dict, List, Any
from playwright.sync_api import sync_playwright
from advanced_menu_scraper import AdvancedMenuScraper
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import statistics

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_advanced_scraper_large_sample():
    """Test the advanced scraper with a larger sample size"""
    
    # Load restaurant data
    data_file = "c:\\Users\\cliff\\Desktop\\MenuScraper_Playwright\\MenuScraper_Playwright\\output\\chicago_restaurants_with_menus.json"
    
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        restaurants = data.get('restaurants', [])
        if not restaurants:
            print("❌ No restaurants found in data file")
            return
        
        print(f"📊 Loaded {len(restaurants)} restaurants from data file")
        
        # Filter restaurants with URLs and select larger sample
        restaurants_with_urls = [r for r in restaurants if r.get('url')]
        
        if not restaurants_with_urls:
            print("❌ No restaurants with URLs found")
            return
        
        print(f"🔗 Found {len(restaurants_with_urls)} restaurants with URLs")
        
        # Test with larger sample sizes
        sample_sizes = [10, 25, 50]  # Progressive testing
        
        for sample_size in sample_sizes:
            if len(restaurants_with_urls) < sample_size:
                print(f"⚠️ Only {len(restaurants_with_urls)} restaurants available, skipping sample size {sample_size}")
                continue
            
            print(f"\n🧪 Testing with sample size: {sample_size}")
            print("=" * 60)
            
            # Select sample
            test_restaurants = restaurants_with_urls[:sample_size]
            
            # Run test
            results = run_advanced_test(test_restaurants, sample_size)
            
            # Save results
            output_file = f"c:\\Users\\cliff\\Desktop\\MenuScraper_Playwright\\MenuScraper_Playwright\\output\\advanced_test_results_n{sample_size}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Results saved to: {output_file}")
            
            # Print summary
            print_test_summary(results, sample_size)
            
            # Brief pause between tests
            if sample_size < max(sample_sizes):
                print("\n⏳ Pausing before next test...")
                time.sleep(5)
    
    except FileNotFoundError:
        print(f"❌ Data file not found: {data_file}")
        print("Please ensure the chicago_restaurants_with_menus.json file exists")
    except Exception as e:
        print(f"❌ Error loading data: {e}")

def run_advanced_test(restaurants: List[Dict], sample_size: int) -> Dict[str, Any]:
    """Run the advanced scraper test on a sample of restaurants"""
    
    scraper = AdvancedMenuScraper()
    results = {
        'test_info': {
            'timestamp': datetime.now().isoformat(),
            'sample_size': sample_size,
            'scraper_version': 'advanced_v2',
            'test_duration': None
        },
        'overall_stats': {
            'total_tested': 0,
            'successful_extractions': 0,
            'success_rate': 0.0,
            'total_menu_items': 0,
            'avg_items_per_success': 0.0,
            'ocr_usage_count': 0,
            'strategies_used': {},
            'confidence_distribution': {},
            'category_distribution': {}
        },
        'restaurant_results': [],
        'performance_metrics': {
            'avg_processing_time': 0.0,
            'fastest_extraction': None,
            'slowest_extraction': None,
            'timeout_count': 0,
            'error_count': 0
        }
    }
    
    start_time = time.time()
    processing_times = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        
        try:
            for i, restaurant in enumerate(restaurants, 1):
                restaurant_start = time.time()
                
                print(f"\n🏪 [{i}/{sample_size}] Testing: {restaurant.get('name', 'Unknown')}")
                print(f"🔗 URL: {restaurant.get('url', 'No URL')}")
                
                page = browser.new_page()
                
                try:
                    # Set page timeout
                    page.set_default_timeout(45000)  # 45 seconds
                    
                    # Test the restaurant
                    menu_data = scraper.advanced_menu_detection(page, restaurant['url'])
                    
                    processing_time = time.time() - restaurant_start
                    processing_times.append(processing_time)
                    
                    # Compile restaurant result
                    restaurant_result = {
                        'restaurant_info': {
                            'name': restaurant.get('name', 'Unknown'),
                            'url': restaurant.get('url', ''),
                            'rating': restaurant.get('rating', 0),
                            'categories': restaurant.get('categories', [])
                        },
                        'menu_data': menu_data,
                        'processing_time': round(processing_time, 2),
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    results['restaurant_results'].append(restaurant_result)
                    
                    # Update stats
                    if menu_data.get('scraping_success', False):
                        results['overall_stats']['successful_extractions'] += 1
                        items_count = menu_data.get('total_items', 0)
                        results['overall_stats']['total_menu_items'] += items_count
                        
                        if menu_data.get('ocr_used', False):
                            results['overall_stats']['ocr_usage_count'] += 1
                        
                        # Track strategies used
                        strategies = menu_data.get('strategies_used', 0)
                        strategy_key = f"{strategies}_strategies"
                        results['overall_stats']['strategies_used'][strategy_key] = \
                            results['overall_stats']['strategies_used'].get(strategy_key, 0) + 1
                        
                        # Track confidence and categories
                        for item in menu_data.get('menu_items', []):
                            confidence = item.get('confidence', 0)
                            confidence_bucket = f"{int(confidence * 10) * 10}-{int(confidence * 10) * 10 + 9}%"
                            results['overall_stats']['confidence_distribution'][confidence_bucket] = \
                                results['overall_stats']['confidence_distribution'].get(confidence_bucket, 0) + 1
                            
                            category = item.get('category', 'other')
                            results['overall_stats']['category_distribution'][category] = \
                                results['overall_stats']['category_distribution'].get(category, 0) + 1
                        
                        print(f"✅ Success! Found {items_count} items in {processing_time:.1f}s")
                        
                        # Show sample items
                        sample_items = menu_data.get('menu_items', [])[:3]
                        for item in sample_items:
                            print(f"   📋 {item.get('name', 'Unknown')} ({item.get('confidence', 0):.2f} confidence)")
                    else:
                        print(f"❌ No menu items found in {processing_time:.1f}s")
                        if 'error' in menu_data:
                            print(f"   Error: {menu_data['error']}")
                            results['performance_metrics']['error_count'] += 1
                    
                    results['overall_stats']['total_tested'] += 1
                    
                except Exception as e:
                    processing_time = time.time() - restaurant_start
                    processing_times.append(processing_time)
                    
                    print(f"❌ Error processing restaurant: {e}")
                    
                    error_result = {
                        'restaurant_info': {
                            'name': restaurant.get('name', 'Unknown'),
                            'url': restaurant.get('url', ''),
                            'rating': restaurant.get('rating', 0),
                            'categories': restaurant.get('categories', [])
                        },
                        'menu_data': {
                            'scraping_success': False,
                            'total_items': 0,
                            'error': str(e)
                        },
                        'processing_time': round(processing_time, 2),
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    results['restaurant_results'].append(error_result)
                    results['overall_stats']['total_tested'] += 1
                    results['performance_metrics']['error_count'] += 1
                
                finally:
                    page.close()
                
                # Brief pause between requests
                time.sleep(1)
        
        finally:
            browser.close()
    
    # Calculate final statistics
    total_time = time.time() - start_time
    results['test_info']['test_duration'] = round(total_time, 2)
    
    if results['overall_stats']['total_tested'] > 0:
        results['overall_stats']['success_rate'] = round(
            (results['overall_stats']['successful_extractions'] / results['overall_stats']['total_tested']) * 100, 1
        )
    
    if results['overall_stats']['successful_extractions'] > 0:
        results['overall_stats']['avg_items_per_success'] = round(
            results['overall_stats']['total_menu_items'] / results['overall_stats']['successful_extractions'], 1
        )
    
    if processing_times:
        results['performance_metrics']['avg_processing_time'] = round(statistics.mean(processing_times), 2)
        results['performance_metrics']['fastest_extraction'] = round(min(processing_times), 2)
        results['performance_metrics']['slowest_extraction'] = round(max(processing_times), 2)
    
    return results

def print_test_summary(results: Dict[str, Any], sample_size: int):
    """Print a comprehensive test summary"""
    
    stats = results['overall_stats']
    perf = results['performance_metrics']
    
    print(f"\n📊 ADVANCED SCRAPER TEST RESULTS (n={sample_size})")
    print("=" * 60)
    
    # Overall Performance
    print(f"🎯 Success Rate: {stats['success_rate']}% ({stats['successful_extractions']}/{stats['total_tested']})")
    print(f"📋 Total Menu Items: {stats['total_menu_items']}")
    print(f"📈 Avg Items per Success: {stats['avg_items_per_success']}")
    print(f"🖼️ OCR Usage: {stats['ocr_usage_count']} restaurants")
    
    # Performance Metrics
    print(f"\n⏱️ PERFORMANCE METRICS")
    print(f"   Average Processing Time: {perf['avg_processing_time']}s")
    print(f"   Fastest Extraction: {perf['fastest_extraction']}s")
    print(f"   Slowest Extraction: {perf['slowest_extraction']}s")
    print(f"   Errors: {perf['error_count']}")
    
    # Strategy Usage
    if stats['strategies_used']:
        print(f"\n🔧 STRATEGY USAGE")
        for strategy, count in stats['strategies_used'].items():
            print(f"   {strategy}: {count} restaurants")
    
    # Confidence Distribution
    if stats['confidence_distribution']:
        print(f"\n📊 CONFIDENCE DISTRIBUTION")
        for conf_range, count in sorted(stats['confidence_distribution'].items()):
            print(f"   {conf_range}: {count} items")
    
    # Category Distribution
    if stats['category_distribution']:
        print(f"\n🍽️ FOOD CATEGORY DISTRIBUTION")
        sorted_categories = sorted(stats['category_distribution'].items(), key=lambda x: x[1], reverse=True)
        for category, count in sorted_categories[:10]:  # Top 10 categories
            print(f"   {category}: {count} items")
    
    # Sample successful extractions
    successful_results = [r for r in results['restaurant_results'] if r['menu_data'].get('scraping_success', False)]
    if successful_results:
        print(f"\n🏆 SAMPLE SUCCESSFUL EXTRACTIONS")
        for i, result in enumerate(successful_results[:3], 1):
            name = result['restaurant_info']['name']
            items_count = result['menu_data']['total_items']
            processing_time = result['processing_time']
            print(f"   {i}. {name}: {items_count} items ({processing_time}s)")
            
            # Show sample menu items
            sample_items = result['menu_data'].get('menu_items', [])[:2]
            for item in sample_items:
                item_name = item.get('name', 'Unknown')
                confidence = item.get('confidence', 0)
                sources = ', '.join(item.get('sources', []))
                print(f"      • {item_name} (conf: {confidence:.2f}, sources: {sources})")
    
    print("\n" + "=" * 60)

def compare_with_previous_results():
    """Compare advanced results with previous enhanced results"""
    
    try:
        # Load previous enhanced results
        enhanced_file = "c:\\Users\\cliff\\Desktop\\MenuScraper_Playwright\\MenuScraper_Playwright\\output\\enhanced_scraper_test_results.json"
        with open(enhanced_file, 'r', encoding='utf-8') as f:
            enhanced_data = json.load(f)
        
        # Load latest advanced results
        advanced_files = [
            "c:\\Users\\cliff\\Desktop\\MenuScraper_Playwright\\MenuScraper_Playwright\\output\\advanced_test_results_n10.json",
            "c:\\Users\\cliff\\Desktop\\MenuScraper_Playwright\\MenuScraper_Playwright\\output\\advanced_test_results_n25.json",
            "c:\\Users\\cliff\\Desktop\\MenuScraper_Playwright\\MenuScraper_Playwright\\output\\advanced_test_results_n50.json"
        ]
        
        print(f"\n📈 COMPARISON WITH PREVIOUS RESULTS")
        print("=" * 60)
        
        # Enhanced scraper baseline
        enhanced_success_rate = enhanced_data.get('overall_stats', {}).get('success_rate', 0)
        enhanced_avg_items = enhanced_data.get('overall_stats', {}).get('avg_items_per_success', 0)
        
        print(f"📊 Enhanced Scraper Baseline (n=5):")
        print(f"   Success Rate: {enhanced_success_rate}%")
        print(f"   Avg Items per Success: {enhanced_avg_items}")
        
        # Compare with advanced results
        for advanced_file in advanced_files:
            if os.path.exists(advanced_file):
                with open(advanced_file, 'r', encoding='utf-8') as f:
                    advanced_data = json.load(f)
                
                sample_size = advanced_data['test_info']['sample_size']
                success_rate = advanced_data['overall_stats']['success_rate']
                avg_items = advanced_data['overall_stats']['avg_items_per_success']
                
                improvement_rate = success_rate - enhanced_success_rate
                improvement_items = avg_items - enhanced_avg_items
                
                print(f"\n🚀 Advanced Scraper (n={sample_size}):")
                print(f"   Success Rate: {success_rate}% ({improvement_rate:+.1f}% vs baseline)")
                print(f"   Avg Items per Success: {avg_items} ({improvement_items:+.1f} vs baseline)")
        
        print("\n" + "=" * 60)
        
    except Exception as e:
        print(f"⚠️ Could not compare with previous results: {e}")

if __name__ == "__main__":
    print("🚀 Starting Advanced Menu Scraper Large Sample Test")
    print("=" * 60)
    
    # Run the large sample test
    test_advanced_scraper_large_sample()
    
    # Compare with previous results
    compare_with_previous_results()
    
    print("\n✅ Advanced scraper testing completed!")