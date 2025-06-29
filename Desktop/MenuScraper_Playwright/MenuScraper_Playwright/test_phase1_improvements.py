#!/usr/bin/env python3
"""
Test script for Phase 1 Menu Scraper Improvements

This script demonstrates the enhanced scraper with:
1. Enhanced Yelp menu detection with comprehensive price extraction
2. Dynamic content handling with improved scrolling for Yelp pages
3. Restaurant website discovery using Google search
4. Fallback logic to scrape official websites when primary URL yields insufficient results

Features tested:
- Enhanced price extraction patterns
- Yelp-specific content handling
- Google search for official restaurant websites
- Fallback scraping logic
- Combined results from multiple sources
"""

import asyncio
import json
import time
from datetime import datetime
from enhanced_dynamic_scraper import EnhancedDynamicScraper

# Test restaurants with various scenarios
TEST_RESTAURANTS = [
    {
        'name': 'The Cheesecake Factory',
        'url': 'https://www.yelp.com/biz/the-cheesecake-factory-beverly-hills',
        'description': 'Popular chain restaurant - should have official website fallback'
    },
    {
        'name': 'Guelaguetza',
        'url': 'https://www.yelp.com/biz/guelaguetza-los-angeles-2',
        'description': 'Local LA restaurant - test Yelp extraction and website discovery'
    },
    {
        'name': 'Republique',
        'url': 'https://www.yelp.com/biz/republique-los-angeles',
        'description': 'Upscale restaurant - should have comprehensive menu on official site'
    },
    {
        'name': 'Night + Market',
        'url': 'https://www.yelp.com/biz/night-market-west-hollywood',
        'description': 'Thai restaurant - test enhanced price detection'
    },
    {
        'name': 'Bestia',
        'url': 'https://www.yelp.com/biz/bestia-los-angeles',
        'description': 'Popular Italian restaurant - comprehensive test case'
    }
]

async def test_single_restaurant(scraper: EnhancedDynamicScraper, restaurant: dict) -> dict:
    """Test scraping a single restaurant with detailed logging"""
    print(f"\n{'='*80}")
    print(f"🍽️  Testing: {restaurant['name']}")
    print(f"📍 URL: {restaurant['url']}")
    print(f"📝 Description: {restaurant['description']}")
    print(f"{'='*80}")
    
    start_time = time.time()
    
    try:
        # Use the new extract_menu_items method with fallback logic
        result = await scraper.extract_menu_items(
            url=restaurant['url'],
            restaurant_name=restaurant['name']
        )
        
        processing_time = time.time() - start_time
        
        # Enhanced result logging
        print(f"\n📊 RESULTS FOR {restaurant['name']}:")
        print(f"   ✅ Success: {result.get('scraping_success', False)}")
        print(f"   📈 Total Items: {result.get('total_items', 0)}")
        print(f"   ⏱️  Processing Time: {processing_time:.2f}s")
        print(f"   🔧 Extraction Method: {result.get('extraction_method', 'unknown')}")
        print(f"   🌐 Primary URL: {result.get('primary_url', 'N/A')}")
        print(f"   🔄 Fallback URL: {result.get('fallback_url', 'None')}")
        
        if result.get('error'):
            print(f"   ❌ Error: {result['error']}")
        
        # Sample items preview
        items = result.get('items', [])
        if items:
            print(f"\n📋 SAMPLE MENU ITEMS (showing first 3):")
            for i, item in enumerate(items[:3]):
                print(f"   {i+1}. {item.get('name', 'Unknown')}")
                if item.get('price'):
                    print(f"      💰 Price: ${item['price']:.2f}")
                if item.get('description'):
                    print(f"      📝 Description: {item['description'][:100]}...")
                print(f"      🏷️  Category: {item.get('category', 'other')}")
                print(f"      🔍 Method: {item.get('extraction_method', 'unknown')}")
                print()
        
        # Enhanced analytics
        if items:
            prices = [item['price'] for item in items if item.get('price')]
            descriptions = [item for item in items if item.get('description')]
            
            print(f"📈 ANALYTICS:")
            print(f"   💰 Items with prices: {len(prices)}/{len(items)} ({len(prices)/len(items)*100:.1f}%)")
            print(f"   📝 Items with descriptions: {len(descriptions)}/{len(items)} ({len(descriptions)/len(items)*100:.1f}%)")
            
            if prices:
                print(f"   💵 Price range: ${min(prices):.2f} - ${max(prices):.2f}")
                print(f"   💵 Average price: ${sum(prices)/len(prices):.2f}")
            
            # Category breakdown
            categories = {}
            for item in items:
                cat = item.get('category', 'other')
                categories[cat] = categories.get(cat, 0) + 1
            
            print(f"   🏷️  Categories: {dict(sorted(categories.items(), key=lambda x: x[1], reverse=True))}")
        
        return {
            'restaurant': restaurant['name'],
            'success': result.get('scraping_success', False),
            'total_items': result.get('total_items', 0),
            'processing_time': processing_time,
            'extraction_method': result.get('extraction_method', 'unknown'),
            'has_fallback': result.get('fallback_url') is not None,
            'error': result.get('error'),
            'price_coverage': len([item for item in items if item.get('price')]) / len(items) * 100 if items else 0,
            'description_coverage': len([item for item in items if item.get('description')]) / len(items) * 100 if items else 0
        }
        
    except Exception as e:
        print(f"❌ Test failed for {restaurant['name']}: {str(e)}")
        return {
            'restaurant': restaurant['name'],
            'success': False,
            'total_items': 0,
            'processing_time': time.time() - start_time,
            'extraction_method': 'error',
            'has_fallback': False,
            'error': str(e),
            'price_coverage': 0,
            'description_coverage': 0
        }

