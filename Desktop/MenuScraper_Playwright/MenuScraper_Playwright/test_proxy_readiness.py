#!/usr/bin/env python3
"""
Proxy Readiness Test Script
Tests the enhanced production scraper's proxy configuration capabilities
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

async def test_proxy_configuration():
    """
    Test proxy configuration capabilities without actual proxies
    """
    print("=== Proxy Readiness Test ===")
    
    # Test data
    test_restaurants = [
        {
            "name": "Alinea Chicago",
            "direct_url": "https://www.alinearestaurant.com"
        },
        {
            "name": "Girl & the Goat Chicago", 
            "direct_url": "https://www.girlandthegoat.com"
        }
    ]
    
    results = {
        "test_time": datetime.now().isoformat(),
        "proxy_configuration_test": True,
        "tests_performed": [
            "Proxy parameter acceptance",
            "Browser launch with proxy settings",
            "Navigation with proxy configuration",
            "Error handling for proxy issues"
        ],
        "test_results": []
    }
    
    # Test 1: No proxy (baseline)
    print("\n1. Testing baseline (no proxy)...")
    try:
        scraper = EnhancedWebsiteMenuScraper()
        test_result = await scraper.scrape_restaurant_menu(
            restaurant_name=test_restaurants[0]["name"],
            direct_url=test_restaurants[0]["direct_url"]
        )
        
        results["test_results"].append({
            "test_type": "baseline_no_proxy",
            "restaurant": test_restaurants[0]["name"],
            "success": test_result.get("success", False),
            "error": test_result.get("error", None),
            "processing_time": test_result.get("processing_time", 0)
        })
        
        print(f"   Result: {'Success' if test_result.get('success') else 'Failed'}")
        if test_result.get("error"):
            print(f"   Error: {test_result['error']}")
            
    except Exception as e:
        print(f"   Exception: {str(e)}")
        results["test_results"].append({
            "test_type": "baseline_no_proxy",
            "restaurant": test_restaurants[0]["name"],
            "success": False,
            "error": f"Exception: {str(e)}",
            "processing_time": 0
        })
    
    # Test 2: Invalid proxy (error handling)
    print("\n2. Testing invalid proxy handling...")
    try:
        # Test with invalid proxy to check error handling
        invalid_proxy = "http://invalid-proxy:8080"
        scraper = EnhancedWebsiteMenuScraper(proxy=invalid_proxy)
        
        test_result = await scraper.scrape_restaurant_menu(
            restaurant_name=test_restaurants[1]["name"],
            direct_url=test_restaurants[1]["direct_url"]
        )
        
        results["test_results"].append({
            "test_type": "invalid_proxy_test",
            "restaurant": test_restaurants[1]["name"],
            "proxy_used": invalid_proxy,
            "success": test_result.get("success", False),
            "error": test_result.get("error", None),
            "processing_time": test_result.get("processing_time", 0)
        })
        
        print(f"   Result: {'Success' if test_result.get('success') else 'Failed (Expected)'}")
        if test_result.get("error"):
            print(f"   Error: {test_result['error']}")
            
    except Exception as e:
        print(f"   Exception (Expected): {str(e)}")
        results["test_results"].append({
            "test_type": "invalid_proxy_test",
            "restaurant": test_restaurants[1]["name"],
            "proxy_used": invalid_proxy,
            "success": False,
            "error": f"Exception: {str(e)}",
            "processing_time": 0
        })
    
    # Test 3: Check if scraper accepts proxy parameter
    print("\n3. Testing proxy parameter acceptance...")
    try:
        # Just test initialization with proxy parameter
        test_proxy = "http://test-proxy:8080"
        scraper = EnhancedWebsiteMenuScraper(proxy=test_proxy)
        
        # Check if proxy is stored/accessible
        proxy_accepted = hasattr(scraper, 'proxy') or 'proxy' in str(scraper.__dict__)
        
        results["proxy_parameter_accepted"] = proxy_accepted
        print(f"   Proxy parameter accepted: {proxy_accepted}")
        
    except Exception as e:
        print(f"   Error initializing with proxy: {str(e)}")
        results["proxy_parameter_accepted"] = False
        results["proxy_init_error"] = str(e)
    
    # Summary
    print("\n=== Test Summary ===")
    print(f"Tests completed: {len(results['test_results'])}")
    
    successful_tests = sum(1 for test in results['test_results'] if test.get('success', False))
    print(f"Successful tests: {successful_tests}")
    
    proxy_ready = results.get("proxy_parameter_accepted", False)
    print(f"Proxy configuration ready: {proxy_ready}")
    
    # Save results
    output_file = f"proxy_readiness_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: {output_file}")
    
    return results

if __name__ == "__main__":
    asyncio.run(test_proxy_configuration())