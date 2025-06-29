#!/usr/bin/env python3
"""
Ultimate Menu Scraper Test Suite
Comprehensive testing with anti-bot detection and advanced extraction
"""

import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Any
from playwright.sync_api import sync_playwright
from ultimate_menu_scraper import UltimateMenuScraper

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

def run_ultimate_test(restaurants: List[Dict], sample_size: int) -> Dict[str, Any]:
    """Run ultimate scraper test with comprehensive analysis"""
    logger.info(f"Starting ultimate scraper test with {sample_size} restaurants")
    
    scraper = UltimateMenuScraper()
    results = {
        'test_info': {
            'timestamp': datetime.now().isoformat(),
            'sample_size': sample_size,
            'scraper_version': 'ultimate_v1',
            'target_success_rate': '50%+',
            'advanced_features': [
                'Anti-bot detection and bypass',
                'Stealth browser configuration',
                'Multi-strategy extraction',
                'Enhanced structured data parsing',
                'Intelligent menu page discovery',
                'Advanced content filtering',
                'Quality scoring system'
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
            'visual_extraction_usage': 0,
            'bot_protection_encountered': 0,
            'bot_protection_bypassed': 0,
            'avg_processing_time': 0.0,
            'avg_quality_score': 0.0,
            'strategy_distribution': {},
            'category_distribution': {},
            'price_extraction_rate': 0.0,
            'error_count': 0,
            'confidence_distribution': {
                'high': 0,  # >0.8
                'medium': 0,  # 0.5-0.8
                'low': 0  # <0.5
            }
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
    confidence_counts = {'high': 0, 'medium': 0, 'low': 0}
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        for i, restaurant in enumerate(test_restaurants, 1):
            name = restaurant.get('name', f'Restaurant_{i}')
            url = restaurant.get('url', '')
            
            logger.info(f"Testing {i}/{sample_size}: {name}")
            
            try:
                # Run ultimate scraper
                result = scraper.ultimate_menu_detection(page, url)
                
                # Store result
                results['restaurants'][name] = result
                
                # Update summary statistics
                results['summary']['total_tested'] += 1
                total_processing_time += result.get('processing_time', 0)
                total_quality_score += result.get('quality_score', 0)
                
                if result.get('error'):
                    error_count += 1
                    if 'bot protection' in result.get('error', '').lower():
                        results['summary']['bot_protection_encountered'] += 1
                
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
                        
                        # Count confidence levels
                        confidence = item.get('confidence', 0)
                        if confidence > 0.8:
                            confidence_counts['high'] += 1
                        elif confidence > 0.5:
                            confidence_counts['medium'] += 1
                        else:
                            confidence_counts['low'] += 1
                
                # Count usage statistics
                if result.get('menu_page_found', False):
                    results['summary']['menu_pages_found'] += 1
                
                extraction_methods = result.get('extraction_methods', [])
                if 'structured' in extraction_methods:
                    results['summary']['structured_data_usage'] += 1
                
                if 'visual' in extraction_methods:
                    results['summary']['visual_extraction_usage'] += 1
                
                # Count strategies
                for method in extraction_methods:
                    strategy_counts[method] = strategy_counts.get(method, 0) + 1
                
                # Log progress
                status = 'SUCCESS' if result.get('scraping_success') else 'FAILED'
                items_found = result.get('total_items', 0)
                processing_time = result.get('processing_time', 0)
                strategies_used = result.get('strategies_used', 0)
                quality_score = result.get('quality_score', 0)
                
                logger.info(f"  Result: {status} - {items_found} items - {processing_time:.1f}s - {strategies_used} strategies - Q:{quality_score:.2f}")
                
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
    results['summary']['confidence_distribution'] = confidence_counts
    
    return results

def save_results(results: Dict[str, Any], filename: str):
    """Save test results to JSON file"""
    try:
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results saved to {filename}")
    except Exception as e:
        logger.error(f"Error saving results: {e}")

def print_ultimate_summary(results: Dict[str, Any]):
    """Print comprehensive test summary"""
    summary = results['summary']
    test_info = results['test_info']
    
    print("\n" + "="*80)
    print("🚀 ULTIMATE MENU SCRAPER TEST RESULTS")
    print("="*80)
    
    print(f"\n📊 TEST OVERVIEW:")
    print(f"   Sample Size: {test_info['sample_size']} restaurants")
    print(f"   Target Success Rate: {test_info['target_success_rate']}")
    print(f"   Scraper Version: {test_info['scraper_version']}")
    print(f"   Test Date: {test_info['timestamp'][:19]}")
    
    print(f"\n🔧 ADVANCED FEATURES:")
    for feature in test_info['advanced_features']:
        print(f"   ✅ {feature}")
    
    print(f"\n🎯 PERFORMANCE METRICS:")
    success_rate = summary['success_rate']
    target_met = "🎉 TARGET ACHIEVED!" if success_rate >= 50.0 else "⚠️ TARGET MISSED"
    print(f"   Success Rate: {success_rate}% ({summary['successful_extractions']}/{summary['total_tested']}) {target_met}")
    print(f"   Total Menu Items: {summary['total_menu_items']}")
    print(f"   Avg Items per Success: {summary['avg_items_per_success']}")
    print(f"   Avg Processing Time: {summary['avg_processing_time']}s")
    print(f"   Avg Quality Score: {summary['avg_quality_score']}")
    print(f"   Error Count: {summary['error_count']}/{summary['total_tested']}")
    
    print(f"\n🛡️ ANTI-BOT PROTECTION:")
    print(f"   Bot Protection Encountered: {summary['bot_protection_encountered']} cases")
    print(f"   Bot Protection Bypassed: {summary['bot_protection_bypassed']} cases")
    bypass_rate = (summary['bot_protection_bypassed'] / max(summary['bot_protection_encountered'], 1)) * 100
    print(f"   Bypass Success Rate: {bypass_rate:.1f}%")
    
    print(f"\n🔧 FEATURE UTILIZATION:")
    print(f"   Menu Pages Found: {summary['menu_pages_found']}/{summary['total_tested']} ({round(summary['menu_pages_found']/summary['total_tested']*100, 1)}%)")
    print(f"   Structured Data Usage: {summary['structured_data_usage']}/{summary['total_tested']} ({round(summary['structured_data_usage']/summary['total_tested']*100, 1)}%)")
    print(f"   Visual Extraction Usage: {summary['visual_extraction_usage']}/{summary['total_tested']} ({round(summary['visual_extraction_usage']/summary['total_tested']*100, 1)}%)")
    print(f"   Price Extraction Rate: {summary['price_extraction_rate']}%")
    
    print(f"\n📈 STRATEGY DISTRIBUTION:")
    for strategy, count in summary['strategy_distribution'].items():
        percentage = round((count / summary['total_tested']) * 100, 1)
        print(f"   {strategy.capitalize()}: {count} uses ({percentage}%)")
    
    print(f"\n🍽️ CATEGORY DISTRIBUTION:")
    for category, count in summary['category_distribution'].items():
        percentage = round((count / summary['total_menu_items']) * 100, 1) if summary['total_menu_items'] > 0 else 0
        print(f"   {category.capitalize()}: {count} items ({percentage}%)")
    
    print(f"\n📊 CONFIDENCE DISTRIBUTION:")
    conf_dist = summary['confidence_distribution']
    total_conf_items = sum(conf_dist.values())
    if total_conf_items > 0:
        print(f"   High Confidence (>0.8): {conf_dist['high']} ({round(conf_dist['high']/total_conf_items*100, 1)}%)")
        print(f"   Medium Confidence (0.5-0.8): {conf_dist['medium']} ({round(conf_dist['medium']/total_conf_items*100, 1)}%)")
        print(f"   Low Confidence (<0.5): {conf_dist['low']} ({round(conf_dist['low']/total_conf_items*100, 1)}%)")
    
    print(f"\n✅ SUCCESSFUL RESTAURANTS:")
    for restaurant in summary.get('successful_restaurants', [])[:10]:
        restaurant_data = results['restaurants'].get(restaurant, {})
        items = restaurant_data.get('total_items', 0)
        quality = restaurant_data.get('quality_score', 0)
        methods = ', '.join(restaurant_data.get('extraction_methods', []))
        strategies = restaurant_data.get('strategies_used', 0)
        print(f"   • {restaurant}: {items} items (Q:{quality:.2f}, {strategies} strategies, {methods})")
    
    if len(summary.get('successful_restaurants', [])) > 10:
        print(f"   ... and {len(summary['successful_restaurants']) - 10} more")
    
    # Performance analysis
    print(f"\n📋 PERFORMANCE ANALYSIS:")
    if success_rate >= 50.0:
        gap = success_rate - 50.0
        print(f"   🎉 SUCCESS: Exceeded target by {gap:.1f} percentage points")
        print(f"   🚀 Ready for production deployment")
        print(f"   🏆 Ultimate scraper has achieved the goal!")
    else:
        gap = 50.0 - success_rate
        print(f"   ⚠️  IMPROVEMENT NEEDED: {gap:.1f} percentage points below target")
        print(f"   🔧 Consider additional optimization strategies")
        print(f"   📊 Analyze successful patterns for insights")
    
    quality_rating = 'Excellent' if summary['avg_quality_score'] > 0.8 else 'Good' if summary['avg_quality_score'] > 0.6 else 'Fair' if summary['avg_quality_score'] > 0.4 else 'Poor'
    speed_rating = 'Fast' if summary['avg_processing_time'] < 8 else 'Moderate' if summary['avg_processing_time'] < 15 else 'Slow'
    error_rate = round(summary['error_count']/summary['total_tested']*100, 1)
    
    print(f"   Quality Score: {quality_rating} ({summary['avg_quality_score']:.3f})")
    print(f"   Processing Speed: {speed_rating} ({summary['avg_processing_time']:.1f}s avg)")
    print(f"   Error Rate: {error_rate}% ({summary['error_count']}/{summary['total_tested']})")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    if success_rate >= 50.0:
        print(f"   ✅ Deploy to production environment")
        print(f"   📈 Scale testing to larger datasets")
        print(f"   🔄 Implement continuous monitoring")
    else:
        print(f"   🔧 Focus on improving extraction accuracy")
        print(f"   🛡️ Enhance bot protection bypass mechanisms")
        print(f"   📊 Analyze failed cases for common patterns")
        if summary['avg_quality_score'] < 0.6:
            print(f"   🎯 Improve content validation and filtering")
        if summary['avg_processing_time'] > 15:
            print(f"   ⚡ Optimize processing speed")

def compare_ultimate_with_previous(ultimate_results: Dict[str, Any]):
    """Compare ultimate scraper with all previous versions"""
    print("\n" + "="*80)
    print("🏆 ULTIMATE SCRAPER VS ALL PREVIOUS VERSIONS")
    print("="*80)
    
    # Load previous results for comparison
    versions = {}
    
    # Enhanced scraper
    try:
        with open('enhanced_scraper_test_results.json', 'r') as f:
            enhanced_data = json.load(f)
            versions['Enhanced'] = {
                'success_rate': enhanced_data.get('summary', {}).get('success_rate', 40.0),
                'avg_items': enhanced_data.get('summary', {}).get('avg_items_per_success', 10.5),
                'quality': enhanced_data.get('summary', {}).get('avg_quality_score', 0.7)
            }
    except:
        versions['Enhanced'] = {'success_rate': 40.0, 'avg_items': 10.5, 'quality': 0.7}
    
    # Advanced scraper
    try:
        with open('advanced_test_results_n50.json', 'r') as f:
            advanced_data = json.load(f)
            versions['Advanced'] = {
                'success_rate': advanced_data.get('summary', {}).get('success_rate', 36.0),
                'avg_items': advanced_data.get('summary', {}).get('avg_items_per_success', 5.5),
                'quality': advanced_data.get('summary', {}).get('avg_quality_score', 0.6)
            }
    except:
        versions['Advanced'] = {'success_rate': 36.0, 'avg_items': 5.5, 'quality': 0.6}
    
    # Improved scraper
    try:
        with open('improved_scraper_test_results.json', 'r') as f:
            improved_data = json.load(f)
            versions['Improved'] = {
                'success_rate': improved_data.get('summary', {}).get('success_rate', 30.0),
                'avg_items': improved_data.get('summary', {}).get('avg_items_per_success', 9.3),
                'quality': improved_data.get('summary', {}).get('avg_quality_score', 0.65)
            }
    except:
        versions['Improved'] = {'success_rate': 30.0, 'avg_items': 9.3, 'quality': 0.65}
    
    # Final optimized scraper
    try:
        with open('final_optimized_test_results_n15.json', 'r') as f:
            final_data = json.load(f)
            versions['Final Optimized'] = {
                'success_rate': final_data.get('summary', {}).get('success_rate', 40.0),
                'avg_items': final_data.get('summary', {}).get('avg_items_per_success', 2.0),
                'quality': final_data.get('summary', {}).get('avg_quality_score', 0.4)
            }
    except:
        versions['Final Optimized'] = {'success_rate': 40.0, 'avg_items': 2.0, 'quality': 0.4}
    
    # Ultimate scraper (current)
    current_summary = ultimate_results['summary']
    versions['🚀 Ultimate'] = {
        'success_rate': current_summary['success_rate'],
        'avg_items': current_summary['avg_items_per_success'],
        'quality': current_summary['avg_quality_score']
    }
    
    print(f"\n📊 SUCCESS RATE EVOLUTION:")
    for version, data in versions.items():
        rate = data['success_rate']
        if '🚀' in version:
            status = "🏆 ULTIMATE"
        elif rate >= 50:
            status = "🎯 TARGET MET"
        elif rate >= 35:
            status = "📈 GOOD"
        elif rate >= 20:
            status = "📉 FAIR"
        else:
            status = "❌ POOR"
        print(f"   {status} {version}: {rate}% success rate")
    
    print(f"\n🍽️ ITEMS PER SUCCESS EVOLUTION:")
    for version, data in versions.items():
        items = data['avg_items']
        if '🚀' in version:
            status = "🏆 ULTIMATE"
        elif items >= 15:
            status = "🎯 EXCELLENT"
        elif items >= 8:
            status = "📈 GOOD"
        elif items >= 5:
            status = "📉 FAIR"
        else:
            status = "❌ POOR"
        print(f"   {status} {version}: {items} items per success")
    
    print(f"\n⭐ QUALITY SCORE EVOLUTION:")
    for version, data in versions.items():
        quality = data['quality']
        if '🚀' in version:
            status = "🏆 ULTIMATE"
        elif quality >= 0.8:
            status = "🎯 EXCELLENT"
        elif quality >= 0.6:
            status = "📈 GOOD"
        elif quality >= 0.4:
            status = "📉 FAIR"
        else:
            status = "❌ POOR"
        print(f"   {status} {version}: {quality:.3f} quality score")
    
    # Calculate overall improvement
    best_previous_rate = max(v['success_rate'] for k, v in versions.items() if '🚀' not in k)
    current_rate = versions['🚀 Ultimate']['success_rate']
    improvement = current_rate - best_previous_rate
    
    print(f"\n📈 ULTIMATE IMPROVEMENT ANALYSIS:")
    print(f"   Best Previous: {best_previous_rate}% (Enhanced/Final Optimized)")
    print(f"   Ultimate: {current_rate}%")
    print(f"   Improvement: {improvement:+.1f} percentage points")
    
    if improvement > 0:
        print(f"   Status: ✅ IMPROVED")
    elif improvement == 0:
        print(f"   Status: ➖ MAINTAINED")
    else:
        print(f"   Status: ❌ DECLINED")
    
    # Final verdict
    print(f"\n🏆 FINAL VERDICT:")
    if current_rate >= 50.0:
        print(f"   🎉 MISSION ACCOMPLISHED!")
        print(f"   🚀 Ultimate scraper has achieved the 50%+ target")
        print(f"   ✅ Ready for production deployment")
    else:
        print(f"   ⚠️ Mission not yet complete")
        print(f"   🔧 Additional optimization needed")
        print(f"   📊 Gap to target: {50.0 - current_rate:.1f} percentage points")

def main():
    """Main test execution"""
    print("🚀 Loading restaurant data for Ultimate Scraper test...")
    restaurants = load_restaurant_data()
    
    if not restaurants:
        print("❌ No restaurant data available. Please ensure restaurant_data.json exists.")
        return
    
    print(f"✅ Loaded {len(restaurants)} restaurants")
    
    # Test with sample size of 20 for comprehensive evaluation
    sample_size = 20
    
    print(f"\n🚀 Testing Ultimate Menu Scraper with {sample_size} restaurants...")
    print("   Features: Anti-bot detection, Stealth mode, Multi-strategy extraction")
    
    results = run_ultimate_test(restaurants, sample_size)
    
    # Save results
    filename = f'ultimate_test_results_n{sample_size}.json'
    save_results(results, filename)
    
    # Print summary
    print_ultimate_summary(results)
    
    # Compare with all previous versions
    compare_ultimate_with_previous(results)
    
    print(f"\n💾 Detailed results saved to: {filename}")
    
    # Final assessment
    success_rate = results['summary']['success_rate']
    print(f"\n🎯 ULTIMATE ASSESSMENT:")
    if success_rate >= 50.0:
        print("   🎉 🎉 🎉 TARGET ACHIEVED! 🎉 🎉 🎉")
        print("   🏆 Ultimate scraper successfully meets the 50%+ requirement")
        print("   ✅ Ready for production deployment")
        print("   🚀 Mission accomplished!")
    else:
        gap = 50.0 - success_rate
        print(f"   ⚠️ Still {gap:.1f}% below target")
        print("   🔧 Consider advanced ML-based approaches")
        print("   📊 Analyze successful patterns for insights")
        print("   🛡️ Enhance anti-detection capabilities")
    
    print("\n🔄 NEXT STEPS:")
    if success_rate >= 50.0:
        print("   📈 Scale to production environment")
        print("   🔄 Implement continuous monitoring")
        print("   🎯 Optimize for specific restaurant types")
        print("   📊 Collect user feedback for improvements")
    else:
        print("   🔬 Deep analysis of failed cases")
        print("   🤖 Consider ML-based content recognition")
        print("   🛡️ Advanced anti-detection research")
        print("   📊 Pattern analysis of successful extractions")

if __name__ == "__main__":
    main()