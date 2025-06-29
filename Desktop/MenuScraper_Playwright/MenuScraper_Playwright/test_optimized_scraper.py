#!/usr/bin/env python3
"""
Optimized Menu Scraper Test Suite
Comprehensive testing with multiple sample sizes and detailed analysis
"""

import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Any
from playwright.sync_api import sync_playwright
from optimized_menu_scraper import OptimizedMenuScraper

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_restaurant_data() -> List[Dict[str, str]]:
    """Load restaurant data from JSON file"""
    try:
        with open('restaurant_data.json', 'r') as f:
            data = json.load(f)
            return data.get('restaurants', [])
    except FileNotFoundError:
        logger.error("restaurant_data.json not found")
        return []
    except Exception as e:
        logger.error(f"Error loading restaurant data: {e}")
        return []

def run_optimized_scraper_test(restaurants: List[Dict], sample_size: int) -> Dict[str, Any]:
    """Run optimized scraper test"""
    logger.info(f"Starting optimized scraper test with {sample_size} restaurants")
    
    scraper = OptimizedMenuScraper()
    results = {
        'test_info': {
            'timestamp': datetime.now().isoformat(),
            'sample_size': sample_size,
            'scraper_version': 'optimized_v1',
            'target_success_rate': '50%+'
        },
        'restaurants': {},
        'summary': {
            'total_tested': 0,
            'successful_extractions': 0,
            'success_rate': 0.0,
            'total_menu_items': 0,
            'avg_items_per_success': 0.0,
            'ocr_usage_count': 0,
            'menu_pages_found': 0,
            'structured_data_usage': 0,
            'avg_processing_time': 0.0,
            'avg_quality_score': 0.0,
            'strategy_distribution': {},
            'category_distribution': {},
            'price_extraction_rate': 0.0
        }
    }
    
    test_restaurants = restaurants[:sample_size]
    total_processing_time = 0
    total_quality_score = 0
    successful_restaurants = []
    strategy_counts = {}
    category_counts = {}
    total_items_with_prices = 0
    total_items = 0
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        for i, restaurant in enumerate(test_restaurants, 1):
            name = restaurant.get('name', f'Restaurant_{i}')
            url = restaurant.get('url', '')
            
            logger.info(f"Testing {i}/{sample_size}: {name}")
            
            try:
                # Run optimized scraper
                result = scraper.optimized_menu_detection(page, url)
                
                # Store result
                results['restaurants'][name] = result
                
                # Update summary statistics
                results['summary']['total_tested'] += 1
                total_processing_time += result.get('processing_time', 0)
                total_quality_score += result.get('quality_score', 0)
                
                if result.get('scraping_success', False):
                    results['summary']['successful_extractions'] += 1
                    successful_restaurants.append(name)
                    
                    # Count menu items
                    menu_items = result.get('menu_items', [])
                    item_count = len(menu_items)
                    results['summary']['total_menu_items'] += item_count
                    total_items += item_count
                    
                    # Count items with prices
                    items_with_prices = sum(1 for item in menu_items if item.get('price'))
                    total_items_with_prices += items_with_prices
                    
                    # Count categories
                    for item in menu_items:
                        category = item.get('category', 'other')
                        category_counts[category] = category_counts.get(category, 0) + 1
                
                # Count usage statistics
                if result.get('ocr_used', False):
                    results['summary']['ocr_usage_count'] += 1
                
                if result.get('menu_page_found', False):
                    results['summary']['menu_pages_found'] += 1
                
                if 'structured' in result.get('extraction_methods', []):
                    results['summary']['structured_data_usage'] += 1
                
                # Count strategies
                for method in result.get('extraction_methods', []):
                    strategy_counts[method] = strategy_counts.get(method, 0) + 1
                
                logger.info(f"  Result: {'SUCCESS' if result.get('scraping_success') else 'FAILED'} - "
                           f"{result.get('total_items', 0)} items - "
                           f"{result.get('processing_time', 0):.1f}s")
                
            except Exception as e:
                logger.error(f"Error testing {name}: {e}")
                results['restaurants'][name] = {
                    'error': str(e),
                    'scraping_success': False,
                    'total_items': 0
                }
                results['summary']['total_tested'] += 1
        
        browser.close()
    
    # Calculate final statistics
    total_tested = results['summary']['total_tested']
    successful = results['summary']['successful_extractions']
    
    if total_tested > 0:
        results['summary']['success_rate'] = round((successful / total_tested) * 100, 1)
        results['summary']['avg_processing_time'] = round(total_processing_time / total_tested, 2)
        results['summary']['avg_quality_score'] = round(total_quality_score / total_tested, 3)
    
    if successful > 0:
        results['summary']['avg_items_per_success'] = round(results['summary']['total_menu_items'] / successful, 1)
    
    if total_items > 0:
        results['summary']['price_extraction_rate'] = round((total_items_with_prices / total_items) * 100, 1)
    
    results['summary']['strategy_distribution'] = strategy_counts
    results['summary']['category_distribution'] = category_counts
    results['summary']['successful_restaurants'] = successful_restaurants
    
    return results