async def run_phase1_tests():
    """Run comprehensive Phase 1 improvement tests"""
    print("🚀 Starting Phase 1 Menu Scraper Improvement Tests")
    print(f"📅 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🧪 Testing {len(TEST_RESTAURANTS)} restaurants")
    
    # Initialize scraper
    scraper = EnhancedDynamicScraper(headless=True, timeout=45000)
    
    if not await scraper.setup_browser():
        print("❌ Failed to setup browser")
        return
    
    print("✅ Browser setup successful")
    
    # Test each restaurant
    results = []
    total_start_time = time.time()
    
    for i, restaurant in enumerate(TEST_RESTAURANTS, 1):
        print(f"\n🔄 Progress: {i}/{len(TEST_RESTAURANTS)}")
        result = await test_single_restaurant(scraper, restaurant)
        results.append(result)
        
        # Brief pause between tests
        await asyncio.sleep(2)
    
    total_time = time.time() - total_start_time
    
    # Comprehensive summary
    print(f"\n{'='*100}")
    print(f"📊 PHASE 1 IMPROVEMENT TEST SUMMARY")
    print(f"{'='*100}")
    
    successful_tests = [r for r in results if r['success']]
    failed_tests = [r for r in results if not r['success']]
    fallback_used = [r for r in results if r['has_fallback']]
    
    print(f"\n🎯 OVERALL PERFORMANCE:")
    print(f"   ✅ Successful extractions: {len(successful_tests)}/{len(results)} ({len(successful_tests)/len(results)*100:.1f}%)")
    print(f"   ❌ Failed extractions: {len(failed_tests)}/{len(results)} ({len(failed_tests)/len(results)*100:.1f}%)")
    print(f"   🔄 Fallback websites used: {len(fallback_used)}/{len(results)} ({len(fallback_used)/len(results)*100:.1f}%)")
    print(f"   ⏱️  Total processing time: {total_time:.2f}s")
    print(f"   ⏱️  Average time per restaurant: {total_time/len(results):.2f}s")
    
    if successful_tests:
        total_items = sum(r['total_items'] for r in successful_tests)
        avg_price_coverage = sum(r['price_coverage'] for r in successful_tests) / len(successful_tests)
        avg_desc_coverage = sum(r['description_coverage'] for r in successful_tests) / len(successful_tests)
        
        print(f"\n📈 EXTRACTION QUALITY:")
        print(f"   📋 Total menu items extracted: {total_items}")
        print(f"   📋 Average items per restaurant: {total_items/len(successful_tests):.1f}")
        print(f"   💰 Average price coverage: {avg_price_coverage:.1f}%")
        print(f"   📝 Average description coverage: {avg_desc_coverage:.1f}%")
    
    # Method breakdown
    methods = {}
    for result in successful_tests:
        method = result['extraction_method']
        methods[method] = methods.get(method, 0) + 1
    
    if methods:
        print(f"\n🔧 EXTRACTION METHODS USED:")
        for method, count in sorted(methods.items(), key=lambda x: x[1], reverse=True):
            print(f"   {method}: {count} restaurants ({count/len(successful_tests)*100:.1f}%)")
    
    # Individual results table
    print(f"\n📋 DETAILED RESULTS:")
    print(f"{'Restaurant':<25} {'Success':<8} {'Items':<6} {'Time':<6} {'Method':<20} {'Fallback':<8}")
    print(f"{'-'*80}")
    
    for result in results:
        fallback_indicator = "Yes" if result['has_fallback'] else "No"
        success_indicator = "✅" if result['success'] else "❌"
        
        print(f"{result['restaurant'][:24]:<25} {success_indicator:<8} {result['total_items']:<6} "
              f"{result['processing_time']:.1f}s{'':<2} {result['extraction_method'][:19]:<20} {fallback_indicator:<8}")
    
    # Error analysis
    if failed_tests:
        print(f"\n❌ ERROR ANALYSIS:")
        error_types = {}
        for result in failed_tests:
            error = result.get('error', 'Unknown error')
            error_types[error] = error_types.get(error, 0) + 1
        
        for error, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
            print(f"   {error}: {count} occurrences")
    
    # Save detailed results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_file = f'phase1_test_results_{timestamp}.json'
    
    detailed_results = {
        'test_info': {
            'timestamp': datetime.now().isoformat(),
            'total_restaurants': len(TEST_RESTAURANTS),
            'successful_extractions': len(successful_tests),
            'failed_extractions': len(failed_tests),
            'fallback_usage': len(fallback_used),
            'total_processing_time': total_time,
            'average_processing_time': total_time / len(results)
        },
        'performance_metrics': {
            'success_rate': len(successful_tests) / len(results) * 100,
            'fallback_usage_rate': len(fallback_used) / len(results) * 100,
            'total_items_extracted': sum(r['total_items'] for r in successful_tests),
            'average_items_per_restaurant': sum(r['total_items'] for r in successful_tests) / len(successful_tests) if successful_tests else 0,
            'average_price_coverage': sum(r['price_coverage'] for r in successful_tests) / len(successful_tests) if successful_tests else 0,
            'average_description_coverage': sum(r['description_coverage'] for r in successful_tests) / len(successful_tests) if successful_tests else 0
        },
        'extraction_methods': methods,
        'individual_results': results,
        'test_restaurants': TEST_RESTAURANTS
    }
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(detailed_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Detailed results saved to: {results_file}")
    
    # Cleanup
    await scraper.cleanup()
    print(f"\n✅ Phase 1 improvement tests completed successfully!")
    print(f"📊 Key improvements demonstrated:")
    print(f"   🔍 Enhanced Yelp menu detection with comprehensive price extraction")
    print(f"   🌐 Restaurant website discovery using Google search")
    print(f"   🔄 Intelligent fallback logic for better coverage")
    print(f"   📈 Improved dynamic content handling")

if __name__ == "__main__":
    # Run the Phase 1 improvement tests
    asyncio.run(run_phase1_tests())