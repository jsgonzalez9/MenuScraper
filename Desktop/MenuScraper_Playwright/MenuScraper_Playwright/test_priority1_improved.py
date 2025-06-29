import asyncio
import json
import time
from priority1_improved_scraper import Priority1ImprovedScraper

def load_restaurant_data():
    """Load restaurant data from JSON file"""
    try:
        with open('restaurant_data.json', 'r') as f:
            data = json.load(f)
            
        # Handle both formats
        if isinstance(data, dict) and 'restaurants' in data:
            restaurants = data['restaurants']
        elif isinstance(data, list):
            restaurants = data
        else:
            raise ValueError("Invalid data format")
            
        return restaurants
    except Exception as e:
        print(f"Error loading restaurant data: {e}")
        return []

async def test_improved_scraper(num_restaurants=20):
    """Test the Priority 1 Improved Scraper"""
    print("🚀 Starting Priority 1 Improved Scraper Test")
    print("=" * 50)
    
    # Load restaurant data
    restaurants = load_restaurant_data()
    if not restaurants:
        print("❌ No restaurant data found")
        return
    
    # Limit to specified number
    test_restaurants = restaurants[:num_restaurants]
    print(f"📊 Testing {len(test_restaurants)} restaurants")
    
    # Initialize scraper
    scraper = Priority1ImprovedScraper(headless=True, timeout=30000)
    
    if not await scraper.setup_browser():
        print("❌ Failed to setup browser")
        return
    
    results = []
    successful_scrapes = 0
    total_items = 0
    total_time = 0
    
    try:
        for i, restaurant in enumerate(test_restaurants, 1):
            print(f"\n[{i}/{len(test_restaurants)}] Testing: {restaurant['name']}")
            print(f"URL: {restaurant['url']}")
            
            start_time = time.time()
            result = await scraper.scrape_restaurant(restaurant)
            processing_time = time.time() - start_time
            
            total_time += processing_time
            
            if result['scraping_success']:
                successful_scrapes += 1
                total_items += result['total_items']
                print(f"✅ Success: {result['total_items']} items ({result['extraction_method']})")
                
                # Show sample items with prices
                items_with_prices = [item for item in result['items'] if item.get('price') is not None]
                if items_with_prices:
                    print(f"💰 Items with prices: {len(items_with_prices)}")
                    for item in items_with_prices[:2]:
                        print(f"   - {item['name']}: ${item['price']}")
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
            
            print(f"⏱️  Time: {processing_time:.1f}s")
            results.append(result)
    
    finally:
        await scraper.close()
    
    # Save results
    output_file = f'priority1_improved_test_results_n{num_restaurants}.json'
    await save_results(results, output_file)
    
    # Print summary
    print_summary(results, total_time)

