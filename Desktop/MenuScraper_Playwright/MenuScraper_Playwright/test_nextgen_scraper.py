#!/usr/bin/env python3
"""
Next-Generation Menu Scraper Test Suite
Comprehensive testing and comparison across all scraper versions
"""

import json
import time
import statistics
from datetime import datetime
from playwright.sync_api import sync_playwright
from nextgen_menu_scraper import NextGenMenuScraper
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_nextgen_scraper(sample_sizes=[15, 30]):
    """Test the next-generation scraper with multiple sample sizes"""
    
    # Load restaurant data
    data_file = "c:\\Users\\cliff\\Desktop\\MenuScraper_Playwright\\MenuScraper_Playwright\\output\\chicago_restaurants_with_menus.json"
    
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        restaurants = data.get('restaurants', [])
        if not restaurants:
            print("❌ No restaurants found in data file")
            return
        
        restaurants_with_urls = [r for r in restaurants if r.get('url')]
        
        print(f"🚀 NEXT-GENERATION MENU SCRAPER TEST SUITE")
        print("=" * 70)
        print(f"📊 Available restaurants: {len(restaurants_with_urls)}")
        print(f"🎯 Target success rate: 50%+")
        print(f"📈 Sample sizes: {sample_sizes}")
        print("\n" + "=" * 70)
        
        scraper = NextGenMenuScraper()
        all_results = {}
        
        for sample_size in sample_sizes:
            print(f"\n🧪 TESTING WITH SAMPLE SIZE: {sample_size}")
            print("-" * 50)
            
            test_restaurants = restaurants_with_urls[:sample_size]
            
            results = {
                'test_info': {
                    'timestamp': datetime.now().isoformat(),
                    'sample_size': sample_size,
                    'scraper_version': 'nextgen_v1',
                    'target_success_rate': '50%+'
                },
                'results': [],
                'summary': {
                    'total_tested': 0,
                    'successful_extractions': 0,
                    'total_items': 0,
                    'ocr_usage': 0,
                    'menu_pages_found': 0,
                    'structured_data_usage': 0,
                    'avg_processing_time': 0,
                    'avg_quality_score': 0,
                    'strategies_distribution': {},
                    'category_distribution': {},
                    'price_extraction_rate': 0
                },
                'performance_metrics': {
                    'success_rate': 0,
                    'avg_items_per_success': 0,
                    'processing_times': [],
                    'quality_scores': [],
                    'confidence_scores': []
                }
            }
            
            processing_times = []
            quality_scores = []
            confidence_scores = []
            category_counts = {}
            strategy_counts = {}
            
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-dev-shm-usage']
                )
                
                try:
                    for i, restaurant in enumerate(test_restaurants, 1):
                        start_time = time.time()
                        
                        print(f"\n🏪 [{i}/{sample_size}] {restaurant.get('name', 'Unknown')}")
                        print(f"🔗 {restaurant.get('url', 'No URL')[:80]}...")
                        
                        page = browser.new_page()
                        
                        try:
                            # Set timeouts
                            page.set_default_timeout(30000)
                            
                            # Test the restaurant
                            menu_data = scraper.nextgen_menu_detection(page, restaurant['url'])
                            
                            processing_time = time.time() - start_time
                            processing_times.append(processing_time)
                            
                            # Compile result
                            restaurant_result = {
                                'restaurant_info': {
                                    'name': restaurant.get('name', 'Unknown'),
                                    'url': restaurant.get('url', ''),
                                    'rating': restaurant.get('rating', 0),
                                    'categories': restaurant.get('categories', [])
                                },
                                'menu_data': menu_data,
                                'processing_time': round(processing_time, 2)
                            }
                            
                            results['results'].append(restaurant_result)
                            
                            # Update summary
                            results['summary']['total_tested'] += 1
                            
                            if menu_data.get('scraping_success', False):
                                results['summary']['successful_extractions'] += 1
                                results['summary']['total_items'] += menu_data.get('total_items', 0)
                                
                                # Track advanced metrics
                                if menu_data.get('ocr_used', False):
                                    results['summary']['ocr_usage'] += 1
                                
                                if menu_data.get('menu_page_found', False):
                                    results['summary']['menu_pages_found'] += 1
                                
                                if 'structured_data' in menu_data.get('extraction_methods', []):
                                    results['summary']['structured_data_usage'] += 1
                                
                                # Quality metrics
                                quality_score = menu_data.get('quality_score', 0)
                                quality_scores.append(quality_score)
                                
                                # Strategy distribution
                                strategies = menu_data.get('strategies_used', 0)
                                strategy_counts[strategies] = strategy_counts.get(strategies, 0) + 1
                                
                                # Category distribution
                                for item in menu_data.get('menu_items', []):
                                    category = item.get('category', 'other')
                                    category_counts[category] = category_counts.get(category, 0) + 1
                                    
                                    # Confidence scores
                                    confidence = item.get('confidence', 0)
                                    confidence_scores.append(confidence)
                                
                                print(f"✅ Success! {menu_data.get('total_items', 0)} items in {processing_time:.1f}s")
                                print(f"   📊 Quality: {quality_score:.2f}, Strategies: {strategies}")
                                
                                # Show improvements
                                improvements = []
                                if menu_data.get('menu_page_found', False):
                                    improvements.append("Menu Page")
                                if menu_data.get('ocr_used', False):
                                    improvements.append("OCR")
                                if 'structured_data' in menu_data.get('extraction_methods', []):
                                    improvements.append("Structured Data")
                                
                                if improvements:
                                    print(f"   🚀 Features: {', '.join(improvements)}")
                                
                                # Show sample items
                                sample_items = menu_data.get('menu_items', [])[:3]
                                for item in sample_items:
                                    name = item.get('name', 'Unknown')
                                    category = item.get('category', 'other')
                                    confidence = item.get('confidence', 0)
                                    price = item.get('price', '')
                                    price_text = f" (${price})" if price else ""
                                    print(f"   📋 {name} [{category}]{price_text} (conf: {confidence:.2f})")
                            else:
                                print(f"❌ No menu items found in {processing_time:.1f}s")
                                if 'error' in menu_data:
                                    print(f"   Error: {menu_data['error']}")
                        
                        except Exception as e:
                            processing_time = time.time() - start_time
                            processing_times.append(processing_time)
                            
                            print(f"❌ Error: {e}")
                            
                            error_result = {
                                'restaurant_info': {
                                    'name': restaurant.get('name', 'Unknown'),
                                    'url': restaurant.get('url', '')
                                },
                                'menu_data': {
                                    'scraping_success': False,
                                    'total_items': 0,
                                    'error': str(e)
                                },
                                'processing_time': round(processing_time, 2)
                            }
                            
                            results['results'].append(error_result)
                            results['summary']['total_tested'] += 1
                        
                        finally:
                            page.close()
                        
                        # Brief pause
                        time.sleep(1)
                
                finally:
                    browser.close()
            
            # Calculate final statistics
            if processing_times:
                results['summary']['avg_processing_time'] = round(statistics.mean(processing_times), 2)
                results['performance_metrics']['processing_times'] = processing_times
            
            if quality_scores:
                results['summary']['avg_quality_score'] = round(statistics.mean(quality_scores), 3)
                results['performance_metrics']['quality_scores'] = quality_scores
            
            if confidence_scores:
                results['performance_metrics']['confidence_scores'] = confidence_scores
            
            # Success rate
            success_rate = 0
            if results['summary']['total_tested'] > 0:
                success_rate = (results['summary']['successful_extractions'] / results['summary']['total_tested']) * 100
            results['performance_metrics']['success_rate'] = round(success_rate, 1)
            
            # Average items per success
            avg_items = 0
            if results['summary']['successful_extractions'] > 0:
                avg_items = results['summary']['total_items'] / results['summary']['successful_extractions']
            results['performance_metrics']['avg_items_per_success'] = round(avg_items, 1)
            
            # Price extraction rate
            total_items = results['summary']['total_items']
            items_with_prices = sum(1 for result in results['results'] 
                                  for item in result.get('menu_data', {}).get('menu_items', []) 
                                  if item.get('price'))
            price_rate = (items_with_prices / total_items * 100) if total_items > 0 else 0
            results['summary']['price_extraction_rate'] = round(price_rate, 1)
            
            # Distributions
            results['summary']['strategies_distribution'] = strategy_counts
            results['summary']['category_distribution'] = category_counts
            
            # Save results
            output_file = f"c:\\Users\\cliff\\Desktop\\MenuScraper_Playwright\\MenuScraper_Playwright\\output\\nextgen_test_results_n{sample_size}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 Results saved to: {output_file}")
            
            # Print summary for this sample size
            print_nextgen_summary(results, sample_size)
            
            all_results[sample_size] = results
        
        # Final comparison
        print_version_comparison(all_results)
        
    except FileNotFoundError:
        print(f"❌ Data file not found: {data_file}")
    except Exception as e:
        print(f"❌ Error: {e}")

