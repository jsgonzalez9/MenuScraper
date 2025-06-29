#!/usr/bin/env python3
"""
Final ML-Enhanced Menu Scraper Test Suite
Comprehensive evaluation with ML features and allergen detection
Target: Achieve 50%+ success rate with enhanced ML capabilities
"""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import statistics

from final_ml_menu_scraper import FinalMLMenuScraper

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
            
        print(f"📊 Loaded {len(restaurants)} restaurants for ML testing")
        return restaurants
        
    except FileNotFoundError:
        print("❌ restaurant_data.json not found")
        return []
    except Exception as e:
        print(f"❌ Error loading restaurant data: {e}")
        return []

async def test_final_ml_scraper(sample_size: int = 20) -> Dict[str, Any]:
    """Test the final ML-enhanced scraper with comprehensive metrics"""
    print(f"\n🤖 STARTING FINAL ML-ENHANCED SCRAPER TEST")
    print(f"📊 Sample size: {sample_size}")
    print(f"🎯 Target success rate: 50%+")
    print(f"🧠 ML Features: Enhanced allergen detection, confidence scoring, smart extraction")
    print("=" * 80)
    
    # Load restaurant data
    restaurants = load_restaurant_data()
    if not restaurants:
        print("❌ No restaurant data available for testing")
        return {}
    
    # Limit sample size
    test_restaurants = restaurants[:sample_size]
    
    # Initialize ML scraper
    scraper = FinalMLMenuScraper(headless=True, timeout=25000)
    
    # Test results storage
    results = {
        'scraper_version': 'Final ML-Enhanced v1.0',
        'test_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'sample_size': len(test_restaurants),
        'success_rate': 0.0,
        'successful_scrapes': 0,
        'total_items_extracted': 0,
        'avg_items_per_success': 0,
        'avg_processing_time': 0,
        
        # ML-specific metrics
        'ml_metrics': {
            'avg_confidence_score': 0,
            'confidence_score_distribution': {
                'high': 0,  # > 0.7
                'medium': 0,  # 0.4-0.7
                'low': 0   # < 0.4
            },
            'extraction_strategy_success': {},
            'quality_assessment_avg': 0,
            'ml_features_usage': {
                'enhanced_css_selectors': 0,
                'ml_text_analysis': 0,
                'structured_data_ml': 0
            }
        },
        
        # Allergen detection metrics
        'allergen_metrics': {
            'total_allergen_detections': 0,
            'allergen_distribution': {},
            'items_with_allergens': 0,
            'allergen_coverage_rate': 0,
            'risk_level_distribution': {
                'high': 0,
                'medium': 0,
                'low': 0
            }
        },
        
        # Quality metrics
        'quality_metrics': {
            'items_with_prices': 0,
            'items_with_descriptions': 0,
            'items_with_categories': 0,
            'items_with_dietary_tags': 0,
            'avg_item_name_length': 0,
            'price_coverage_avg': 0
        },
        
        # Performance metrics
        'performance_metrics': {
            'fastest_scrape': float('inf'),
            'slowest_scrape': 0,
            'total_test_time': 0,
            'avg_items_per_minute': 0
        },
        
        'error_analysis': {},
        'detailed_results': []
    }
    
    start_time = time.time()
    
    try:
        # Setup browser
        if not await scraper.setup_browser():
            print("❌ Failed to setup ML scraper browser")
            return results
        
        print(f"\n🔄 Testing {len(test_restaurants)} restaurants with ML enhancement...\n")
        
        # Test each restaurant
        for i, restaurant in enumerate(test_restaurants, 1):
            restaurant_name = restaurant.get('name', f'Restaurant {i}')
            url = restaurant.get('url', '')
            
            print(f"[{i:2d}/{len(test_restaurants)}] 🍽️  Testing: {restaurant_name}")
            print(f"           🌐 URL: {url}")
            
            # Extract menu items with ML
            result = await scraper.extract_menu_items(url)
            
            # Process results
            processing_time = result.get('processing_time', 0)
            success = result.get('success', False)
            total_items = result.get('total_items', 0)
            extraction_method = result.get('extraction_method', 'unknown')
            ml_features = result.get('ml_features', {})
            
            # Update basic metrics
            if success:
                results['successful_scrapes'] += 1
                results['total_items_extracted'] += total_items
                
                # ML metrics processing
                confidence_scores = ml_features.get('confidence_scores', [])
                if confidence_scores:
                    avg_confidence = sum(confidence_scores) / len(confidence_scores)
                    results['ml_metrics']['avg_confidence_score'] += avg_confidence
                    
                    # Confidence distribution
                    for score in confidence_scores:
                        if score > 0.7:
                            results['ml_metrics']['confidence_score_distribution']['high'] += 1
                        elif score > 0.4:
                            results['ml_metrics']['confidence_score_distribution']['medium'] += 1
                        else:
                            results['ml_metrics']['confidence_score_distribution']['low'] += 1
                
                # Extraction strategy tracking
                strategies = ml_features.get('extraction_strategies_used', [])
                for strategy in strategies:
                    results['ml_metrics']['extraction_strategy_success'][strategy] = \
                        results['ml_metrics']['extraction_strategy_success'].get(strategy, 0) + 1
                    results['ml_metrics']['ml_features_usage'][strategy] = \
                        results['ml_metrics']['ml_features_usage'].get(strategy, 0) + 1
                
                # Quality assessment
                quality_score = ml_features.get('quality_assessment', 0)
                results['ml_metrics']['quality_assessment_avg'] += quality_score
                
                # Allergen analysis
                allergen_summary = result.get('allergen_summary', {})
                for allergen, count in allergen_summary.items():
                    results['allergen_metrics']['allergen_distribution'][allergen] = \
                        results['allergen_metrics']['allergen_distribution'].get(allergen, 0) + count
                    results['allergen_metrics']['total_allergen_detections'] += count
                
                # Item-level analysis
                items = result.get('items', [])
                items_with_allergens = 0
                risk_levels = {'high': 0, 'medium': 0, 'low': 0}
                
                for item in items:
                    # Quality metrics
                    if item.get('price'):
                        results['quality_metrics']['items_with_prices'] += 1
                    if item.get('description') and len(item['description']) > 5:
                        results['quality_metrics']['items_with_descriptions'] += 1
                    if item.get('category'):
                        results['quality_metrics']['items_with_categories'] += 1
                    if item.get('dietary_tags'):
                        results['quality_metrics']['items_with_dietary_tags'] += 1
                    
                    # Allergen metrics
                    if item.get('allergens'):
                        items_with_allergens += 1
                        risk_level = item.get('allergen_risk_level', 'low')
                        risk_levels[risk_level] = risk_levels.get(risk_level, 0) + 1
                    
                    # Name length
                    name_length = len(item.get('name', ''))
                    if name_length > 0:
                        current_avg = results['quality_metrics']['avg_item_name_length']
                        total_items_so_far = results['total_items_extracted']
                        results['quality_metrics']['avg_item_name_length'] = \
                            (current_avg * (total_items_so_far - 1) + name_length) / total_items_so_far
                
                results['allergen_metrics']['items_with_allergens'] += items_with_allergens
                for level, count in risk_levels.items():
                    results['allergen_metrics']['risk_level_distribution'][level] += count
                
                # Price coverage
                price_coverage = result.get('price_coverage', 0)
                results['quality_metrics']['price_coverage_avg'] += price_coverage
                
                print(f"           ✅ Success: {total_items} items extracted")
                print(f"           ⏱️  Time: {processing_time}s")
                print(f"           🔧 Method: {extraction_method}")
                print(f"           🧠 ML Quality: {quality_score:.2f}")
                if confidence_scores:
                    print(f"           📊 Avg Confidence: {avg_confidence:.2f}")
                if allergen_summary:
                    print(f"           🚨 Allergens: {sum(allergen_summary.values())} detected")
                
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
                'ml_features': ml_features,
                'allergen_summary': result.get('allergen_summary', {}),
                'price_coverage': result.get('price_coverage', 0),
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
        
        # ML metrics averages
        results['ml_metrics']['avg_confidence_score'] = round(
            results['ml_metrics']['avg_confidence_score'] / results['successful_scrapes'], 3
        )
        results['ml_metrics']['quality_assessment_avg'] = round(
            results['ml_metrics']['quality_assessment_avg'] / results['successful_scrapes'], 2
        )
        
        # Quality metrics averages
        results['quality_metrics']['price_coverage_avg'] = round(
            results['quality_metrics']['price_coverage_avg'] / results['successful_scrapes'], 1
        )
        
        # Allergen coverage rate
        if results['total_items_extracted'] > 0:
            results['allergen_metrics']['allergen_coverage_rate'] = round(
                (results['allergen_metrics']['items_with_allergens'] / results['total_items_extracted']) * 100, 1
            )
    
    # Calculate average processing time
    if results['detailed_results']:
        total_processing_time = sum(r['processing_time'] for r in results['detailed_results'])
        results['avg_processing_time'] = round(
            total_processing_time / len(results['detailed_results']), 2
        )
        
        # Items per minute
        if total_test_time > 0:
            results['performance_metrics']['avg_items_per_minute'] = round(
                (results['total_items_extracted'] / total_test_time) * 60, 1
            )
    
    # Fix infinite value for fastest scrape
    if results['performance_metrics']['fastest_scrape'] == float('inf'):
        results['performance_metrics']['fastest_scrape'] = 0
    
    return results

