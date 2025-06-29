#!/usr/bin/env python3
"""
Test Enhanced Allergen-Aware Menu Scraper
Comprehensive testing with practical allergen detection
"""

import json
import time
import logging
from typing import Dict, List, Any
from playwright.sync_api import sync_playwright
from enhanced_allergen_scraper import EnhancedMenuScraper, AllergenType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_restaurant_data(file_path: str = "restaurant_data.json") -> List[Dict[str, str]]:
    """Load restaurant data for testing"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Handle both flat list and nested structure
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and 'restaurants' in data:
                return data['restaurants']
            else:
                logger.error(f"Unexpected data structure in {file_path}")
                return []
    except FileNotFoundError:
        logger.error(f"Restaurant data file not found: {file_path}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing restaurant data: {e}")
        return []

def test_enhanced_allergen_scraper(sample_size: int = 18) -> Dict[str, Any]:
    """Test the enhanced allergen scraper with comprehensive metrics"""
    restaurants = load_restaurant_data()
    if not restaurants:
        logger.error("No restaurant data available for testing")
        return {}
    
    # Limit sample size
    test_restaurants = restaurants[:sample_size]
    
    scraper = EnhancedMenuScraper()
    results = []
    
    # Performance metrics
    total_tests = len(test_restaurants)
    successful_scrapes = 0
    total_items = 0
    total_processing_time = 0
    
    # Strategy usage tracking
    strategy_usage = {
        'css_selectors': 0,
        'text_patterns': 0,
        'structured_data': 0
    }
    
    # Allergen and dietary metrics
    allergen_detections = {allergen.value: 0 for allergen in AllergenType}
    dietary_tag_counts = {}
    confidence_scores = []
    category_distribution = {}
    
    # Quality metrics
    items_with_prices = 0
    items_with_descriptions = 0
    items_with_allergens = 0
    items_with_dietary_tags = 0
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            ]
        )
        
        page = browser.new_page()
        page.set_extra_http_headers({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        for i, restaurant in enumerate(test_restaurants, 1):
            name = restaurant.get('name', f'Restaurant {i}')
            url = restaurant.get('url', '')
            
            logger.info(f"Testing {i}/{total_tests}: {name}")
            
            try:
                # Test enhanced allergen scraper
                result = scraper.enhanced_menu_detection(page, url)
                
                # Update metrics
                if result.get('scraping_success', False):
                    successful_scrapes += 1
                
                items_found = result.get('total_items', 0)
                total_items += items_found
                total_processing_time += result.get('processing_time', 0)
                
                # Track strategy usage
                for strategy in result.get('extraction_strategies', []):
                    if strategy in strategy_usage:
                        strategy_usage[strategy] += 1
                
                # Track allergen detections
                allergen_summary = result.get('allergen_summary', {})
                for allergen, count in allergen_summary.items():
                    if allergen in allergen_detections:
                        allergen_detections[allergen] += count
                
                # Track dietary tags
                for tag in result.get('dietary_tags_detected', []):
                    dietary_tag_counts[tag] = dietary_tag_counts.get(tag, 0) + 1
                
                # Track confidence scores
                if result.get('confidence_score', 0) > 0:
                    confidence_scores.append(result['confidence_score'])
                
                # Track category distribution
                category_dist = result.get('category_distribution', {})
                for category, count in category_dist.items():
                    category_distribution[category] = category_distribution.get(category, 0) + count
                
                # Quality analysis
                for item in result.get('menu_items', []):
                    if item.get('price'):
                        items_with_prices += 1
                    if item.get('description') and len(item['description']) > 5:
                        items_with_descriptions += 1
                    if item.get('allergens'):
                        items_with_allergens += 1
                    if item.get('dietary_tags'):
                        items_with_dietary_tags += 1
                
                # Store detailed result
                detailed_result = {
                    'restaurant_name': name,
                    'url': url,
                    'scraping_success': result.get('scraping_success', False),
                    'total_items': items_found,
                    'processing_time': result.get('processing_time', 0),
                    'confidence_score': result.get('confidence_score', 0.0),
                    'extraction_strategies': result.get('extraction_strategies', []),
                    'allergen_summary': allergen_summary,
                    'dietary_tags_detected': result.get('dietary_tags_detected', []),
                    'category_distribution': category_dist,
                    'sample_items': result.get('menu_items', [])[:3],  # Store first 3 items
                    'error': result.get('error', None)
                }
                
                results.append(detailed_result)
                
                # Brief pause between requests
                time.sleep(1.5)
                
            except Exception as e:
                logger.error(f"Error testing {name}: {e}")
                results.append({
                    'restaurant_name': name,
                    'url': url,
                    'scraping_success': False,
                    'total_items': 0,
                    'error': str(e)
                })
        
        browser.close()
    
    # Calculate final metrics
    success_rate = (successful_scrapes / total_tests * 100) if total_tests > 0 else 0
    avg_items_per_success = (total_items / successful_scrapes) if successful_scrapes > 0 else 0
    avg_processing_time = total_processing_time / total_tests if total_tests > 0 else 0
    avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
    
    # Strategy usage rates
    strategy_usage_rates = {}
    for strategy, count in strategy_usage.items():
        strategy_usage_rates[strategy] = (count / total_tests * 100) if total_tests > 0 else 0
    
    # Quality metrics
    quality_metrics = {
        'price_coverage': (items_with_prices / total_items * 100) if total_items > 0 else 0,
        'description_coverage': (items_with_descriptions / total_items * 100) if total_items > 0 else 0,
        'allergen_coverage': (items_with_allergens / total_items * 100) if total_items > 0 else 0,
        'dietary_tag_coverage': (items_with_dietary_tags / total_items * 100) if total_items > 0 else 0
    }
    
    # Filter out allergens with no detections
    active_allergens = {k: v for k, v in allergen_detections.items() if v > 0}
    
    summary = {
        'scraper_version': 'Enhanced Allergen v1.0',
        'test_date': time.strftime('%Y-%m-%d %H:%M:%S'),
        'sample_size': total_tests,
        'success_rate': round(success_rate, 1),
        'successful_scrapes': successful_scrapes,
        'total_items_extracted': total_items,
        'avg_items_per_success': round(avg_items_per_success, 1),
        'avg_processing_time': round(avg_processing_time, 2),
        'avg_confidence_score': round(avg_confidence, 3),
        'strategy_usage_rates': {k: round(v, 1) for k, v in strategy_usage_rates.items()},
        'allergen_detections': active_allergens,
        'dietary_tag_counts': dietary_tag_counts,
        'category_distribution': category_distribution,
        'quality_metrics': {k: round(v, 1) for k, v in quality_metrics.items()},
        'confidence_score_range': {
            'min': round(min(confidence_scores), 3) if confidence_scores else 0,
            'max': round(max(confidence_scores), 3) if confidence_scores else 0,
            'avg': round(avg_confidence, 3)
        },
        'detailed_results': results
    }
    
    return summary

def save_test_results(results: Dict[str, Any], filename: str = "enhanced_allergen_test_results.json"):
    """Save test results to JSON file"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        logger.info(f"Test results saved to {filename}")
    except Exception as e:
        logger.error(f"Error saving test results: {e}")