def print_nextgen_summary(results, sample_size):
    """Print detailed summary for next-gen scraper"""
    
    summary = results['summary']
    metrics = results['performance_metrics']
    
    print(f"\n📊 NEXT-GEN SCRAPER RESULTS (n={sample_size})")
    print("=" * 60)
    
    # Core metrics
    print(f"🎯 Success Rate: {metrics['success_rate']}% ({summary['successful_extractions']}/{summary['total_tested']})")
    print(f"📋 Total Menu Items: {summary['total_items']}")
    print(f"📈 Avg Items per Success: {metrics['avg_items_per_success']}")
    print(f"⏱️ Avg Processing Time: {summary['avg_processing_time']}s")
    print(f"🏆 Avg Quality Score: {summary['avg_quality_score']}")
    
    # Advanced features
    print(f"\n🚀 ADVANCED FEATURES")
    print(f"   🔗 Menu Pages Found: {summary['menu_pages_found']} ({summary['menu_pages_found']/summary['total_tested']*100:.1f}%)")
    print(f"   📸 OCR Usage: {summary['ocr_usage']} ({summary['ocr_usage']/summary['total_tested']*100:.1f}%)")
    print(f"   📊 Structured Data: {summary['structured_data_usage']} ({summary['structured_data_usage']/summary['total_tested']*100:.1f}%)")
    print(f"   💰 Price Extraction: {summary['price_extraction_rate']}%")
    
    # Strategy distribution
    if summary['strategies_distribution']:
        print(f"\n📈 STRATEGY USAGE")
        for strategies, count in sorted(summary['strategies_distribution'].items()):
            percentage = (count / summary['successful_extractions']) * 100
            print(f"   {strategies} strategies: {count} restaurants ({percentage:.1f}%)")
    
    # Category distribution (top 5)
    if summary['category_distribution']:
        print(f"\n🍽️ TOP FOOD CATEGORIES")
        sorted_categories = sorted(summary['category_distribution'].items(), key=lambda x: x[1], reverse=True)
        for category, count in sorted_categories[:5]:
            percentage = (count / summary['total_items']) * 100
            print(f"   {category.title()}: {count} items ({percentage:.1f}%)")
    
    # Performance insights
    if metrics['confidence_scores']:
        avg_confidence = statistics.mean(metrics['confidence_scores'])
        print(f"\n📊 QUALITY INSIGHTS")
        print(f"   Average Confidence: {avg_confidence:.3f}")
        print(f"   Quality Score Range: {min(metrics['quality_scores']):.2f} - {max(metrics['quality_scores']):.2f}")
    
    # Success examples
    successful_results = [r for r in results['results'] if r['menu_data'].get('scraping_success', False)]
    if successful_results:
        print(f"\n🏆 TOP PERFORMING EXTRACTIONS")
        # Sort by total items found
        top_results = sorted(successful_results, key=lambda x: x['menu_data']['total_items'], reverse=True)[:3]
        
        for i, result in enumerate(top_results, 1):
            name = result['restaurant_info']['name']
            items_count = result['menu_data']['total_items']
            quality = result['menu_data'].get('quality_score', 0)
            strategies = result['menu_data'].get('strategies_used', 0)
            methods = ', '.join(result['menu_data'].get('extraction_methods', []))
            
            print(f"   {i}. {name}: {items_count} items (quality: {quality:.2f}, {strategies} strategies)")
            print(f"      Methods: {methods}")
            
            # Show sample items
            sample_items = result['menu_data'].get('menu_items', [])[:2]
            for item in sample_items:
                item_name = item.get('name', 'Unknown')
                category = item.get('category', 'other')
                confidence = item.get('confidence', 0)
                price = item.get('price', '')
                price_text = f" (${price})" if price else ""
                print(f"        • {item_name} [{category}]{price_text} (conf: {confidence:.2f})")
    
    print("\n" + "=" * 60)

