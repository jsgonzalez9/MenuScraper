#!/usr/bin/env python3
"""
Proxy-Enhanced Menu Scraper Test
Demonstrates the enhanced scraper with proxy support
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

# Import the enhanced production scraper
try:
    from enhanced_website_menu_scraper import EnhancedWebsiteMenuScraper
except ImportError:
    print("Error: Could not import EnhancedWebsiteMenuScraper")
    exit(1)

async def test_proxy_enhanced_scraper(proxy_list=None):
    """
    Test the enhanced scraper with proxy support
    
    Args:
        proxy_list: List of proxy URLs (e.g., ['http://proxy1:port', 'http://proxy2:port'])
    """
    print("=== Proxy-Enhanced Menu Scraper Test ===")
    
    # Test restaurants
    test_restaurants = [
        {
            "name": "Alinea Chicago",
            "direct_url": "https://www.alinearestaurant.com"
        },
        {
            "name": "Girl & the Goat Chicago", 
            "direct_url": "https://www.girlandthegoat.com"
        },
        {
            "name": "Au Cheval Chicago",
            "direct_url": "https://www.aucheval.com"
        }
    ]
    
    results = {
        "test_time": datetime.now().isoformat(),
        "proxy_enhanced_test": True,
        "proxy_list_provided": proxy_list is not None,
        "proxy_count": len(proxy_list) if proxy_list else 0,
        "test_results": []
    }
    
    # Test 1: No proxy (baseline)
    print("\n1. Testing baseline (no proxy)...")
    await test_single_configuration(None, test_restaurants[0], results, "baseline_no_proxy")
    
    # Test 2: With proxies (if provided)
    if proxy_list:
        for i, proxy in enumerate(proxy_list[:2]):  # Test first 2 proxies
            print(f"\n{i+2}. Testing with proxy {i+1}: {proxy}...")
            restaurant = test_restaurants[min(i+1, len(test_restaurants)-1)]
            await test_single_configuration(proxy, restaurant, results, f"proxy_{i+1}_test")
    else:
        print("\n2. No proxies provided - skipping proxy tests")
        print("   To test with proxies, provide a list of proxy URLs")
    
    # Summary
    print("\n=== Test Summary ===")
    print(f"Tests completed: {len(results['test_results'])}")
    
    successful_tests = sum(1 for test in results['test_results'] if test.get('success', False))
    print(f"Successful tests: {successful_tests}")
    
    if proxy_list:
        proxy_tests = [test for test in results['test_results'] if 'proxy' in test.get('test_type', '')]
        successful_proxy_tests = sum(1 for test in proxy_tests if test.get('success', False))
        print(f"Successful proxy tests: {successful_proxy_tests}/{len(proxy_tests)}")
    
    # Save results
    output_file = f"proxy_enhanced_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: {output_file}")
    
    return results

async def test_single_configuration(proxy, restaurant, results, test_type):
    """
    Test a single proxy configuration
    """
    try:
        # Initialize scraper with or without proxy
        if proxy:
            scraper = EnhancedWebsiteMenuScraper(proxy=proxy, headless=True, timeout=30000)
            print(f"   🌐 Using proxy: {proxy}")
        else:
            scraper = EnhancedWebsiteMenuScraper(headless=True, timeout=30000)
            print(f"   🌐 No proxy (direct connection)")
        
        # Test scraping
        test_result = await scraper.scrape_restaurant_menu(
            restaurant_name=restaurant["name"],
            direct_url=restaurant["direct_url"]
        )
        
        # Store result
        result_data = {
            "test_type": test_type,
            "restaurant": restaurant["name"],
            "url": restaurant["direct_url"],
            "proxy_used": proxy,
            "success": test_result.get("success", False),
            "total_items": test_result.get("total_items", 0),
            "processing_time": test_result.get("processing_time", 0),
            "error": test_result.get("error"),
            "extraction_method": test_result.get("extraction_method")
        }
        
        results["test_results"].append(result_data)
        
        # Print result
        if test_result.get("success"):
            print(f"   ✅ Success: {test_result.get('total_items', 0)} items extracted")
            print(f"   ⏱️  Processing time: {test_result.get('processing_time', 0):.2f}s")
        else:
            print(f"   ❌ Failed: {test_result.get('error', 'Unknown error')}")
            print(f"   ⏱️  Processing time: {test_result.get('processing_time', 0):.2f}s")
            
    except Exception as e:
        print(f"   💥 Exception: {str(e)}")
        results["test_results"].append({
            "test_type": test_type,
            "restaurant": restaurant["name"],
            "url": restaurant["direct_url"],
            "proxy_used": proxy,
            "success": False,
            "total_items": 0,
            "processing_time": 0,
            "error": f"Exception: {str(e)}",
            "extraction_method": None
        })

async def demo_proxy_rotation():
    """
    Demonstrate proxy rotation capabilities
    """
    print("\n=== Proxy Rotation Demo ===")
    print("This demonstrates how to use different proxies for different requests")
    print("Useful for avoiding rate limits and IP blocks\n")
    
    # Example proxy list (replace with real proxies)
    example_proxies = [
        "http://proxy1.example.com:8080",
        "http://proxy2.example.com:8080", 
        "http://proxy3.example.com:8080"
    ]
    
    print("Example proxy rotation pattern:")
    for i, proxy in enumerate(example_proxies):
        print(f"   Request {i+1}: {proxy}")
    
    print("\n💡 Benefits of proxy rotation:")
    print("   • Avoid IP-based rate limiting")
    print("   • Distribute load across multiple IPs")
    print("   • Reduce chance of being blocked")
    print("   • Enable higher throughput scraping")
    
    print("\n🔧 Implementation ready:")
    print("   • Proxy parameter in scraper constructor")
    print("   • Easy to switch between proxies")
    print("   • Error handling for proxy failures")
    print("   • Fallback to direct connection if needed")

if __name__ == "__main__":
    print("🚀 Starting Proxy-Enhanced Menu Scraper Test")
    print("\nThis test will verify proxy functionality with the enhanced scraper.")
    print("To test with real proxies, modify the proxy_list variable below.\n")
    
    # Example: Replace with your actual proxy list
    # proxy_list = [
    #     "http://username:password@proxy1.example.com:8080",
    #     "http://username:password@proxy2.example.com:8080"
    # ]
    proxy_list = None  # Set to None to test without proxies
    
    # Run the test
    asyncio.run(test_proxy_enhanced_scraper(proxy_list))
    
    # Show proxy rotation demo
    asyncio.run(demo_proxy_rotation())