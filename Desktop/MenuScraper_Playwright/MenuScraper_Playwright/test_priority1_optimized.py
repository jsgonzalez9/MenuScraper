import asyncio
import json
import time
from typing import Dict, List, Any
from priority1_optimized_scraper import Priority1OptimizedScraper

def load_restaurant_data(file_path: str = 'restaurant_data.json', limit: int = 20) -> List[Dict[str, Any]]:
    """Load restaurant data from JSON file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle different JSON structures
        if isinstance(data, dict) and 'restaurants' in data:
            restaurants = data['restaurants']
        elif isinstance(data, list):
            restaurants = data
        else:
            print(f"❌ Unexpected data structure in {file_path}")
            return []
        
        return restaurants[:limit]
    
    except Exception as e:
        print(f"❌ Error loading restaurant data: {e}")
        return []

async def run_test(restaurants: List[Dict[str, Any]], scraper_name: str = "Priority1OptimizedScraper") -> Dict[str, Any]:
    """Run scraping test on restaurants"""
    print(f"\n🚀 Starting {scraper_name} test with {len(restaurants)} restaurants...")
    
    scraper = Priority1OptimizedScraper(headless=True, timeout=30000)
    
    # Setup browser
    if not await scraper.setup_browser():
        print("❌ Failed to setup browser")
        return {}
    
    results = []
    successful_scrapes = 0
    total_items = 0
    total_time = 0
    
    for i, restaurant in enumerate(restaurants, 1):
        print(f"\n📍 [{i}/{len(restaurants)}] Testing: {restaurant.get('name', 'Unknown')}")
        
        try:
            result = await scraper.scrape_restaurant(restaurant)
            results.append(result)
            
            if result['scraping_success']:
                successful_scrapes += 1
                total_items += result['total_items']
                print(f"   ✅ Success: {result['total_items']} items ({result.get('extraction_method', 'unknown')})")
            else:
                print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")
            
            total_time += result['processing_time']
            
        except Exception as e:
            print(f"   💥 Exception: {e}")
            results.append({
                'restaurant_name': restaurant.get('name', 'Unknown'),
                'url': restaurant.get('url', ''),
                'scraping_success': False,
                'error': f'Test exception: {str(e)}',
                'processing_time': 0
            })
    
    await scraper.close()
    
    # Compile test results
    test_results = {
        'scraper_name': scraper_name,
        'test_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'total_restaurants': len(restaurants),
        'successful_scrapes': successful_scrapes,
        'success_rate': (successful_scrapes / len(restaurants)) * 100,
        'total_items_extracted': total_items,
        'average_items_per_success': total_items / max(successful_scrapes, 1),
        'total_processing_time': total_time,
        'average_time_per_restaurant': total_time / len(restaurants),
        'results': results
    }
    
    return test_results

def analyze_results(test_results: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze test results for detailed metrics"""
    results = test_results.get('results', [])
    
    # Basic metrics
    successful_results = [r for r in results if r.get('scraping_success', False)]
    failed_results = [r for r in results if not r.get('scraping_success', False)]
    
    # Content quality analysis
    items_with_price = 0
    items_with_description = 0
    total_confidence = 0
    confidence_count = 0
    category_counts = {}
    extraction_methods = {}
    
    for result in successful_results:
        for item in result.get('items', []):
            if item.get('price') is not None:
                items_with_price += 1
            if item.get('description'):
                items_with_description += 1
            if 'confidence_score' in item:
                total_confidence += item['confidence_score']
                confidence_count += 1
            
            category = item.get('category', 'unknown')
            category_counts[category] = category_counts.get(category, 0) + 1
        
        method = result.get('extraction_method', 'unknown')
        extraction_methods[method] = extraction_methods.get(method, 0) + 1
    
    # Error analysis
    error_counts = {}
    for result in failed_results:
        error = result.get('error', 'Unknown error')
        error_counts[error] = error_counts.get(error, 0) + 1
    
    total_items = test_results.get('total_items_extracted', 0)
    
    analysis = {
        'content_quality': {
            'price_coverage': (items_with_price / max(total_items, 1)) * 100,
            'description_coverage': (items_with_description / max(total_items, 1)) * 100,
            'average_confidence': total_confidence / max(confidence_count, 1),
            'items_with_price': items_with_price,
            'items_with_description': items_with_description
        },
        'category_distribution': category_counts,
        'extraction_methods': extraction_methods,
        'error_analysis': {
            'total_failures': len(failed_results),
            'failure_rate': (len(failed_results) / len(results)) * 100,
            'error_types': error_counts
        },
        'performance_comparison': {
            'previous_scrapers': {
                'enhanced_scraper': {'success_rate': 35.0, 'price_coverage': 0.0},
                'priority1_scraper': {'success_rate': 35.0, 'price_coverage': 0.0},
                'improved_scraper': {'success_rate': 0.0, 'price_coverage': 0.0},
                'balanced_scraper': {'success_rate': 35.0, 'price_coverage': 0.0},
                'final_scraper': {'success_rate': 0.0, 'price_coverage': 0.0}
            },
            'current_scraper': {
                'success_rate': test_results.get('success_rate', 0),
                'price_coverage': (items_with_price / max(total_items, 1)) * 100
            }
        }
    }
    
    return analysis

