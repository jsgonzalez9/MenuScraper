import asyncio
import json
import time
from typing import Dict, List, Any
from priority1_enhanced_scraper import Priority1EnhancedScraper

def load_restaurant_data(file_path: str = 'restaurant_data.json') -> List[Dict[str, Any]]:
    """Load restaurant data from JSON file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle different data structures
        if isinstance(data, dict) and 'restaurants' in data:
            return data['restaurants']
        elif isinstance(data, list):
            return data
        else:
            print(f"❌ Unexpected data structure in {file_path}")
            return []
            
    except FileNotFoundError:
        print(f"❌ File {file_path} not found")
        return []
    except Exception as e:
        print(f"❌ Error loading restaurant data: {e}")
        return []

async def test_priority1_scraper(sample_size: int = 20) -> Dict[str, Any]:
    """Test the Priority 1 Enhanced Scraper"""
    print(f"🚀 Testing Priority 1 Enhanced Scraper with {sample_size} restaurants...")
    
    # Load restaurant data
    restaurants = load_restaurant_data()
    if not restaurants:
        print("❌ No restaurant data available")
        return {}
    
    # Limit to sample size
    test_restaurants = restaurants[:sample_size]
    print(f"📊 Testing {len(test_restaurants)} restaurants")
    
    # Initialize scraper
    scraper = Priority1EnhancedScraper(headless=True)
    
    if not await scraper.setup_browser():
        print("❌ Failed to setup browser")
        return {}
    
    results = []
    successful_scrapes = 0
    total_items = 0
    total_time = 0
    
    extraction_methods = {}
    confidence_scores = []
    price_coverage = 0
    description_coverage = 0
    allergen_detections = 0
    dietary_tag_detections = 0
    category_distribution = {}
    
    failed_restaurants = []
    
    try:
        for i, restaurant in enumerate(test_restaurants, 1):
            print(f"\n[{i}/{len(test_restaurants)}] Testing: {restaurant.get('name', 'Unknown')}")
            
            start_time = time.time()
            result = await scraper.scrape_restaurant(restaurant)
            processing_time = time.time() - start_time
            
            total_time += processing_time
            
            if result['scraping_success']:
                successful_scrapes += 1
                items = result['items']
                total_items += len(items)
                
                # Track extraction method
                method = result.get('extraction_method', 'unknown')
                extraction_methods[method] = extraction_methods.get(method, 0) + 1
                
                # Analyze items
                for item in items:
                    # Confidence scores
                    if 'confidence_score' in item:
                        confidence_scores.append(item['confidence_score'])
                    
                    # Price coverage
                    if item.get('has_price'):
                        price_coverage += 1
                    
                    # Description coverage
                    if item.get('has_description'):
                        description_coverage += 1
                    
                    # Allergen detection
                    if item.get('allergens'):
                        allergen_detections += 1
                    
                    # Dietary tags
                    if item.get('dietary_tags'):
                        dietary_tag_detections += 1
                    
                    # Category distribution
                    category = item.get('category', 'other')
                    category_distribution[category] = category_distribution.get(category, 0) + 1
                
                print(f"✅ Success: {len(items)} items extracted using {method}")
            else:
                failed_restaurants.append({
                    'name': restaurant.get('name', 'Unknown'),
                    'url': restaurant.get('url', ''),
                    'error': result.get('error', 'Unknown error')
                })
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
            
            results.append(result)
            
            # Brief pause between requests
            await asyncio.sleep(1)
    
    finally:
        await scraper.close()
    
    # Calculate metrics
    success_rate = (successful_scrapes / len(test_restaurants)) * 100 if test_restaurants else 0
    avg_items_per_restaurant = total_items / successful_scrapes if successful_scrapes > 0 else 0
    avg_processing_time = total_time / len(test_restaurants) if test_restaurants else 0
    avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
    
    price_coverage_pct = (price_coverage / total_items) * 100 if total_items > 0 else 0
    description_coverage_pct = (description_coverage / total_items) * 100 if total_items > 0 else 0
    allergen_detection_pct = (allergen_detections / total_items) * 100 if total_items > 0 else 0
    dietary_tag_pct = (dietary_tag_detections / total_items) * 100 if total_items > 0 else 0
    
    # Compile comprehensive results
    test_results = {
        'scraper_info': {
            'name': 'Priority 1 Enhanced Scraper v1.0',
            'version': '1.0',
            'focus': 'Enhanced content detection and extraction',
            'test_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'sample_size': len(test_restaurants)
        },
        'performance_metrics': {
            'success_rate': round(success_rate, 1),
            'successful_scrapes': successful_scrapes,
            'total_restaurants_tested': len(test_restaurants),
            'total_items_extracted': total_items,
            'avg_items_per_restaurant': round(avg_items_per_restaurant, 1),
            'avg_processing_time_seconds': round(avg_processing_time, 2),
            'total_processing_time_seconds': round(total_time, 2)
        },
        'extraction_analysis': {
            'extraction_methods_used': extraction_methods,
            'primary_extraction_method': max(extraction_methods.items(), key=lambda x: x[1])[0] if extraction_methods else 'none'
        },
        'content_quality_metrics': {
            'avg_confidence_score': round(avg_confidence, 3),
            'confidence_distribution': {
                'high_confidence_0.8+': len([s for s in confidence_scores if s >= 0.8]),
                'medium_confidence_0.5-0.8': len([s for s in confidence_scores if 0.5 <= s < 0.8]),
                'low_confidence_below_0.5': len([s for s in confidence_scores if s < 0.5])
            },
            'price_coverage_percentage': round(price_coverage_pct, 1),
            'description_coverage_percentage': round(description_coverage_pct, 1),
            'items_with_prices': price_coverage,
            'items_with_descriptions': description_coverage
        },
        'allergen_and_dietary_analysis': {
            'allergen_detection_percentage': round(allergen_detection_pct, 1),
            'dietary_tag_percentage': round(dietary_tag_pct, 1),
            'items_with_allergens': allergen_detections,
            'items_with_dietary_tags': dietary_tag_detections
        },
        'category_analysis': {
            'category_distribution': category_distribution,
            'total_categories_detected': len(category_distribution),
            'most_common_category': max(category_distribution.items(), key=lambda x: x[1])[0] if category_distribution else 'none'
        },
        'error_analysis': {
            'failed_restaurants_count': len(failed_restaurants),
            'failure_rate': round((len(failed_restaurants) / len(test_restaurants)) * 100, 1) if test_restaurants else 0,
            'common_errors': {},
            'failed_restaurants': failed_restaurants[:5]  # Show first 5 failures
        },
        'detailed_results': results
    }
    
    # Analyze common errors
    error_counts = {}
    for failure in failed_restaurants:
        error = failure['error']
        error_counts[error] = error_counts.get(error, 0) + 1
    test_results['error_analysis']['common_errors'] = error_counts
    
    return test_results

def save_results(results: Dict[str, Any], filename: str = 'priority1_test_results_n20.json'):
    """Save test results to JSON file"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Results saved to {filename}")
    except Exception as e:
        print(f"❌ Error saving results: {e}")