def print_version_comparison(all_results):
    """Compare next-gen results across sample sizes and with previous versions"""
    
    print(f"\n📈 COMPREHENSIVE SCRAPER COMPARISON")
    print("=" * 80)
    
    # Next-gen results across sample sizes
    print(f"\n🚀 NEXT-GEN SCRAPER SCALING")
    print(f"{'Sample Size':<12} {'Success Rate':<12} {'Avg Items':<10} {'Quality':<8} {'Features'}")
    print("-" * 70)
    
    for sample_size, results in all_results.items():
        metrics = results['performance_metrics']
        summary = results['summary']
        
        features = []
        if summary['menu_pages_found'] > 0:
            features.append(f"Menu:{summary['menu_pages_found']}")
        if summary['ocr_usage'] > 0:
            features.append(f"OCR:{summary['ocr_usage']}")
        if summary['structured_data_usage'] > 0:
            features.append(f"Struct:{summary['structured_data_usage']}")
        
        feature_text = ', '.join(features) if features else 'Basic'
        
        print(f"{sample_size:<12} {metrics['success_rate']:<12}% {metrics['avg_items_per_success']:<10} {summary['avg_quality_score']:<8.2f} {feature_text}")
    
    # Historical comparison
    print(f"\n📊 HISTORICAL PERFORMANCE COMPARISON")
    print(f"{'Version':<20} {'Sample':<8} {'Success Rate':<12} {'Avg Items':<10} {'Key Features'}")
    print("-" * 80)
    
    # Load and compare with previous versions
    versions = [
        {"name": "Enhanced Scraper", "file": "enhanced_scraper_test_results.json", "sample_size": 5},
        {"name": "Advanced Scraper", "file": "advanced_test_results_n10.json", "sample_size": 10},
        {"name": "Improved Scraper", "file": "improved_scraper_test_results.json", "sample_size": 10}
    ]
    
    for version in versions:
        try:
            file_path = f"c:\\Users\\cliff\\Desktop\\MenuScraper_Playwright\\MenuScraper_Playwright\\output\\{version['file']}"
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if 'overall_stats' in data:
                # Advanced scraper format
                success_rate = data['overall_stats'].get('success_rate', 0)
                avg_items = data['overall_stats'].get('avg_items_per_success', 0)
            else:
                # Other formats
                summary = data.get('summary', {})
                total = summary.get('total_tested', 1)
                successful = summary.get('successful_extractions', 0)
                success_rate = (successful / total) * 100 if total > 0 else 0
                avg_items = summary.get('total_items', 0) / successful if successful > 0 else 0
            
            features = []
            if version['name'] == "Enhanced Scraper":
                features = ["Multi-strategy"]
            elif version['name'] == "Advanced Scraper":
                features = ["ML confidence", "Categories"]
            elif version['name'] == "Improved Scraper":
                features = ["Menu nav", "Enhanced OCR"]
            
            print(f"{version['name']:<20} {version['sample_size']:<8} {success_rate:<12.1f} {avg_items:<10.1f} {', '.join(features)}")
            
        except Exception as e:
            print(f"{version['name']:<20} {version['sample_size']:<8} {'Error':<12} {'Error':<10} {str(e)[:20]}")
    
    # Next-gen results
    for sample_size, results in all_results.items():
        metrics = results['performance_metrics']
        features = ["All strategies", "Quality scoring", "Advanced filtering"]
        
        print(f"{'Next-Gen Scraper':<20} {sample_size:<8} {metrics['success_rate']:<12} {metrics['avg_items_per_success']:<10.1f} {', '.join(features)}")
    
    print("\n" + "=" * 80)
    
    # Performance insights
    if all_results:
        largest_sample = max(all_results.keys())
        best_result = all_results[largest_sample]
        
        print(f"\n🎯 ACHIEVEMENT SUMMARY")
        print(f"   ✅ Target Success Rate: 50%+")
        print(f"   📊 Achieved Success Rate: {best_result['performance_metrics']['success_rate']}%")
        print(f"   🏆 Quality Score: {best_result['summary']['avg_quality_score']:.3f}")
        print(f"   🚀 Advanced Features: Menu navigation, OCR, Structured data")
        print(f"   📈 Scalability: Tested up to {largest_sample} restaurants")
        
        if best_result['performance_metrics']['success_rate'] >= 50:
            print(f"   🎉 SUCCESS: Target achieved!")
        else:
            gap = 50 - best_result['performance_metrics']['success_rate']
            print(f"   📈 PROGRESS: {gap:.1f}% gap to target")

def run_quick_demo():
    """Run a quick demo with 5 restaurants"""
    print(f"\n🚀 QUICK NEXT-GEN DEMO (5 restaurants)")
    print("=" * 50)
    
    test_nextgen_scraper([5])

if __name__ == "__main__":
    print("🚀 NEXT-GENERATION MENU SCRAPER TEST SUITE")
    print("=" * 70)
    
    # Run comprehensive tests
    test_nextgen_scraper([15, 30])
    
    print("\n✅ Next-generation scraper testing completed!")
    print("🎯 Target: 50%+ success rate with enhanced quality")