def save_results(test_results: Dict[str, Any], analysis: Dict[str, Any], filename: str):
    """Save test results and analysis to file"""
    output = {
        'test_results': test_results,
        'analysis': analysis
    }
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Results saved to {filename}")
    except Exception as e:
        print(f"❌ Error saving results: {e}")

def print_summary(test_results: Dict[str, Any], analysis: Dict[str, Any]):
    """Print test summary"""
    print(f"\n{'='*60}")
    print(f"🎯 PRIORITY 1 OPTIMIZED SCRAPER TEST SUMMARY")
    print(f"{'='*60}")
    
    # Basic metrics
    print(f"\n📊 BASIC METRICS:")
    print(f"   • Success Rate: {test_results.get('success_rate', 0):.1f}%")
    print(f"   • Total Items: {test_results.get('total_items_extracted', 0)}")
    print(f"   • Avg Items/Success: {test_results.get('average_items_per_success', 0):.1f}")
    print(f"   • Avg Time/Restaurant: {test_results.get('average_time_per_restaurant', 0):.1f}s")
    
    # Content quality
    quality = analysis.get('content_quality', {})
    print(f"\n🎨 CONTENT QUALITY:")
    print(f"   • Price Coverage: {quality.get('price_coverage', 0):.1f}%")
    print(f"   • Description Coverage: {quality.get('description_coverage', 0):.1f}%")
    print(f"   • Average Confidence: {quality.get('average_confidence', 0):.2f}")
    print(f"   • Items with Price: {quality.get('items_with_price', 0)}")
    print(f"   • Items with Description: {quality.get('items_with_description', 0)}")
    
    # Extraction methods
    methods = analysis.get('extraction_methods', {})
    print(f"\n🔧 EXTRACTION METHODS:")
    for method, count in methods.items():
        print(f"   • {method}: {count} restaurants")
    
    # Categories
    categories = analysis.get('category_distribution', {})
    print(f"\n📂 CATEGORY DISTRIBUTION:")
    for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        print(f"   • {category}: {count} items")
    
    # Error analysis
    errors = analysis.get('error_analysis', {})
    print(f"\n❌ ERROR ANALYSIS:")
    print(f"   • Failure Rate: {errors.get('failure_rate', 0):.1f}%")
    error_types = errors.get('error_types', {})
    for error, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
        print(f"   • {error}: {count} occurrences")
    
    # Performance comparison
    comparison = analysis.get('performance_comparison', {})
    current = comparison.get('current_scraper', {})
    print(f"\n📈 PERFORMANCE COMPARISON:")
    print(f"   Current Optimized Scraper:")
    print(f"     - Success Rate: {current.get('success_rate', 0):.1f}%")
    print(f"     - Price Coverage: {current.get('price_coverage', 0):.1f}%")
    
    previous = comparison.get('previous_scrapers', {})
    print(f"   Previous Best (Balanced): {previous.get('balanced_scraper', {}).get('success_rate', 0):.1f}% success, {previous.get('balanced_scraper', {}).get('price_coverage', 0):.1f}% price")
    
    # Success/failure examples
    results = test_results.get('results', [])
    successful = [r for r in results if r.get('scraping_success', False)]
    failed = [r for r in results if not r.get('scraping_success', False)]
    
    if successful:
        print(f"\n✅ SUCCESSFUL RESTAURANTS:")
        for result in successful[:5]:
            items_count = result.get('total_items', 0)
            method = result.get('extraction_method', 'unknown')
            print(f"   • {result.get('restaurant_name', 'Unknown')}: {items_count} items ({method})")
    
    if failed:
        print(f"\n❌ FAILED RESTAURANTS:")
        for result in failed[:5]:
            error = result.get('error', 'Unknown error')
            print(f"   • {result.get('restaurant_name', 'Unknown')}: {error}")
    
    # Final assessment
    success_rate = test_results.get('success_rate', 0)
    price_coverage = quality.get('price_coverage', 0)
    
    print(f"\n🏆 FINAL ASSESSMENT:")
    if success_rate >= 50 and price_coverage >= 20:
        print(f"   🎉 EXCELLENT: Target achieved! Success rate {success_rate:.1f}% and price coverage {price_coverage:.1f}%")
    elif success_rate >= 40:
        print(f"   ✅ GOOD: Success rate {success_rate:.1f}% is promising, price coverage needs improvement")
    elif success_rate >= 30:
        print(f"   ⚠️  MODERATE: Success rate {success_rate:.1f}% is acceptable, but needs optimization")
    else:
        print(f"   ❌ POOR: Success rate {success_rate:.1f}% needs significant improvement")

async def main():
    """Main test function"""
    # Load restaurant data
    restaurants = load_restaurant_data('restaurant_data.json', limit=20)
    
    if not restaurants:
        print("❌ No restaurant data loaded")
        return
    
    # Run test
    test_results = await run_test(restaurants, "Priority1OptimizedScraper")
    
    if not test_results:
        print("❌ Test failed")
        return
    
    # Analyze results
    analysis = analyze_results(test_results)
    
    # Save results
    save_results(test_results, analysis, 'priority1_optimized_test_results_n20.json')
    
    # Print summary
    print_summary(test_results, analysis)

if __name__ == "__main__":
    asyncio.run(main())