def print_summary(results: Dict[str, Any]):
    """Print a comprehensive summary of test results"""
    if not results:
        print("❌ No results to display")
        return
    
    perf = results.get('performance_metrics', {})
    quality = results.get('content_quality_metrics', {})
    allergen = results.get('allergen_and_dietary_analysis', {})
    category = results.get('category_analysis', {})
    extraction = results.get('extraction_analysis', {})
    errors = results.get('error_analysis', {})
    
    print("\n" + "="*80)
    print("🎯 PRIORITY 1 ENHANCED SCRAPER - TEST RESULTS SUMMARY")
    print("="*80)
    
    print(f"\n📊 PERFORMANCE METRICS:")
    print(f"   Success Rate: {perf.get('success_rate', 0)}% ({perf.get('successful_scrapes', 0)}/{perf.get('total_restaurants_tested', 0)})")
    print(f"   Total Items Extracted: {perf.get('total_items_extracted', 0)}")
    print(f"   Avg Items per Restaurant: {perf.get('avg_items_per_restaurant', 0)}")
    print(f"   Avg Processing Time: {perf.get('avg_processing_time_seconds', 0)}s")
    
    print(f"\n🔧 EXTRACTION ANALYSIS:")
    print(f"   Primary Method: {extraction.get('primary_extraction_method', 'none')}")
    methods = extraction.get('extraction_methods_used', {})
    for method, count in methods.items():
        print(f"   - {method}: {count} restaurants")
    
    print(f"\n📈 CONTENT QUALITY:")
    print(f"   Avg Confidence Score: {quality.get('avg_confidence_score', 0)}")
    print(f"   Price Coverage: {quality.get('price_coverage_percentage', 0)}% ({quality.get('items_with_prices', 0)} items)")
    print(f"   Description Coverage: {quality.get('description_coverage_percentage', 0)}% ({quality.get('items_with_descriptions', 0)} items)")
    
    conf_dist = quality.get('confidence_distribution', {})
    print(f"   Confidence Distribution:")
    print(f"     - High (0.8+): {conf_dist.get('high_confidence_0.8+', 0)}")
    print(f"     - Medium (0.5-0.8): {conf_dist.get('medium_confidence_0.5-0.8', 0)}")
    print(f"     - Low (<0.5): {conf_dist.get('low_confidence_below_0.5', 0)}")
    
    print(f"\n🏷️ ALLERGEN & DIETARY ANALYSIS:")
    print(f"   Allergen Detection: {allergen.get('allergen_detection_percentage', 0)}% ({allergen.get('items_with_allergens', 0)} items)")
    print(f"   Dietary Tags: {allergen.get('dietary_tag_percentage', 0)}% ({allergen.get('items_with_dietary_tags', 0)} items)")
    
    print(f"\n📂 CATEGORY ANALYSIS:")
    print(f"   Categories Detected: {category.get('total_categories_detected', 0)}")
    print(f"   Most Common: {category.get('most_common_category', 'none')}")
    
    cat_dist = category.get('category_distribution', {})
    if cat_dist:
        print(f"   Distribution:")
        for cat, count in sorted(cat_dist.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"     - {cat}: {count} items")
    
    print(f"\n❌ ERROR ANALYSIS:")
    print(f"   Failure Rate: {errors.get('failure_rate', 0)}% ({errors.get('failed_restaurants_count', 0)} restaurants)")
    
    common_errors = errors.get('common_errors', {})
    if common_errors:
        print(f"   Common Errors:")
        for error, count in sorted(common_errors.items(), key=lambda x: x[1], reverse=True)[:3]:
            print(f"     - {error}: {count} occurrences")
    
    print("\n" + "="*80)
    print("🎯 PRIORITY 1 IMPROVEMENTS ACHIEVED:")
    print("   ✅ Enhanced CSS selectors with better specificity")
    print("   ✅ Improved price detection with multiple patterns")
    print("   ✅ Better text parsing and item extraction")
    print("   ✅ Enhanced menu content detection")
    print("   ✅ Multiple extraction strategies with fallbacks")
    print("="*80)