def save_results(results: Dict[str, Any], filename: str):
    """Save test results to JSON file"""
    try:
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results saved to {filename}")
    except Exception as e:
        logger.error(f"Error saving results: {e}")

def print_optimized_summary(results: Dict[str, Any]):
    """Print comprehensive test summary"""
    summary = results['summary']
    test_info = results['test_info']
    
    print("\n" + "="*80)
    print("OPTIMIZED MENU SCRAPER TEST RESULTS")
    print("="*80)
    
    print(f"\n📊 TEST OVERVIEW:")
    print(f"   Sample Size: {test_info['sample_size']} restaurants")
    print(f"   Target Success Rate: {test_info['target_success_rate']}")
    print(f"   Scraper Version: {test_info['scraper_version']}")
    print(f"   Test Date: {test_info['timestamp'][:19]}")
    
    print(f"\n🎯 PERFORMANCE METRICS:")
    success_rate = summary['success_rate']
    target_met = "✅ TARGET MET" if success_rate >= 50.0 else "❌ TARGET MISSED"
    print(f"   Success Rate: {success_rate}% ({summary['successful_extractions']}/{summary['total_tested']}) {target_met}")
    print(f"   Total Menu Items: {summary['total_menu_items']}")
    print(f"   Avg Items per Success: {summary['avg_items_per_success']}")
    print(f"   Avg Processing Time: {summary['avg_processing_time']}s")
    print(f"   Avg Quality Score: {summary['avg_quality_score']}")
    
    print(f"\n🔧 FEATURE UTILIZATION:")
    print(f"   OCR Usage: {summary['ocr_usage_count']}/{summary['total_tested']} ({round(summary['ocr_usage_count']/summary['total_tested']*100, 1)}%)")
    print(f"   Menu Pages Found: {summary['menu_pages_found']}/{summary['total_tested']} ({round(summary['menu_pages_found']/summary['total_tested']*100, 1)}%)")
    print(f"   Structured Data Usage: {summary['structured_data_usage']}/{summary['total_tested']} ({round(summary['structured_data_usage']/summary['total_tested']*100, 1)}%)")
    print(f"   Price Extraction Rate: {summary['price_extraction_rate']}%")
    
    print(f"\n📈 STRATEGY DISTRIBUTION:")
    for strategy, count in summary['strategy_distribution'].items():
        percentage = round((count / summary['total_tested']) * 100, 1)
        print(f"   {strategy.capitalize()}: {count} uses ({percentage}%)")
    
    print(f"\n🍽️ CATEGORY DISTRIBUTION:")
    for category, count in summary['category_distribution'].items():
        percentage = round((count / summary['total_menu_items']) * 100, 1) if summary['total_menu_items'] > 0 else 0
        print(f"   {category.capitalize()}: {count} items ({percentage}%)")
    
    print(f"\n✅ SUCCESSFUL RESTAURANTS:")
    for restaurant in summary.get('successful_restaurants', [])[:10]:
        restaurant_data = results['restaurants'].get(restaurant, {})
        items = restaurant_data.get('total_items', 0)
        quality = restaurant_data.get('quality_score', 0)
        methods = ', '.join(restaurant_data.get('extraction_methods', []))
        print(f"   • {restaurant}: {items} items (quality: {quality:.2f}, methods: {methods})")
    
    if len(summary.get('successful_restaurants', [])) > 10:
        print(f"   ... and {len(summary['successful_restaurants']) - 10} more")
    
    # Performance analysis
    print(f"\n📋 PERFORMANCE ANALYSIS:")
    if success_rate >= 50.0:
        gap = success_rate - 50.0
        print(f"   🎉 SUCCESS: Exceeded target by {gap:.1f} percentage points")
    else:
        gap = 50.0 - success_rate
        print(f"   ⚠️  IMPROVEMENT NEEDED: {gap:.1f} percentage points below target")
    
    print(f"   Quality Score: {'Excellent' if summary['avg_quality_score'] > 0.8 else 'Good' if summary['avg_quality_score'] > 0.6 else 'Needs Improvement'}")
    print(f"   Processing Speed: {'Fast' if summary['avg_processing_time'] < 10 else 'Moderate' if summary['avg_processing_time'] < 20 else 'Slow'}")

