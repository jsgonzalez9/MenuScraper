#!/usr/bin/env python3
"""
Test Enhanced Production Menu Scraper
Tests the new features: enhanced website discovery and EasyOCR integration
"""

import asyncio
import json
from pathlib import Path
from production_menu_scraper import ProductionMenuScraper

async def test_enhanced_features():
    """Test the enhanced production scraper features"""
    print("🧪 TESTING ENHANCED PRODUCTION SCRAPER")
    print("=" * 50)
    
    # Test restaurants
    test_restaurants = [
        "Alinea Chicago",
        "Girl & the Goat Chicago", 
        "Au Cheval Chicago"
    ]
    
    scraper = ProductionMenuScraper(headless=True, ocr_enabled=True)
    
    try:
        # Setup browser
        if not await scraper.setup_browser():
            print("❌ Failed to setup browser")
            return
        
        results = []
        
        for restaurant_name in test_restaurants:
            print(f"\n🔍 Testing: {restaurant_name}")
            print("-" * 30)
            
            # Test enhanced website discovery
            print("1. Testing enhanced website discovery...")
            try:
                website_url = await scraper._find_restaurant_website(restaurant_name)
                if website_url:
                    print(f"   ✅ Found website: {website_url}")
                    
                    # Test menu extraction with OCR
                    print("2. Testing menu extraction with OCR support...")
                    result = await scraper.extract_menu_items(website_url)
                    
                    print(f"   Success: {result['success']}")
                    print(f"   Items found: {result['total_items']}")
                    print(f"   Extraction method: {result['extraction_method']}")
                    print(f"   Processing time: {result['processing_time']}s")
                    print(f"   Menu images found: {len(result['menu_image_urls'])}")
                    print(f"   OCR texts extracted: {len(result['ocr_texts'])}")
                    
                    if result['items']:
                        print("   Sample items:")
                        for i, item in enumerate(result['items'][:3], 1):
                            print(f"     {i}. {item['name']} - {item.get('price', 'No price')}")
                    
                    results.append({
                        'restaurant': restaurant_name,
                        'website_found': True,
                        'website_url': website_url,
                        'extraction_result': result
                    })
                else:
                    print("   ⚠️ No suitable website found")
                    results.append({
                        'restaurant': restaurant_name,
                        'website_found': False,
                        'website_url': None,
                        'extraction_result': None
                    })
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
                results.append({
                    'restaurant': restaurant_name,
                    'website_found': False,
                    'error': str(e)
                })
        
        # Save results
        output_file = f"enhanced_production_test_results_{asyncio.get_event_loop().time():.0f}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📊 SUMMARY")
        print("=" * 20)
        successful_discoveries = sum(1 for r in results if r.get('website_found', False))
        successful_extractions = sum(1 for r in results if r.get('extraction_result') and r.get('extraction_result', {}).get('success', False))
        
        print(f"Restaurants tested: {len(test_restaurants)}")
        print(f"Websites discovered: {successful_discoveries}")
        print(f"Successful extractions: {successful_extractions}")
        print(f"Results saved to: {output_file}")
        
        # Test OCR capabilities
        print(f"\n🔬 OCR CAPABILITY TEST")
        print("=" * 25)
        try:
            import easyocr
            import cv2
            print("✅ EasyOCR available")
            print("✅ OpenCV available")
            print("✅ OCR processing enabled")
        except ImportError as e:
            print(f"⚠️ OCR dependencies missing: {e}")
            print("📝 OCR will use simulation mode")
        
    finally:
        await scraper.cleanup()

if __name__ == "__main__":
    asyncio.run(test_enhanced_features())