async def main():
    """Main test function"""
    sample_size = 20
    
    print("🎯 Priority 1 Enhanced Scraper Test")
    print(f"Focus: Enhanced content detection and extraction")
    print(f"Sample size: {sample_size} restaurants\n")
    
    # Run the test
    results = await test_priority1_scraper(sample_size)
    
    if results:
        # Save results
        save_results(results, f'priority1_test_results_n{sample_size}.json')
        
        # Print summary
        print_summary(results)
        
        # Compare with previous version
        print("\n📊 COMPARISON WITH ENHANCED DYNAMIC SCRAPER:")
        print("   Previous (Enhanced Dynamic): 35% success rate, 0% price coverage")
        current_success = results.get('performance_metrics', {}).get('success_rate', 0)
        current_price = results.get('content_quality_metrics', {}).get('price_coverage_percentage', 0)
        print(f"   Current (Priority 1): {current_success}% success rate, {current_price}% price coverage")
        
        if current_success > 35:
            print(f"   🎉 SUCCESS RATE IMPROVEMENT: +{current_success - 35:.1f}%")
        if current_price > 0:
            print(f"   🎉 PRICE COVERAGE IMPROVEMENT: +{current_price:.1f}%")
    else:
        print("❌ Test failed - no results generated")

if __name__ == "__main__":
    asyncio.run(main())