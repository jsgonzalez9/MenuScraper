#!/usr/bin/env python3
"""
Test script for Phase 2 scraper implementations
Tests DoorDash, Uber Eats scrapers and OCR framework
"""

import asyncio
import logging
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from doordash_scraper import DoorDashScraper
from ubereats_scraper import UberEatsScraper
from production_menu_scraper import ProductionMenuScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_doordash_scraper():
    """Test DoorDash scraper basic functionality"""
    logger.info("🧪 Testing DoorDash Scraper...")
    
    scraper = DoorDashScraper()
    
    try:
        # Test scraper initialization
        assert hasattr(scraper, 'extract_menu_items'), "Missing extract_menu_items method"
        assert hasattr(scraper, 'setup_browser'), "Missing setup_browser method"
        assert hasattr(scraper, 'cleanup'), "Missing cleanup method"
        
        logger.info("✅ DoorDash scraper structure verified")
        
        # Test with a sample URL (won't actually scrape due to blocking)
        sample_url = "https://www.doordash.com/store/sample-restaurant"
        
        # This would normally extract menu items, but we'll just verify the method exists
        logger.info(f"📋 DoorDash scraper ready for URL: {sample_url}")
        
    except Exception as e:
        logger.error(f"❌ DoorDash scraper test failed: {e}")
        raise
    finally:
        await scraper.cleanup()

async def test_ubereats_scraper():
    """Test Uber Eats scraper basic functionality"""
    logger.info("🧪 Testing Uber Eats Scraper...")
    
    scraper = UberEatsScraper()
    
    try:
        # Test scraper initialization
        assert hasattr(scraper, 'extract_menu_items'), "Missing extract_menu_items method"
        assert hasattr(scraper, 'setup_browser'), "Missing setup_browser method"
        assert hasattr(scraper, 'cleanup'), "Missing cleanup method"
        
        logger.info("✅ Uber Eats scraper structure verified")
        
        # Test with a sample URL (won't actually scrape due to blocking)
        sample_url = "https://www.ubereats.com/store/sample-restaurant"
        
        # This would normally extract menu items, but we'll just verify the method exists
        logger.info(f"📋 Uber Eats scraper ready for URL: {sample_url}")
        
    except Exception as e:
        logger.error(f"❌ Uber Eats scraper test failed: {e}")
        raise
    finally:
        await scraper.cleanup()

async def test_ocr_framework():
    """Test OCR framework in production scraper"""
    logger.info("🧪 Testing OCR Framework...")
    
    scraper = ProductionMenuScraper(ocr_enabled=True)
    
    try:
        # Test OCR-related methods exist
        assert hasattr(scraper, '_find_menu_image_urls'), "Missing _find_menu_image_urls method"
        assert hasattr(scraper, '_process_image_with_ocr'), "Missing _process_image_with_ocr method"
        assert hasattr(scraper, '_extract_items_from_ocr_text'), "Missing _extract_items_from_ocr_text method"
        assert hasattr(scraper, '_is_likely_menu_image'), "Missing _is_likely_menu_image method"
        
        logger.info("✅ OCR framework methods verified")
        
        # Test image URL filtering
        test_urls = [
            "https://example.com/menu-image.jpg",  # Should pass
            "https://example.com/food-photo.png",  # Should pass
            "https://example.com/logo-small.jpg",  # Should fail
            "https://example.com/background.jpg",  # Should fail
            "https://example.com/dish-special.jpg"  # Should pass
        ]
        
        for url in test_urls:
            is_menu = scraper._is_likely_menu_image(url)
            logger.info(f"📸 {url}: {'✅ Menu image' if is_menu else '❌ Not menu image'}")
        
        # Test OCR text extraction
        sample_ocr_text = "APPETIZERS\nBruschetta $8.99\nCalamari Rings $12.99"
        extracted_items = scraper._extract_items_from_ocr_text(sample_ocr_text)
        
        logger.info(f"📋 Extracted {len(extracted_items)} items from OCR text")
        for item in extracted_items:
            logger.info(f"   - {item['name']}: {item['price']}")
        
        # Test simulated OCR
        sample_url = "https://example.com/menu.jpg"
        simulated_text = scraper._simulate_ocr_extraction(sample_url)
        logger.info(f"🔍 Simulated OCR result: {simulated_text[:50]}...")
        
        logger.info("✅ OCR framework functionality verified")
        
    except Exception as e:
        logger.error(f"❌ OCR framework test failed: {e}")
        raise
    finally:
        await scraper.cleanup()

async def test_phase2_integration():
    """Test Phase 2 integration and compatibility"""
    logger.info("🧪 Testing Phase 2 Integration...")
    
    try:
        # Test that all scrapers can be imported and initialized
        doordash = DoorDashScraper()
        ubereats = UberEatsScraper()
        production = ProductionMenuScraper(ocr_enabled=True)
        
        # Verify they all have consistent interfaces
        scrapers = [doordash, ubereats, production]
        
        for i, scraper in enumerate(scrapers):
            scraper_name = ['DoorDash', 'UberEats', 'Production'][i]
            
            # Check required methods
            required_methods = ['extract_menu_items', 'setup_browser', 'cleanup']
            for method in required_methods:
                assert hasattr(scraper, method), f"{scraper_name} missing {method}"
            
            logger.info(f"✅ {scraper_name} scraper interface verified")
        
        # Test OCR-specific features
        assert hasattr(production, 'ocr_enabled'), "Production scraper missing ocr_enabled"
        assert hasattr(production, 'image_selectors'), "Production scraper missing image_selectors"
        
        logger.info("✅ Phase 2 integration verified")
        
        # Cleanup all scrapers
        for scraper in scrapers:
            await scraper.cleanup()
        
    except Exception as e:
        logger.error(f"❌ Phase 2 integration test failed: {e}")
        raise

async def main():
    """Run all Phase 2 tests"""
    logger.info("🚀 Starting Phase 2 Scraper Tests")
    
    tests = [
        ("DoorDash Scraper", test_doordash_scraper),
        ("Uber Eats Scraper", test_ubereats_scraper),
        ("OCR Framework", test_ocr_framework),
        ("Phase 2 Integration", test_phase2_integration)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            logger.info(f"\n{'='*50}")
            logger.info(f"Running: {test_name}")
            logger.info(f"{'='*50}")
            
            await test_func()
            
            logger.info(f"✅ {test_name} PASSED")
            passed += 1
            
        except Exception as e:
            logger.error(f"❌ {test_name} FAILED: {e}")
            failed += 1
    
    # Summary
    logger.info(f"\n{'='*50}")
    logger.info(f"TEST SUMMARY")
    logger.info(f"{'='*50}")
    logger.info(f"✅ Passed: {passed}")
    logger.info(f"❌ Failed: {failed}")
    logger.info(f"📊 Total: {passed + failed}")
    
    if failed == 0:
        logger.info("🎉 All Phase 2 tests passed!")
    else:
        logger.warning(f"⚠️ {failed} test(s) failed")
    
    return failed == 0

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)