def compare_scraper_versions(optimized_results: Dict[str, Any]):
    """Compare optimized scraper with previous versions"""
    print("\n" + "="*80)
    print("SCRAPER VERSION COMPARISON")
    print("="*80)
    
    # Load previous results for comparison
    previous_results = {}
    
    try:
        with open('enhanced_scraper_test_results.json', 'r') as f:
            enhanced_data = json.load(f)
            previous_results['Enhanced'] = {
                'success_rate': enhanced_data.get('summary', {}).get('success_rate', 0),
                'avg_items': enhanced_data.get('summary', {}).get('avg_items_per_success', 0)
            }
    except:
        previous_results['Enhanced'] = {'success_rate': 40.0, 'avg_items': 10.5}  # From previous tests
    
    try:
        with open('advanced_test_results_n50.json', 'r') as f:
            advanced_data = json.load(f)
            previous_results['Advanced'] = {
                'success_rate': advanced_data.get('summary', {}).get('success_rate', 0),
                'avg_items': advanced_data.get('summary', {}).get('avg_items_per_success', 0)
            }
    except:
        previous_results['Advanced'] = {'success_rate': 36.0, 'avg_items': 5.5}  # From previous tests
    
    try:
        with open('improved_scraper_test_results.json', 'r') as f:
            improved_data = json.load(f)
            previous_results['Improved'] = {
                'success_rate': improved_data.get('summary', {}).get('success_rate', 0),
                'avg_items': improved_data.get('summary', {}).get('avg_items_per_success', 0)
            }
    except:
        previous_results['Improved'] = {'success_rate': 30.0, 'avg_items': 9.3}  # From previous tests
    
    # Add current results
    current_summary = optimized_results['summary']
    previous_results['Optimized'] = {
        'success_rate': current_summary['success_rate'],
        'avg_items': current_summary['avg_items_per_success']
    }
    
    print(f"\n📊 SUCCESS RATE COMPARISON:")
    for version, data in previous_results.items():
        rate = data['success_rate']
        status = "🏆" if version == 'Optimized' else "📈" if rate >= 40 else "📉"
        print(f"   {status} {version} Scraper: {rate}% success rate")
    
    print(f"\n🍽️ AVERAGE ITEMS PER SUCCESS:")
    for version, data in previous_results.items():
        items = data['avg_items']
        status = "🏆" if version == 'Optimized' else "📈" if items >= 8 else "📉"
        print(f"   {status} {version} Scraper: {items} items per success")
    
    # Calculate improvements
    if 'Enhanced' in previous_results:
        enhanced_rate = previous_results['Enhanced']['success_rate']
        current_rate = current_summary['success_rate']
        improvement = current_rate - enhanced_rate
        
        print(f"\n📈 IMPROVEMENT OVER ENHANCED SCRAPER:")
        print(f"   Success Rate: {improvement:+.1f} percentage points")
        print(f"   Status: {'Significant Improvement' if improvement > 5 else 'Moderate Improvement' if improvement > 0 else 'Needs Work'}")

def main():
    """Main test execution"""
    print("Loading restaurant data...")
    restaurants = load_restaurant_data()
    
    if not restaurants:
        print("No restaurant data available. Please ensure restaurant_data.json exists.")
        return
    
    print(f"Loaded {len(restaurants)} restaurants")
    
    # Test with sample size of 20 (balanced for thorough testing)
    sample_size = 20
    
    print(f"\nTesting Optimized Menu Scraper with {sample_size} restaurants...")
    results = run_optimized_scraper_test(restaurants, sample_size)
    
    # Save results
    filename = f'optimized_test_results_n{sample_size}.json'
    save_results(results, filename)
    
    # Print summary
    print_optimized_summary(results)
    
    # Compare with previous versions
    compare_scraper_versions(results)
    
    print(f"\n💾 Detailed results saved to: {filename}")
    print("\n🎯 NEXT STEPS:")
    if results['summary']['success_rate'] >= 50.0:
        print("   ✅ Target achieved! Consider testing with larger sample sizes")
        print("   🔄 Focus on consistency and edge case handling")
    else:
        gap = 50.0 - results['summary']['success_rate']
        print(f"   ⚠️  Need {gap:.1f}% improvement to reach 50% target")
        print("   🔧 Consider additional optimization strategies")
    
    print("   📊 Analyze failed cases for further improvements")
    print("   🚀 Consider implementing machine learning enhancements")

if __name__ == "__main__":
    main()