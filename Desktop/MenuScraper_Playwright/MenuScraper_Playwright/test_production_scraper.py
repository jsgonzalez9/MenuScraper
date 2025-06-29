#!/usr/bin/env python3
"""
Production Menu Scraper Test Suite
Comprehensive evaluation of the production scraper performance
Target: Achieve 50%+ success rate with robust metrics
"""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

from production_menu_scraper import ProductionMenuScraper

def load_restaurant_data() -> List[Dict[str, str]]:
    """Load restaurant data from JSON file"""
    try:
        with open('restaurant_data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Handle both flat list and nested dictionary structures
        if isinstance(data, list):
            restaurants = data
        elif isinstance(data, dict) and 'restaurants' in data:
            restaurants = data['restaurants']
        else:
            raise ValueError("Invalid restaurant data format")
            
        print(f"📊 Loaded {len(restaurants)} restaurants for testing")
        return restaurants
        
    except FileNotFoundError:
        print("❌ restaurant_data.json not found")
        return []
    except Exception as e:
        print(f"❌ Error loading restaurant data: {e}")
        return []

async def test_production_scraper(sample_size: int = 20) -> Dict[str, Any]:
    """Test the production scraper with comprehensive metrics"""
    print(f"\n🚀 STARTING PRODUCTION SCRAPER TEST")
    print(f"📊 Sample size: {sample_size}")
    print(f"🎯 Target success rate: 50%+")
    print("=" * 80)
    
    # Load restaurant data
    restaurants = load_restaurant_data()
    if not restaurants:
        print("❌ No restaurant data available for testing")
        return {}
    
    # Limit sample size
    test_restaurants = restaurants[:sample_size]
    
    # Initialize scraper
    scraper = ProductionMenuScraper(headless=True, timeout=30000)
    
    # Test results storage
    results = {
        'scraper_version': 'Production v1.0',
        'test_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'sample_size': len(test_restaurants),
        'success_rate': 0.0,
        'successful_scrapes': 0,
        'total_items_extracted': 0,
        'avg_items_per_success': 0,
        'avg_processing_time': 0,
        'extraction_method_distribution': {},
        'allergen_detections': {},
        'price_coverage_stats': {
            'avg_coverage': 0,
            'min_coverage': 0,
            'max_coverage': 0
        },
        'quality_metrics': {
            'items_with_prices': 0,
            'items_with_descriptions': 0,
            'items_with_allergens': 0,
            'avg_item_name_length': 0
        },
        'performance_metrics': {
            'fastest_scrape': float('inf'),
            'slowest_scrape': 0,
            'total_test_time': 0
        },
        'error_analysis': {},
        'detailed_results': []
    }
    
    start_time = time.time()
    
    try:
        # Setup browser
        if not await scraper.setup_browser():
            print("❌ Failed to setup browser")
            return results
        
        print(f"\n🔄 Testing {len(test_restaurants)} restaurants...\n")
        
        # Test each restaurant
        for i, restaurant in enumerate(test_restaurants, 1):
            restaurant_name = restaurant.get('name', f'Restaurant {i}')
            url = restaurant.get('url', '')
            
            print(f"[{i:2d}/{len(test_restaurants)}] 🍽️  Testing: {restaurant_name}")
            print(f"           🌐 URL: {url}")
            
            # Extract menu items
            result = await scraper.extract_menu_items(url)
            
            # Process results
            processing_time = result.get('processing_time', 0)
            success = result.get('success', False)
            total_items = result.get('total_items', 0)
            extraction_method = result.get('extraction_method', 'unknown')
            
            # Update metrics
            if success:
                results['successful_scrapes'] += 1
                results['total_items_extracted'] += total_items
                
                # Track extraction methods
                method_key = extraction_method.split(':')[0] if ':' in extraction_method else extraction_method
                results['extraction_method_distribution'][method_key] = \
                    results['extraction_method_distribution'].get(method_key, 0) + 1
                
                # Allergen analysis
                allergen_summary = result.get('allergen_summary', {})
                for allergen, count in allergen_summary.items():
                    results['allergen_detections'][allergen] = \
                        results['allergen_detections'].get(allergen, 0) + count
                
                # Quality metrics
                items = result.get('items', [])
                for item in items:
                    if item.get('price'):
                        results['quality_metrics']['items_with_prices'] += 1
                    if item.get('description') and len(item['description']) > 5:
                        results['quality_metrics']['items_with_descriptions'] += 1
                    if item.get('allergens'):
                        results['quality_metrics']['items_with_allergens'] += 1
                    
                    name_length = len(item.get('name', ''))
                    if name_length > 0:
                        current_avg = results['quality_metrics']['avg_item_name_length']
                        total_items_so_far = results['total_items_extracted']
                        results['quality_metrics']['avg_item_name_length'] = \
                            (current_avg * (total_items_so_far - 1) + name_length) / total_items_so_far
                
                print(f"           ✅ Success: {total_items} items extracted")
                print(f"           ⏱️  Time: {processing_time}s")
                print(f"           🔧 Method: {extraction_method}")
                
            else:
                error = result.get('error', 'Unknown error')
                results['error_analysis'][error] = results['error_analysis'].get(error, 0) + 1
                print(f"           ❌ Failed: {error}")
                print(f"           ⏱️  Time: {processing_time}s")
            
            # Performance tracking
            results['performance_metrics']['fastest_scrape'] = min(
                results['performance_metrics']['fastest_scrape'], processing_time
            )
            results['performance_metrics']['slowest_scrape'] = max(
                results['performance_metrics']['slowest_scrape'], processing_time
            )
            
            # Store detailed result
            detailed_result = {
                'restaurant_name': restaurant_name,
                'url': url,
                'scraping_success': success,
                'total_items': total_items,
                'processing_time': processing_time,
                'extraction_method': extraction_method,
                'price_coverage': result.get('price_coverage', 0),
                'allergen_summary': result.get('allergen_summary', {}),
                'error': result.get('error')
            }
            results['detailed_results'].append(detailed_result)
            
            print()  # Empty line for readability
            
            # Small delay between requests
            await asyncio.sleep(1)
    
    finally:
        await scraper.cleanup()
    
    # Calculate final metrics
    total_test_time = time.time() - start_time
    results['performance_metrics']['total_test_time'] = round(total_test_time, 2)
    
    if results['successful_scrapes'] > 0:
        results['success_rate'] = round(
            (results['successful_scrapes'] / len(test_restaurants)) * 100, 1
        )
        results['avg_items_per_success'] = round(
            results['total_items_extracted'] / results['successful_scrapes'], 1
        )
    
    # Calculate average processing time
    if results['detailed_results']:
        total_processing_time = sum(r['processing_time'] for r in results['detailed_results'])
        results['avg_processing_time'] = round(
            total_processing_time / len(results['detailed_results']), 2
        )
    
    # Price coverage statistics
    price_coverages = [r['price_coverage'] for r in results['detailed_results'] if r['scraping_success']]
    if price_coverages:
        results['price_coverage_stats'] = {
            'avg_coverage': round(sum(price_coverages) / len(price_coverages), 1),
            'min_coverage': min(price_coverages),
            'max_coverage': max(price_coverages)
        }
    
    # Fix infinite value for fastest scrape
    if results['performance_metrics']['fastest_scrape'] == float('inf'):
        results['performance_metrics']['fastest_scrape'] = 0
    
    return results

def save_results(results: Dict[str, Any], filename: str = None) -> str:
    """Save test results to JSON file"""
    if not filename:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'production_test_results_{timestamp}.json'
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"📁 Results saved to: {filename}")
        return filename
    except Exception as e:
        print(f"❌ Failed to save results: {e}")
        return ""

