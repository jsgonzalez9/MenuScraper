#!/usr/bin/env python3
"""
Test that writes results to a file
"""

import asyncio
import json
from datetime import datetime
from production_menu_scraper import ProductionMenuScraper

async def test_and_write_results():
    results = {
        "test_time": datetime.now().isoformat(),
        "tests": []
    }
    
    # Test 1: Check OCR dependencies
    ocr_test = {"name": "OCR Dependencies", "status": "unknown", "details": {}}
    try:
        import easyocr
        ocr_test["details"]["easyocr"] = "available"
    except ImportError:
        ocr_test["details"]["easyocr"] = "missing"
    
    try:
        import cv2
        ocr_test["details"]["opencv"] = "available"
    except ImportError:
        ocr_test["details"]["opencv"] = "missing"
    
    ocr_test["status"] = "pass" if all(v == "available" for v in ocr_test["details"].values()) else "fail"
    results["tests"].append(ocr_test)
    
    # Test 2: Scraper initialization
    init_test = {"name": "Scraper Initialization", "status": "unknown", "details": {}}
    try:
        scraper = ProductionMenuScraper(headless=True, ocr_enabled=True)
        init_test["status"] = "pass"
        init_test["details"]["initialization"] = "success"
        
        # Test 3: Method availability
        method_test = {"name": "Enhanced Methods", "status": "unknown", "details": {}}
        method_test["details"]["website_discovery"] = "available" if hasattr(scraper, '_find_restaurant_website') else "missing"
        method_test["details"]["ocr_processing"] = "available" if hasattr(scraper, '_process_image_with_ocr') else "missing"
        method_test["status"] = "pass" if all(v == "available" for v in method_test["details"].values()) else "fail"
        results["tests"].append(method_test)
        
        # Test 4: Browser setup
        browser_test = {"name": "Browser Setup", "status": "unknown", "details": {}}
        try:
            if await scraper.setup_browser():
                browser_test["status"] = "pass"
                browser_test["details"]["setup"] = "success"
                await scraper.cleanup()
            else:
                browser_test["status"] = "fail"
                browser_test["details"]["setup"] = "failed"
        except Exception as e:
            browser_test["status"] = "error"
            browser_test["details"]["error"] = str(e)
        
        results["tests"].append(browser_test)
        
    except Exception as e:
        init_test["status"] = "error"
        init_test["details"]["error"] = str(e)
    
    results["tests"].append(init_test)
    
    # Write results to file
    output_file = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # Also write a simple status file
    with open("test_status.txt", 'w') as f:
        f.write(f"Test completed at: {datetime.now()}\n")
        f.write(f"Results saved to: {output_file}\n")
        for test in results["tests"]:
            f.write(f"{test['name']}: {test['status']}\n")

if __name__ == "__main__":
    asyncio.run(test_and_write_results())