def print_comprehensive_summary(results: Dict[str, Any]):
    """Print comprehensive test summary"""
    print("\n" + "="*80)
    print("ENHANCED ALLERGEN-AWARE MENU SCRAPER TEST RESULTS")
    print("="*80)
    
    print(f"\n📊 PERFORMANCE METRICS:")
    print(f"   Scraper Version: {results['scraper_version']}")
    print(f"   Test Date: {results['test_date']}")
    print(f"   Sample Size: {results['sample_size']} restaurants")
    print(f"   Success Rate: {results['success_rate']}% ({results['successful_scrapes']}/{results['sample_size']})")
    print(f"   Total Items: {results['total_items_extracted']}")
    print(f"   Avg Items/Success: {results['avg_items_per_success']}")
    print(f"   Avg Processing Time: {results['avg_processing_time']}s")
    print(f"   Avg Confidence Score: {results['avg_confidence_score']}")
    
    print(f"\n🔧 EXTRACTION STRATEGY USAGE:")
    for strategy, rate in results['strategy_usage_rates'].items():
        print(f"   {strategy.replace('_', ' ').title()}: {rate}%")
    
    print(f"\n📈 QUALITY METRICS:")
    quality = results['quality_metrics']
    print(f"   Price Coverage: {quality['price_coverage']}%")
    print(f"   Description Coverage: {quality['description_coverage']}%")
    print(f"   Allergen Coverage: {quality['allergen_coverage']}%")
    print(f"   Dietary Tag Coverage: {quality['dietary_tag_coverage']}%")
    
    print(f"\n⚠️  ALLERGEN DETECTIONS:")
    if results['allergen_detections']:
        for allergen, count in sorted(results['allergen_detections'].items(), key=lambda x: x[1], reverse=True):
            print(f"   {allergen.title()}: {count} items")
    else:
        print("   No allergens detected")
    
    print(f"\n🥗 DIETARY TAGS DETECTED:")
    if results['dietary_tag_counts']:
        for tag, count in sorted(results['dietary_tag_counts'].items(), key=lambda x: x[1], reverse=True):
            print(f"   {tag.title()}: {count} restaurants")
    else:
        print("   No dietary tags detected")
    
    print(f"\n📂 CATEGORY DISTRIBUTION:")
    if results['category_distribution']:
        for category, count in sorted(results['category_distribution'].items(), key=lambda x: x[1], reverse=True):
            print(f"   {category.title()}: {count} items")
    else:
        print("   No categories detected")
    
    print(f"\n📈 CONFIDENCE SCORE ANALYSIS:")
    conf_range = results['confidence_score_range']
    print(f"   Range: {conf_range['min']} - {conf_range['max']}")
    print(f"   Average: {conf_range['avg']}")
    
    print(f"\n🎯 TARGET ANALYSIS:")
    target_success_rate = 50.0
    current_rate = results['success_rate']
    gap = target_success_rate - current_rate
    
    if current_rate >= target_success_rate:
        print(f"   ✅ TARGET ACHIEVED! Success rate {current_rate}% exceeds {target_success_rate}% target")
        print(f"   🚀 Ready for production deployment!")
    else:
        print(f"   ⚠️  Gap to target: {gap:.1f}% (Current: {current_rate}%, Target: {target_success_rate}%)")
        if gap <= 10:
            print(f"   📈 Close to target - minor optimizations needed")
        else:
            print(f"   🔧 Significant improvements required")
    
    print(f"\n📋 SAMPLE SUCCESSFUL EXTRACTIONS:")
    successful_results = [r for r in results['detailed_results'] if r.get('scraping_success', False)]
    
    for i, result in enumerate(successful_results[:3], 1):
        print(f"\n   {i}. {result['restaurant_name']}:")
        print(f"      Items: {result['total_items']}")
        print(f"      Confidence: {result.get('confidence_score', 0):.3f}")
        print(f"      Strategies: {result.get('extraction_strategies', [])}")
        print(f"      Allergens: {list(result.get('allergen_summary', {}).keys())}")
        print(f"      Dietary Tags: {result.get('dietary_tags_detected', [])}")
        
        for j, item in enumerate(result.get('sample_items', [])[:2], 1):
            print(f"         {j}. {item.get('name', 'Unknown')} - {item.get('price', 'No price')}")
            if item.get('allergens'):
                print(f"            ⚠️  Allergens: {', '.join(item['allergens'])}")
            if item.get('dietary_tags'):
                print(f"            🥗 Dietary: {', '.join(item['dietary_tags'])}")
            print(f"            📊 Confidence: {item.get('confidence', 0):.2f}")
    
    print(f"\n🔄 COMPARISON WITH PREVIOUS VERSIONS:")
    print(f"   Enhanced Scraper: 40.0% success rate")
    print(f"   Final Optimized: 40.0% success rate")
    print(f"   ML Enhanced: 0.0% success rate (failed due to missing dependencies)")
    print(f"   Enhanced Allergen: {current_rate}% success rate")
    
    if current_rate > 40.0:
        print(f"   ✅ Enhanced Allergen shows {current_rate - 40.0:.1f}% improvement!")
        print(f"   🏆 NEW BEST PERFORMER!")
    elif current_rate == 40.0:
        print(f"   ➡️  Enhanced Allergen matches best previous performance")
        print(f"   ➕ Plus adds allergen detection capabilities")
    else:
        print(f"   ⚠️  Enhanced Allergen is {40.0 - current_rate:.1f}% below best previous performance")
    
    print(f"\n🚀 NEXT STEPS:")
    if current_rate >= target_success_rate:
        print(f"   • ✅ Deploy Enhanced Allergen scraper to production")
        print(f"   • 📊 Monitor allergen detection accuracy in real-world usage")
        print(f"   • 👥 Collect user feedback for allergen detection improvement")
        print(f"   • 🔄 Implement continuous learning from user corrections")
        print(f"   • 🌐 Expand to additional restaurant chains and websites")
        print(f"   • 📱 Integrate with AllergySavvy mobile app")
    else:
        print(f"   • 🔍 Analyze failed cases for pattern identification")
        print(f"   • 🎯 Focus on improving CSS selector accuracy")
        print(f"   • 📝 Enhance text pattern recognition")
        print(f"   • 🤖 Consider lightweight ML integration (without heavy dependencies)")
        print(f"   • 🔗 Investigate API partnerships with restaurant chains")
        print(f"   • 📊 A/B test different extraction strategies")
    
    print(f"\n💡 ALLERGEN DETECTION INSIGHTS:")
    if results['allergen_detections']:
        total_allergen_items = sum(results['allergen_detections'].values())
        print(f"   • {total_allergen_items} menu items contain identifiable allergens")
        print(f"   • {results['quality_metrics']['allergen_coverage']}% of items have allergen information")
        print(f"   • Most common allergens: {', '.join(list(results['allergen_detections'].keys())[:3])}")
    else:
        print(f"   • No allergens detected - may need keyword expansion")
        print(f"   • Consider adding more allergen detection patterns")
    
    print("\n" + "="*80)

def main():
    """Main test execution"""
    print("Starting Enhanced Allergen-Aware Menu Scraper Test...")
    
    # Run comprehensive test
    results = test_enhanced_allergen_scraper(sample_size=18)
    
    if results:
        # Save results
        save_test_results(results, "enhanced_allergen_test_results_n18.json")
        
        # Print summary
        print_comprehensive_summary(results)
        
        print(f"\n✅ Test completed successfully!")
        print(f"📁 Detailed results saved to: enhanced_allergen_test_results_n18.json")
    else:
        print("❌ Test failed - no results generated")

if __name__ == "__main__":
    main()