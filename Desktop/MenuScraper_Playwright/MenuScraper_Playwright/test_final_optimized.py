#!/usr/bin/env python3
"""
Final Optimized Menu Scraper Test Suite
Testing the fixed version with comprehensive analysis
"""

import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Any
from playwright.sync_api import sync_playwright
from final_optimized_scraper import FinalOptimizedMenuScraper

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

def run_final_optimized_test(restaurants: List[Dict], sample_size: int) -> Dict[str, Any]:
    """Run final optimized scraper test"""
    logger.info(f"Starting final optimized scraper test with {sample_size} restaurants")
    
    scraper = FinalOptimizedMenuScraper()
    results = {
        'test_info': {
            'timestamp': datetime.now().isoformat(),
            'sample_size': sample_size,
            'scraper_version': 'final_optimized_v1',
            'target_success_rate': '50%+',
            'fixes_applied': [
                'Fixed CSS selector issues',
                'Improved error handling',
                'More permissive validation',
                'Better fallback strategies',
                'Simplified extraction methods'
            ]
        },
        'restaurants': {},
        'summary': {
            'total_tested': 0,
            'successful_extractions': 0,
            'success_rate': 0.0,
            'total_menu_items': 0,
            'avg_items_per_success': 0.0,
            'menu_pages_found': 0,
            'structured_data_usage': 0,
            'avg_processing_time': 0.0,
            'avg_quality_score': 0.0,
            'strategy_distribution': {},
            'category_distribution': {},
            'price_extraction_rate': 0.0,
            'error_count': 0
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
    error_count = 0
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        for i, restaurant in enumerate(test_restaurants, 1):
            name = restaurant.get('name', f'Restaurant_{i}')
            url = restaurant.get('url', '')
            
            logger.info(f"Testing {i}/{sample_size}: {name}")
            
            try:
                # Run final optimized scraper
                result = scraper.final_optimized_detection(page, url)
                
                # Store result
                results['restaurants'][name] = result
                
                # Update summary statistics
                results['summary']['total_tested'] += 1
                total_processing_time += result.get('processing_time', 0)
                total_quality_score += result.get('quality_score', 0)
                
                if result.get('error'):
                    error_count += 1
                
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
                if result.get('menu_page_found', False):
                    results['summary']['menu_pages_found'] += 1
                
                if 'structured' in result.get('extraction_methods', []):
                    results['summary']['structured_data_usage'] += 1
                
                # Count strategies
                for method in result.get('extraction_methods', []):
                    strategy_counts[method] = strategy_counts.get(method, 0) + 1
                
                status = 'SUCCESS' if result.get('scraping_success') else 'FAILED'
                items_found = result.get('total_items', 0)
                processing_time = result.get('processing_time', 0)
                strategies_used = result.get('strategies_used', 0)
                
                logger.info(f"  Result: {status} - {items_found} items - {processing_time:.1f}s - {strategies_used} strategies")
                
            except Exception as e:
                logger.error(f"Error testing {name}: {e}")
                results['restaurants'][name] = {
                    'error': str(e),
                    'scraping_success': False,
                    'total_items': 0
                }
                results['summary']['total_tested'] += 1
                error_count += 1
        
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
    results['summary']['error_count'] = error_count
    
    return results

def save_results(results: Dict[str, Any], filename: str):
    """Save test results to JSON file"""
    try:
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results saved to {filename}")
    except Exception as e:
        logger.error(f"Error saving results: {e}")

def print_final_optimized_summary(results: Dict[str, Any]):
    """Print comprehensive test summary"""
    summary = results['summary']
    test_info = results['test_info']
    
    print("\n" + "="*80)
    print("FINAL OPTIMIZED MENU SCRAPER TEST RESULTS")
    print("="*80)
    
    print(f"\n📊 TEST OVERVIEW:")
    print(f"   Sample Size: {test_info['sample_size']} restaurants")
    print(f"   Target Success Rate: {test_info['target_success_rate']}")
    print(f"   Scraper Version: {test_info['scraper_version']}")
    print(f"   Test Date: {test_info['timestamp'][:19]}")
    
    print(f"\n🔧 FIXES APPLIED:")
    for fix in test_info['fixes_applied']:
        print(f"   ✅ {fix}")
    
    print(f"\n🎯 PERFORMANCE METRICS:")
    success_rate = summary['success_rate']
    target_met = "✅ TARGET MET" if success_rate >= 50.0 else "❌ TARGET MISSED"
    print(f"   Success Rate: {success_rate}% ({summary['successful_extractions']}/{summary['total_tested']}) {target_met}")
    print(f"   Total Menu Items: {summary['total_menu_items']}")
    print(f"   Avg Items per Success: {summary['avg_items_per_success']}")
    print(f"   Avg Processing Time: {summary['avg_processing_time']}s")
    print(f"   Avg Quality Score: {summary['avg_quality_score']}")
    print(f"   Error Count: {summary['error_count']}/{summary['total_tested']}")
    
    print(f"\n🔧 FEATURE UTILIZATION:")
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
        print(f"   🚀 Ready for production deployment")
    else:
        gap = 50.0 - success_rate
        print(f"   ⚠️  IMPROVEMENT NEEDED: {gap:.1f} percentage points below target")
        print(f"   🔧 Consider additional optimization strategies")
    
    print(f"   Quality Score: {'Excellent' if summary['avg_quality_score'] > 0.8 else 'Good' if summary['avg_quality_score'] > 0.6 else 'Needs Improvement'}")
    print(f"   Processing Speed: {'Fast' if summary['avg_processing_time'] < 10 else 'Moderate' if summary['avg_processing_time'] < 20 else 'Slow'}")
    print(f"   Error Rate: {round(summary['error_count']/summary['total_tested']*100, 1)}%")

def compare_all_scraper_versions(final_results: Dict[str, Any]):
    """Compare all scraper versions"""
    print("\n" + "="*80)
    print("COMPREHENSIVE SCRAPER VERSION COMPARISON")
    print("="*80)
    
    # Load previous results for comparison
    versions = {}
    
    # Enhanced scraper
    try:
        with open('enhanced_scraper_test_results.json', 'r') as f:
            enhanced_data = json.load(f)
            versions['Enhanced'] = {
                'success_rate': enhanced_data.get('summary', {}).get('success_rate', 40.0),
                'avg_items': enhanced_data.get('summary', {}).get('avg_items_per_success', 10.5)
            }
    except:
        versions['Enhanced'] = {'success_rate': 40.0, 'avg_items': 10.5}
    
    # Advanced scraper
    try:
        with open('advanced_test_results_n50.json', 'r') as f:
            advanced_data = json.load(f)
            versions['Advanced'] = {
                'success_rate': advanced_data.get('summary', {}).get('success_rate', 36.0),
                'avg_items': advanced_data.get('summary', {}).get('avg_items_per_success', 5.5)
            }
    except:
        versions['Advanced'] = {'success_rate': 36.0, 'avg_items': 5.5}
    
    # Improved scraper
    try:
        with open('improved_scraper_test_results.json', 'r') as f:
            improved_data = json.load(f)
            versions['Improved'] = {
                'success_rate': improved_data.get('summary', {}).get('success_rate', 30.0),
                'avg_items': improved_data.get('summary', {}).get('avg_items_per_success', 9.3)
            }
    except:
        versions['Improved'] = {'success_rate': 30.0, 'avg_items': 9.3}
    
    # Next-gen scraper
    try:
        with open('nextgen_test_results_n30.json', 'r') as f:
            nextgen_data = json.load(f)
            versions['Next-Gen'] = {
                'success_rate': nextgen_data.get('summary', {}).get('success_rate', 6.7),
                'avg_items': nextgen_data.get('summary', {}).get('avg_items_per_success', 29.0)
            }
    except:
        versions['Next-Gen'] = {'success_rate': 6.7, 'avg_items': 29.0}
    
    # Optimized scraper (failed)
    versions['Optimized'] = {'success_rate': 0.0, 'avg_items': 0.0}
    
    # Final optimized scraper (current)
    current_summary = final_results['summary']
    versions['Final Optimized'] = {
        'success_rate': current_summary['success_rate'],
        'avg_items': current_summary['avg_items_per_success']
    }
    
    print(f"\n📊 SUCCESS RATE EVOLUTION:")
    for version, data in versions.items():
        rate = data['success_rate']
        if version == 'Final Optimized':
            status = "🏆 CURRENT"
        elif rate >= 50:
            status = "🎯 TARGET MET"
        elif rate >= 30:
            status = "📈 GOOD"
        elif rate >= 10:
            status = "📉 POOR"
        else:
            status = "❌ FAILED"
        print(f"   {status} {version}: {rate}% success rate")
    
    print(f"\n🍽️ ITEMS PER SUCCESS EVOLUTION:")
    for version, data in versions.items():
        items = data['avg_items']
        if version == 'Final Optimized':
            status = "🏆 CURRENT"
        elif items >= 15:
            status = "🎯 EXCELLENT"
        elif items >= 8:
            status = "📈 GOOD"
        elif items >= 5:
            status = "📉 FAIR"
        else:
            status = "❌ POOR"
        print(f"   {status} {version}: {items} items per success")
    
    # Calculate overall improvement
    best_previous = max(v['success_rate'] for k, v in versions.items() if k != 'Final Optimized')
    current_rate = versions['Final Optimized']['success_rate']
    improvement = current_rate - best_previous
    
    print(f"\n📈 OVERALL IMPROVEMENT:")
    print(f"   Best Previous: {best_previous}% (Enhanced Scraper)")
    print(f"   Current: {current_rate}% (Final Optimized)")
    print(f"   Improvement: {improvement:+.1f} percentage points")
    
    if improvement > 0:
        print(f"   Status: ✅ IMPROVED")
    elif improvement == 0:
        print(f"   Status: ➖ MAINTAINED")
    else:
        print(f"   Status: ❌ DECLINED")

def main():
    """Main test execution"""
    print("Loading restaurant data...")
    restaurants = load_restaurant_data()
    
    if not restaurants:
        print("No restaurant data available. Please ensure restaurant_data.json exists.")
        return
    
    print(f"Loaded {len(restaurants)} restaurants")
    
    # Test with sample size of 15 (balanced for thorough testing)
    sample_size = 15
    
    print(f"\nTesting Final Optimized Menu Scraper with {sample_size} restaurants...")
    results = run_final_optimized_test(restaurants, sample_size)
    
    # Save results
    filename = f'final_optimized_test_results_n{sample_size}.json'
    save_results(results, filename)
    
    # Print summary
    print_final_optimized_summary(results)
    
    # Compare with all previous versions
    compare_all_scraper_versions(results)
    
    print(f"\n💾 Detailed results saved to: {filename}")
    print("\n🎯 FINAL ASSESSMENT:")
    if results['summary']['success_rate'] >= 50.0:
        print("   🎉 TARGET ACHIEVED! Final optimized scraper meets requirements")
        print("   ✅ Ready for production deployment")
        print("   🚀 Consider scaling to larger datasets")
    else:
        gap = 50.0 - results['summary']['success_rate']
        print(f"   ⚠️  Still {gap:.1f}% below target")
        print("   🔧 Additional optimization strategies needed")
        print("   📊 Analyze successful cases for patterns")
    
    print("\n🔄 NEXT STEPS:")
    print("   📈 Monitor performance on diverse restaurant types")
    print("   🛠️  Implement continuous improvement based on feedback")
    print("   🎯 Consider domain-specific optimizations")

if __name__ == "__main__":
    main()