#!/usr/bin/env python3
"""
Test Enhanced Dynamic Menu Scraper
Evaluates the performance of the enhanced scraper with improved selectors and dynamic content handling
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Any
import statistics

from enhanced_dynamic_scraper import EnhancedDynamicScraper

def load_restaurant_data(filename: str = 'restaurant_data.json') -> List[Dict[str, Any]]:
    """Load restaurant data from JSON file"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('restaurants', [])
    except FileNotFoundError:
        print(f"❌ File {filename} not found")
        return []
    except json.JSONDecodeError:
        print(f"❌ Invalid JSON in {filename}")
        return []

async def test_enhanced_dynamic_scraper(sample_size: int = 20) -> Dict[str, Any]:
    """Test the enhanced dynamic scraper with comprehensive metrics"""
    
    print(f"🚀 Testing Enhanced Dynamic Scraper (Sample size: {sample_size})")
    print("=" * 60)
    
    # Load restaurant data
    restaurants = load_restaurant_data()
    if not restaurants:
        print("❌ No restaurant data available")
        return {}
    
    # Take sample
    test_restaurants = restaurants[:sample_size]
    print(f"📊 Testing {len(test_restaurants)} restaurants")
    
    # Initialize scraper
    scraper = EnhancedDynamicScraper(headless=True, timeout=30000)
    
    if not await scraper.setup_browser():
        print("❌ Failed to setup browser")
        return {}
    
    # Test results storage
    results = []
    successful_scrapes = 0
    total_items = 0
    total_time = 0
    
    # Metrics tracking
    extraction_methods = {}
    confidence_scores = []
    allergen_detections = 0
    items_with_prices = 0
    items_with_descriptions = 0
    category_distribution = {}
    dietary_tags_found = 0
    processing_times = []
    
    # Error tracking
    error_types = {}
    
    start_time = time.time()
    
    try:
        for i, restaurant in enumerate(test_restaurants, 1):
            print(f"\n[{i}/{len(test_restaurants)}] Testing: {restaurant.get('name', 'Unknown')}")
            print(f"URL: {restaurant.get('url', 'No URL')}")
            
            # Scrape restaurant
            result = await scraper.scrape_restaurant_enhanced(restaurant)
            results.append(result)
            
            # Update metrics
            if result['scraping_success']:
                successful_scrapes += 1
                total_items += result['total_items']
                
                # Track extraction method
                method = result.get('extraction_method', 'unknown')
                extraction_methods[method] = extraction_methods.get(method, 0) + 1
                
                # Analyze items
                for item in result.get('items', []):
                    # Confidence scores
                    if 'confidence_score' in item:
                        confidence_scores.append(item['confidence_score'])
                    
                    # Allergen detection
                    if item.get('allergens'):
                        allergen_detections += 1
                    
                    # Price and description tracking
                    if item.get('has_price'):
                        items_with_prices += 1
                    if item.get('has_description'):
                        items_with_descriptions += 1
                    
                    # Category distribution
                    category = item.get('category', 'unknown')
                    category_distribution[category] = category_distribution.get(category, 0) + 1
                    
                    # Dietary tags
                    if item.get('dietary_tags'):
                        dietary_tags_found += 1
                
                print(f"✅ Success: {result['total_items']} items found")
            else:
                error = result.get('error', 'Unknown error')
                error_type = error.split(':')[0] if ':' in error else error
                error_types[error_type] = error_types.get(error_type, 0) + 1
                print(f"❌ Failed: {error}")
            
            # Track processing time
            processing_times.append(result.get('processing_time', 0))
            total_time += result.get('processing_time', 0)
            
            # Small delay between requests
            await asyncio.sleep(1)
    
    finally:
        await scraper.cleanup()
    
    # Calculate final metrics
    success_rate = (successful_scrapes / len(test_restaurants)) * 100
    avg_items_per_success = total_items / successful_scrapes if successful_scrapes > 0 else 0
    avg_processing_time = statistics.mean(processing_times) if processing_times else 0
    
    # Confidence score analysis
    avg_confidence = statistics.mean(confidence_scores) if confidence_scores else 0
    confidence_distribution = {
        'high': len([s for s in confidence_scores if s >= 0.8]),
        'medium': len([s for s in confidence_scores if 0.5 <= s < 0.8]),
        'low': len([s for s in confidence_scores if s < 0.5])
    }
    
    # Quality metrics
    price_coverage = (items_with_prices / total_items * 100) if total_items > 0 else 0
    description_coverage = (items_with_descriptions / total_items * 100) if total_items > 0 else 0
    allergen_detection_rate = (allergen_detections / total_items * 100) if total_items > 0 else 0
    
    # Compile comprehensive results
    test_results = {
        'scraper_info': {
            'name': 'Enhanced Dynamic Scraper v1.0',
            'version': '1.0',
            'test_date': datetime.now().isoformat(),
            'sample_size': len(test_restaurants)
        },
        'performance_metrics': {
            'success_rate': round(success_rate, 1),
            'successful_scrapes': successful_scrapes,
            'total_items_extracted': total_items,
            'average_items_per_success': round(avg_items_per_success, 1),
            'total_processing_time': round(total_time, 2),
            'average_processing_time': round(avg_processing_time, 2)
        },
        'extraction_analysis': {
            'methods_used': extraction_methods,
            'primary_method': max(extraction_methods.items(), key=lambda x: x[1])[0] if extraction_methods else 'none'
        },
        'ml_metrics': {
            'confidence_scores': {
                'average': round(avg_confidence, 3),
                'distribution': confidence_distribution,
                'total_scored_items': len(confidence_scores)
            },
            'allergen_detection': {
                'items_with_allergens': allergen_detections,
                'detection_rate_percent': round(allergen_detection_rate, 1)
            },
            'dietary_tags': {
                'items_with_tags': dietary_tags_found,
                'tag_rate_percent': round((dietary_tags_found / total_items * 100) if total_items > 0 else 0, 1)
            }
        },
        'quality_metrics': {
            'price_coverage_percent': round(price_coverage, 1),
            'description_coverage_percent': round(description_coverage, 1),
            'category_distribution': category_distribution
        },
        'error_analysis': {
            'failed_scrapes': len(test_restaurants) - successful_scrapes,
            'error_types': error_types,
            'most_common_error': max(error_types.items(), key=lambda x: x[1])[0] if error_types else 'none'
        },
        'detailed_results': results
    }
    
    # Save results to file
    output_filename = f'enhanced_dynamic_test_results_n{sample_size}.json'
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(test_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n📊 ENHANCED DYNAMIC SCRAPER TEST RESULTS")
    print("=" * 60)
    print(f"🎯 Success Rate: {success_rate:.1f}% ({successful_scrapes}/{len(test_restaurants)})")
    print(f"📦 Total Items: {total_items}")
    print(f"📈 Avg Items/Success: {avg_items_per_success:.1f}")
    print(f"⏱️  Avg Processing Time: {avg_processing_time:.2f}s")
    
    print(f"\n🔍 EXTRACTION ANALYSIS:")
    for method, count in extraction_methods.items():
        print(f"  • {method}: {count} restaurants")
    
    print(f"\n🤖 ML-INSPIRED METRICS:")
    print(f"  • Avg Confidence: {avg_confidence:.3f}")
    print(f"  • High Confidence: {confidence_distribution['high']} items")
    print(f"  • Medium Confidence: {confidence_distribution['medium']} items")
    print(f"  • Low Confidence: {confidence_distribution['low']} items")
    print(f"  • Allergen Detection: {allergen_detection_rate:.1f}% ({allergen_detections} items)")
    print(f"  • Dietary Tags: {dietary_tags_found} items")
    
    print(f"\n📋 QUALITY METRICS:")
    print(f"  • Price Coverage: {price_coverage:.1f}%")
    print(f"  • Description Coverage: {description_coverage:.1f}%")
    
    print(f"\n📊 CATEGORY DISTRIBUTION:")
    for category, count in sorted(category_distribution.items(), key=lambda x: x[1], reverse=True):
        print(f"  • {category}: {count} items")
    
    if error_types:
        print(f"\n❌ ERROR ANALYSIS:")
        for error_type, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
            print(f"  • {error_type}: {count} occurrences")
    
    print(f"\n💾 Results saved to: {output_filename}")
    
    # Performance comparison note
    print(f"\n📈 PERFORMANCE COMPARISON:")
    print(f"  • Target Success Rate: 50%+")
    print(f"  • Current Success Rate: {success_rate:.1f}%")
    if success_rate >= 50:
        print(f"  • ✅ TARGET ACHIEVED! (+{success_rate-50:.1f}% above target)")
    else:
        print(f"  • ⚠️  Need {50-success_rate:.1f}% improvement to reach target")
    
    return test_results

async def main():
    """Main test function"""
    try:
        # Test with sample size of 20
        results = await test_enhanced_dynamic_scraper(sample_size=20)
        
        if results:
            print("\n🎉 Enhanced Dynamic Scraper test completed successfully!")
        else:
            print("\n❌ Enhanced Dynamic Scraper test failed!")
            
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")

if __name__ == "__main__":
    asyncio.run(main())