async def save_results(results, filename):
    """Save test results to JSON file"""
    try:
        # Calculate metrics
        successful_results = [r for r in results if r['scraping_success']]
        total_items = sum(r['total_items'] for r in successful_results)
        
        # Content quality metrics
        items_with_price = 0
        items_with_description = 0
        confidence_scores = []
        categories = {}
        allergen_detections = 0
        dietary_tag_detections = 0
        extraction_methods = {}
        
        for result in successful_results:
            for item in result['items']:
                if item.get('price') is not None:
                    items_with_price += 1
                if item.get('description'):
                    items_with_description += 1
                
                confidence_scores.append(item.get('confidence_score', 0))
                
                category = item.get('category', 'other')
                categories[category] = categories.get(category, 0) + 1
                
                if item.get('allergens'):
                    allergen_detections += len(item['allergens'])
                if item.get('dietary_tags'):
                    dietary_tag_detections += len(item['dietary_tags'])
            
            method = result.get('extraction_method', 'unknown')
            extraction_methods[method] = extraction_methods.get(method, 0) + 1
        
        # Error analysis
        failed_results = [r for r in results if not r['scraping_success']]
        error_types = {}
        for result in failed_results:
            error = result.get('error', 'Unknown error')
            error_types[error] = error_types.get(error, 0) + 1
        
        # Compile summary
        summary = {
            'test_info': {
                'scraper_version': 'Priority1ImprovedScraper',
                'total_restaurants_tested': len(results),
                'test_timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            },
            'performance_metrics': {
                'success_rate': (len(successful_results) / len(results)) * 100,
                'successful_scrapes': len(successful_results),
                'failed_scrapes': len(failed_results),
                'total_items_extracted': total_items,
                'avg_items_per_success': total_items / len(successful_results) if successful_results else 0
            },
            'content_quality': {
                'price_coverage': (items_with_price / total_items * 100) if total_items > 0 else 0,
                'description_coverage': (items_with_description / total_items * 100) if total_items > 0 else 0,
                'avg_confidence_score': sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0,
                'items_with_price': items_with_price,
                'items_with_description': items_with_description
            },
            'categorization': categories,
            'allergen_dietary': {
                'allergen_detections': allergen_detections,
                'dietary_tag_detections': dietary_tag_detections
            },
            'extraction_methods': extraction_methods,
            'error_analysis': {
                'error_types': error_types,
                'failed_restaurants': [r['restaurant_name'] for r in failed_results]
            },
            'detailed_results': results
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Results saved to: {filename}")
        
    except Exception as e:
        print(f"❌ Error saving results: {e}")

def print_summary(results, total_time):
    """Print test summary"""
    print("\n" + "=" * 60)
    print("📊 PRIORITY 1 IMPROVED SCRAPER TEST SUMMARY")
    print("=" * 60)
    
    successful_results = [r for r in results if r['scraping_success']]
    failed_results = [r for r in results if not r['scraping_success']]
    total_items = sum(r['total_items'] for r in successful_results)
    
    # Basic metrics
    success_rate = (len(successful_results) / len(results)) * 100
    print(f"🎯 Success Rate: {success_rate:.1f}% ({len(successful_results)}/{len(results)})")
    print(f"📦 Total Items: {total_items}")
    print(f"⏱️  Total Time: {total_time:.1f}s")
    print(f"⚡ Avg Time/Restaurant: {total_time/len(results):.1f}s")
    
    if successful_results:
        print(f"📈 Avg Items/Success: {total_items/len(successful_results):.1f}")
    
    # Content quality analysis
    items_with_price = 0
    items_with_description = 0
    confidence_scores = []
    categories = {}
    
    for result in successful_results:
        for item in result['items']:
            if item.get('price') is not None:
                items_with_price += 1
            if item.get('description'):
                items_with_description += 1
            confidence_scores.append(item.get('confidence_score', 0))
            category = item.get('category', 'other')
            categories[category] = categories.get(category, 0) + 1
    
    print("\n📋 CONTENT QUALITY:")
    if total_items > 0:
        price_coverage = (items_with_price / total_items) * 100
        desc_coverage = (items_with_description / total_items) * 100
        print(f"💰 Price Coverage: {price_coverage:.1f}% ({items_with_price}/{total_items})")
        print(f"📝 Description Coverage: {desc_coverage:.1f}% ({items_with_description}/{total_items})")
    
    if confidence_scores:
        avg_confidence = sum(confidence_scores) / len(confidence_scores)
        print(f"🎯 Avg Confidence: {avg_confidence:.3f}")
    
    # Category breakdown
    if categories:
        print("\n🏷️  CATEGORIES:")
        for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_items) * 100 if total_items > 0 else 0
            print(f"   {category}: {count} ({percentage:.1f}%)")
    
    # Error analysis
    if failed_results:
        print("\n❌ FAILED RESTAURANTS:")
        error_counts = {}
        for result in failed_results:
            error = result.get('error', 'Unknown error')
            error_counts[error] = error_counts.get(error, 0) + 1
        
        for error, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"   {error}: {count}")
    
    # Extraction methods
    extraction_methods = {}
    for result in successful_results:
        method = result.get('extraction_method', 'unknown')
        extraction_methods[method] = extraction_methods.get(method, 0) + 1
    
    if extraction_methods:
        print("\n🔧 EXTRACTION METHODS:")
        for method, count in sorted(extraction_methods.items(), key=lambda x: x[1], reverse=True):
            print(f"   {method}: {count}")
    
    print("\n" + "=" * 60)
    
    # Comparison with previous results
    print("\n📈 COMPARISON WITH PREVIOUS SCRAPER:")
    print("Previous Enhanced Dynamic Scraper: 35% success rate, 0% price coverage")
    print(f"Current Improved Scraper: {success_rate:.1f}% success rate, {(items_with_price / total_items * 100) if total_items > 0 else 0:.1f}% price coverage")
    
    if success_rate > 35:
        print("✅ SUCCESS RATE IMPROVED!")
    elif success_rate == 35:
        print("➡️  Success rate maintained")
    else:
        print("⚠️  Success rate decreased")
    
    if total_items > 0 and (items_with_price / total_items * 100) > 0:
        print("✅ PRICE COVERAGE IMPROVED!")
    else:
        print("⚠️  Price coverage still needs work")

if __name__ == "__main__":
    asyncio.run(test_improved_scraper(20))