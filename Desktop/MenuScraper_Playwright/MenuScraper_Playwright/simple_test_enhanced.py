#!/usr/bin/env python3
"""
Simple test for enhanced production scraper
"""

import asyncio
import sys
from production_menu_scraper import ProductionMenuScraper

async def simple_test():
    print("Testing Enhanced Production Scraper")
    print("=" * 40)
    
    # Test OCR dependencies
    print("\n1. Checking OCR dependencies:")
    try:
        import easyocr
        print("   ✅ EasyOCR available")
    except ImportError:
        print("   ❌ EasyOCR not available")
    
    try:
        import cv2
        print("   ✅ OpenCV available")
    except ImportError:
        print("   ❌ OpenCV not available")
    
    # Test scraper initialization
    print("\n2. Testing scraper initialization:")
    try:
        scraper = ProductionMenuScraper(headless=True, ocr_enabled=True)
        print("   ✅ Scraper initialized successfully")
        
        # Test browser setup
        print("\n3. Testing browser setup:")
        if await scraper.setup_browser():
            print("   ✅ Browser setup successful")
            
            # Test website discovery method
            print("\n4. Testing website discovery method:")
            if hasattr(scraper, '_find_restaurant_website'):
                print("   ✅ Enhanced website discovery method available")
            else:
                print("   ❌ Enhanced website discovery method missing")
            
            # Test OCR method
            print("\n5. Testing OCR method:")
            if hasattr(scraper, '_process_image_with_ocr'):
                print("   ✅ Enhanced OCR processing method available")
            else:
                print("   ❌ Enhanced OCR processing method missing")
            
            await scraper.cleanup()
            print("\n✅ All tests completed successfully")
        else:
            print("   ❌ Browser setup failed")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(simple_test())