def print_comprehensive_summary(results: Dict[str, Any]):
    """Print comprehensive test summary"""
    print("\n" + "=" * 80)
    print("🎯 PRODUCTION SCRAPER TEST RESULTS SUMMARY")
    print("=" * 80)
    
    # Basic metrics
    print(f"\n📊 CORE METRICS:")
    print(f"   🎯 Success Rate: {results['success_rate']}% ({results['successful_scrapes']}/{results['sample_size']})")
    print(f"   📋 Total Items: {results['total_items_extracted']}")
    print(f"   📈 Avg Items/Success: {results['avg_items_per_success']}")
    print(f"   ⏱️  Avg Processing Time: {results['avg_processing_time']}s")
    
    # Performance assessment
    target_success_rate = 50.0
    if results['success_rate'] >= target_success_rate:
        print(f"   ✅ TARGET ACHIEVED! ({results['success_rate']}% >= {target_success_rate}%)")
    else:
        gap = target_success_rate - results['success_rate']
        print(f"   ⚠️  Target missed by {gap}% ({results['success_rate']}% < {target_success_rate}%)")
    
    # Extraction methods
    if results['extraction_method_distribution']:
        print(f"\n🔧 EXTRACTION METHODS:")
        for method, count in results['extraction_method_distribution'].items():
            percentage = (count / results['successful_scrapes']) * 100
            print(f"   • {method}: {count} uses ({percentage:.1f}%)")
    
    # Quality metrics
    print(f"\n📈 QUALITY METRICS:")
    total_items = results['total_items_extracted']
    if total_items > 0:
        price_pct = (results['quality_metrics']['items_with_prices'] / total_items) * 100
        desc_pct = (results['quality_metrics']['items_with_descriptions'] / total_items) * 100
        allergen_pct = (results['quality_metrics']['items_with_allergens'] / total_items) * 100
        
        print(f"   💰 Items with prices: {results['quality_metrics']['items_with_prices']} ({price_pct:.1f}%)")
        print(f"   📝 Items with descriptions: {results['quality_metrics']['items_with_descriptions']} ({desc_pct:.1f}%)")
        print(f"   🚨 Items with allergens: {results['quality_metrics']['items_with_allergens']} ({allergen_pct:.1f}%)")
        print(f"   📏 Avg name length: {results['quality_metrics']['avg_item_name_length']:.1f} chars")
    
    # Price coverage
    if results['price_coverage_stats']['avg_coverage'] > 0:
        print(f"\n💰 PRICE COVERAGE:")
        print(f"   📊 Average: {results['price_coverage_stats']['avg_coverage']}%")
        print(f"   📉 Range: {results['price_coverage_stats']['min_coverage']}% - {results['price_coverage_stats']['max_coverage']}%")
    
    # Allergen detection
    if results['allergen_detections']:
        print(f"\n🚨 ALLERGEN DETECTIONS:")
        for allergen, count in sorted(results['allergen_detections'].items(), key=lambda x: x[1], reverse=True):
            print(f"   • {allergen}: {count} occurrences")
    
    # Performance metrics
    print(f"\n⚡ PERFORMANCE:")
    print(f"   🏃 Fastest scrape: {results['performance_metrics']['fastest_scrape']}s")
    print(f"   🐌 Slowest scrape: {results['performance_metrics']['slowest_scrape']}s")
    print(f"   🕐 Total test time: {results['performance_metrics']['total_test_time']}s")
    
    # Error analysis
    if results['error_analysis']:
        print(f"\n❌ ERROR ANALYSIS:")
        for error, count in sorted(results['error_analysis'].items(), key=lambda x: x[1], reverse=True):
            percentage = (count / results['sample_size']) * 100
            print(f"   • {error}: {count} occurrences ({percentage:.1f}%)")
    
    # Comparison with previous versions
    print(f"\n🔄 COMPARISON WITH PREVIOUS VERSIONS:")
    previous_results = {
        'Enhanced Scraper': 40.0,
        'Advanced Scraper': 30.0,
        'Improved Scraper': 25.0,
        'Final Optimized': 40.0,
        'ML Enhanced': 0.0,
        'Enhanced Allergen': 0.0
    }
    
    current_rate = results['success_rate']
    best_previous = max(previous_results.values())
    
    for version, rate in previous_results.items():
        print(f"   {version}: {rate}% success rate")
    
    print(f"   Production Scraper: {current_rate}% success rate")
    
    if current_rate > best_previous:
        improvement = current_rate - best_previous
        print(f"   🎉 NEW BEST! Improved by {improvement}% over previous best")
    elif current_rate == best_previous:
        print(f"   🤝 MATCHES best previous performance")
    else:
        decline = best_previous - current_rate
        print(f"   ⚠️  Production is {decline}% below best previous performance")
    
    # Recommendations
    print(f"\n🚀 NEXT STEPS:")
    if results['success_rate'] >= 50:
        print(f"   • 🎯 Target achieved! Consider production deployment")
        print(f"   • 📈 Focus on scaling and optimization")
        print(f"   • 🔍 Monitor performance in production")
    else:
        print(f"   • 🔍 Analyze failed cases for pattern identification")
        print(f"   • 🎯 Focus on improving extraction accuracy")
        print(f"   • 🤖 Consider advanced ML integration")
        print(f"   • 🔗 Investigate API partnerships")
    
    print(f"   • 📊 A/B test different strategies")
    print(f"   • 🚨 Enhance allergen detection coverage")
    print(f"   • 💰 Improve price extraction accuracy")
    
    print("\n" + "=" * 80)
    print("✅ Test completed successfully!")

async def main():
    """Main test execution"""
    # Run comprehensive test
    results = await test_production_scraper(sample_size=20)
    
    if results:
        # Print summary
        print_comprehensive_summary(results)
        
        # Save results
        filename = save_results(results, 'production_test_results_n20.json')
        print(f"📁 Detailed results saved to: {filename}")
    else:
        print("❌ Test failed to complete")

if __name__ == "__main__":
    asyncio.run(main())