def save_results(results: Dict[str, Any], filename: str = None) -> str:
    """Save test results to JSON file"""
    if not filename:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'final_ml_test_results_{timestamp}.json'
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"📁 Results saved to: {filename}")
        return filename
    except Exception as e:
        print(f"❌ Failed to save results: {e}")
        return ""

def print_comprehensive_ml_summary(results: Dict[str, Any]):
    """Print comprehensive ML test summary"""
    print("\n" + "=" * 80)
    print("🤖 FINAL ML-ENHANCED SCRAPER TEST RESULTS SUMMARY")
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
        print(f"   🎉 TARGET ACHIEVED! ({results['success_rate']}% >= {target_success_rate}%)")
    else:
        gap = target_success_rate - results['success_rate']
        print(f"   ⚠️  Target missed by {gap}% ({results['success_rate']}% < {target_success_rate}%)")
    
    # ML-specific metrics
    ml_metrics = results['ml_metrics']
    print(f"\n🧠 ML ENHANCEMENT METRICS:")
    print(f"   📊 Avg Confidence Score: {ml_metrics['avg_confidence_score']:.3f}")
    print(f"   🎯 Quality Assessment: {ml_metrics['quality_assessment_avg']:.2f}")
    
    # Confidence distribution
    conf_dist = ml_metrics['confidence_score_distribution']
    total_conf_items = sum(conf_dist.values())
    if total_conf_items > 0:
        print(f"   📈 Confidence Distribution:")
        print(f"      • High (>0.7): {conf_dist['high']} ({conf_dist['high']/total_conf_items*100:.1f}%)")
        print(f"      • Medium (0.4-0.7): {conf_dist['medium']} ({conf_dist['medium']/total_conf_items*100:.1f}%)")
        print(f"      • Low (<0.4): {conf_dist['low']} ({conf_dist['low']/total_conf_items*100:.1f}%)")
    
    # Extraction strategies
    if ml_metrics['extraction_strategy_success']:
        print(f"   🔧 Successful Extraction Strategies:")
        for strategy, count in ml_metrics['extraction_strategy_success'].items():
            print(f"      • {strategy}: {count} successes")
    
    # Allergen detection metrics
    allergen_metrics = results['allergen_metrics']
    print(f"\n🚨 ALLERGEN DETECTION METRICS:")
    print(f"   🔍 Total Detections: {allergen_metrics['total_allergen_detections']}")
    print(f"   📊 Items with Allergens: {allergen_metrics['items_with_allergens']}")
    print(f"   📈 Allergen Coverage: {allergen_metrics['allergen_coverage_rate']}%")
    
    # Allergen distribution
    if allergen_metrics['allergen_distribution']:
        print(f"   🏷️  Allergen Types Detected:")
        for allergen, count in sorted(allergen_metrics['allergen_distribution'].items(), key=lambda x: x[1], reverse=True):
            print(f"      • {allergen}: {count} occurrences")
    
    # Risk level distribution
    risk_dist = allergen_metrics['risk_level_distribution']
    total_risk_items = sum(risk_dist.values())
    if total_risk_items > 0:
        print(f"   ⚠️  Risk Level Distribution:")
        print(f"      • High Risk: {risk_dist['high']} ({risk_dist['high']/total_risk_items*100:.1f}%)")
        print(f"      • Medium Risk: {risk_dist['medium']} ({risk_dist['medium']/total_risk_items*100:.1f}%)")
        print(f"      • Low Risk: {risk_dist['low']} ({risk_dist['low']/total_risk_items*100:.1f}%)")
    
    # Quality metrics
    quality_metrics = results['quality_metrics']
    print(f"\n📈 QUALITY METRICS:")
    total_items = results['total_items_extracted']
    if total_items > 0:
        price_pct = (quality_metrics['items_with_prices'] / total_items) * 100
        desc_pct = (quality_metrics['items_with_descriptions'] / total_items) * 100
        cat_pct = (quality_metrics['items_with_categories'] / total_items) * 100
        diet_pct = (quality_metrics['items_with_dietary_tags'] / total_items) * 100
        
        print(f"   💰 Items with prices: {quality_metrics['items_with_prices']} ({price_pct:.1f}%)")
        print(f"   📝 Items with descriptions: {quality_metrics['items_with_descriptions']} ({desc_pct:.1f}%)")
        print(f"   🏷️  Items with categories: {quality_metrics['items_with_categories']} ({cat_pct:.1f}%)")
        print(f"   🥗 Items with dietary tags: {quality_metrics['items_with_dietary_tags']} ({diet_pct:.1f}%)")
        print(f"   📏 Avg name length: {quality_metrics['avg_item_name_length']:.1f} chars")
        print(f"   💰 Avg price coverage: {quality_metrics['price_coverage_avg']:.1f}%")
    
    # Performance metrics
    perf_metrics = results['performance_metrics']
    print(f"\n⚡ PERFORMANCE METRICS:")
    print(f"   🏃 Fastest scrape: {perf_metrics['fastest_scrape']}s")
    print(f"   🐌 Slowest scrape: {perf_metrics['slowest_scrape']}s")
    print(f"   🕐 Total test time: {perf_metrics['total_test_time']}s")
    print(f"   📊 Items per minute: {perf_metrics['avg_items_per_minute']}")
    
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
        'Final Optimized': 40.0,
        'Production Scraper': 0.0,
        'ML Enhanced': 0.0,
        'Enhanced Allergen': 0.0
    }
    
    current_rate = results['success_rate']
    best_previous = max(previous_results.values())
    
    for version, rate in previous_results.items():
        print(f"   {version}: {rate}% success rate")
    
    print(f"   Final ML-Enhanced: {current_rate}% success rate")
    
    if current_rate > best_previous:
        improvement = current_rate - best_previous
        print(f"   🎉 NEW BEST! Improved by {improvement}% over previous best")
    elif current_rate == best_previous:
        print(f"   🤝 MATCHES best previous performance")
    else:
        decline = best_previous - current_rate
        print(f"   ⚠️  Final ML is {decline}% below best previous performance")
    
    # ML-specific recommendations
    print(f"\n🚀 ML-ENHANCED NEXT STEPS:")
    if results['success_rate'] >= 50:
        print(f"   • 🎯 TARGET ACHIEVED! Deploy ML-enhanced scraper")
        print(f"   • 🧠 Fine-tune ML models with collected data")
        print(f"   • 📈 Implement continuous learning pipeline")
    else:
        print(f"   • 🔍 Analyze ML confidence patterns for improvement")
        print(f"   • 🧠 Enhance allergen detection algorithms")
        print(f"   • 📊 Collect more training data for ML models")
        print(f"   • 🎯 Implement ensemble extraction methods")
    
    print(f"   • 🚨 Expand allergen database with user feedback")
    print(f"   • 📱 Integrate with AllergySavvy-style ML pipeline")
    print(f"   • 🔄 Implement real-time model updates")
    
    print("\n" + "=" * 80)
    print("✅ Final ML-Enhanced test completed successfully!")

async def main():
    """Main test execution"""
    # Run comprehensive ML test
    results = await test_final_ml_scraper(sample_size=20)
    
    if results:
        # Print summary
        print_comprehensive_ml_summary(results)
        
        # Save results
        filename = save_results(results, 'final_ml_test_results_n20.json')
        print(f"📁 Detailed results saved to: {filename}")
    else:
        print("❌ ML test failed to complete")

if __name__ == "__main__":
    asyncio.run(main())