#!/usr/bin/env python3
"""
Phase 2 Demo Script
Demonstrates DoorDash, Uber Eats scrapers and OCR framework capabilities
"""

import asyncio
import logging
from pathlib import Path
import sys
import json

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from doordash_scraper import DoorDashScraper
from ubereats_scraper import UberEatsScraper
from production_menu_scraper import ProductionMenuScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def demo_doordash_scraper():
    """Demonstrate DoorDash scraper capabilities"""
    logger.info("\n🚀 DoorDash Scraper Demo")
    logger.info("=" * 40)
    
    scraper = DoorDashScraper()
    
    try:
        # Show scraper configuration
        logger.info(f"📱 Mobile User Agent: {scraper.mobile_user_agent[:50]}...")
        logger.info(f"🎯 Menu Selectors: {len(scraper.menu_selectors)} configured")
        logger.info(f"💰 Price Patterns: {len(scraper.price_patterns)} configured")
        
        # Sample URLs for demonstration (won't actually scrape due to blocking)
        sample_urls = [
            "https://www.doordash.com/store/mcdonalds",
            "https://www.doordash.com/store/subway",
            "https://www.doordash.com/store/pizza-hut"
        ]
        
        logger.info("\n📋 Ready to scrape DoorDash restaurants:")
        for i, url in enumerate(sample_urls, 1):
            logger.info(f"   {i}. {url}")
        
        logger.info("\n✨ DoorDash scraper features:")
        logger.info("   • Mobile-optimized browser setup")
        logger.info("   • DoorDash-specific selectors")
        logger.info("   • Modal and popup handling")
        logger.info("   • Infinite scroll support")
        logger.info("   • Price extraction patterns")
        
    except Exception as e:
        logger.error(f"❌ DoorDash demo failed: {e}")
    finally:
        await scraper.cleanup()

async def demo_ubereats_scraper():
    """Demonstrate Uber Eats scraper capabilities"""
    logger.info("\n🚀 Uber Eats Scraper Demo")
    logger.info("=" * 40)
    
    scraper = UberEatsScraper()
    
    try:
        # Show scraper configuration
        logger.info(f"🖥️ Desktop User Agent: {scraper.desktop_user_agent[:50]}...")
        logger.info(f"🎯 Menu Selectors: {len(scraper.menu_selectors)} configured")
        logger.info(f"💰 Price Patterns: {len(scraper.price_patterns)} configured")
        
        # Sample URLs for demonstration
        sample_urls = [
            "https://www.ubereats.com/store/starbucks",
            "https://www.ubereats.com/store/chipotle",
            "https://www.ubereats.com/store/taco-bell"
        ]
        
        logger.info("\n📋 Ready to scrape Uber Eats restaurants:")
        for i, url in enumerate(sample_urls, 1):
            logger.info(f"   {i}. {url}")
        
        logger.info("\n✨ Uber Eats scraper features:")
        logger.info("   • Desktop-optimized browser setup")
        logger.info("   • Uber Eats-specific selectors")
        logger.info("   • JSON data extraction")
        logger.info("   • Modal and overlay handling")
        logger.info("   • Advanced price patterns")
        
    except Exception as e:
        logger.error(f"❌ Uber Eats demo failed: {e}")
    finally:
        await scraper.cleanup()

async def demo_ocr_framework():
    """Demonstrate OCR framework capabilities"""
    logger.info("\n🚀 OCR Framework Demo")
    logger.info("=" * 40)
    
    scraper = ProductionMenuScraper(ocr_enabled=True)
    
    try:
        logger.info(f"🔍 OCR Enabled: {scraper.ocr_enabled}")
        logger.info(f"📸 Image Selectors: {len(scraper.image_selectors)} configured")
        
        # Demonstrate image URL filtering
        logger.info("\n📸 Image URL Filtering Demo:")
        test_images = [
            ("https://restaurant.com/menu-board.jpg", "Menu board image"),
            ("https://restaurant.com/food-special.png", "Food special photo"),
            ("https://restaurant.com/logo-small.jpg", "Small logo (should be filtered)"),
            ("https://restaurant.com/dish-pasta.jpg", "Pasta dish photo"),
            ("https://restaurant.com/background-texture.jpg", "Background image (should be filtered)")
        ]
        
        for url, description in test_images:
            is_menu = scraper._is_likely_menu_image(url)
            status = "✅ ACCEPT" if is_menu else "❌ REJECT"
            logger.info(f"   {status} - {description}")
        
        # Demonstrate OCR text processing
        logger.info("\n🔍 OCR Text Processing Demo:")
        sample_ocr_texts = [
            "APPETIZERS\nBruschetta $8.99\nCalamari Rings $12.99\nStuffed Mushrooms $9.99",
            "MAIN COURSES\nGrilled Salmon $18.99\nChicken Parmesan $16.99\nBeef Tenderloin $24.99",
            "DESSERTS\nTiramisu $7.99\nChocolate Cake $6.99\nIce Cream Sundae $4.99"
        ]
        
        total_items = 0
        for i, ocr_text in enumerate(sample_ocr_texts, 1):
            logger.info(f"\n   📋 Sample OCR Text {i}:")
            logger.info(f"   Raw: {ocr_text[:30]}...")
            
            items = scraper._extract_items_from_ocr_text(ocr_text)
            total_items += len(items)
            
            for item in items:
                logger.info(f"      • {item['name']}: {item['price']}")
        
        logger.info(f"\n📊 Total items extracted from OCR: {total_items}")
        
        # Demonstrate simulated OCR
        logger.info("\n🎭 Simulated OCR Demo:")
        sample_urls = [
            "https://restaurant.com/menu1.jpg",
            "https://restaurant.com/menu2.jpg",
            "https://restaurant.com/menu3.jpg"
        ]
        
        for url in sample_urls:
            simulated_text = scraper._simulate_ocr_extraction(url)
            logger.info(f"   📸 {url}")
            logger.info(f"   🔍 OCR Result: {simulated_text[:40]}...")
        
        logger.info("\n✨ OCR Framework features:")
        logger.info("   • Intelligent image URL filtering")
        logger.info("   • Menu-specific image detection")
        logger.info("   • OCR text preprocessing")
        logger.info("   • Menu item extraction from OCR")
        logger.info("   • Simulated OCR for testing")
        logger.info("   • Ready for EasyOCR/Tesseract integration")
        
    except Exception as e:
        logger.error(f"❌ OCR framework demo failed: {e}")
    finally:
        await scraper.cleanup()

async def demo_phase2_integration():
    """Demonstrate Phase 2 integration capabilities"""
    logger.info("\n🚀 Phase 2 Integration Demo")
    logger.info("=" * 40)
    
    try:
        # Show all available scrapers
        scrapers_info = [
            ("DoorDash", DoorDashScraper, "Mobile-optimized delivery platform scraper"),
            ("Uber Eats", UberEatsScraper, "Desktop-optimized delivery platform scraper"),
            ("Production", ProductionMenuScraper, "Enhanced scraper with OCR capabilities")
        ]
        
        logger.info("📦 Available Scrapers:")
        for name, scraper_class, description in scrapers_info:
            logger.info(f"   • {name}: {description}")
        
        # Demonstrate scraper selection logic
        logger.info("\n🎯 Smart Scraper Selection:")
        url_examples = [
            ("https://www.doordash.com/store/restaurant", "DoorDash"),
            ("https://www.ubereats.com/store/restaurant", "Uber Eats"),
            ("https://www.yelp.com/biz/restaurant", "Production (with OCR)"),
            ("https://restaurant-website.com/menu", "Production (with OCR)")
        ]
        
        for url, recommended in url_examples:
            logger.info(f"   📍 {url}")
            logger.info(f"      → Recommended: {recommended} scraper")
        
        logger.info("\n✨ Phase 2 Integration Features:")
        logger.info("   • Platform-specific scrapers (DoorDash, Uber Eats)")
        logger.info("   • Enhanced OCR framework")
        logger.info("   • Consistent scraper interfaces")
        logger.info("   • Intelligent image detection")
        logger.info("   • Fallback OCR processing")
        logger.info("   • Comprehensive testing framework")
        
        # Show Phase 2 improvements summary
        logger.info("\n📈 Phase 2 Improvements:")
        improvements = [
            "Created DoorDash-specific scraper with mobile optimization",
            "Created Uber Eats-specific scraper with desktop optimization",
            "Enhanced production scraper with OCR capabilities",
            "Added intelligent menu image detection",
            "Implemented OCR text processing pipeline",
            "Added comprehensive test and demo scripts",
            "Maintained backward compatibility with Phase 1"
        ]
        
        for i, improvement in enumerate(improvements, 1):
            logger.info(f"   {i}. {improvement}")
        
    except Exception as e:
        logger.error(f"❌ Phase 2 integration demo failed: {e}")

async def main():
    """Run Phase 2 demonstration"""
    logger.info("🎉 Welcome to MenuScraper Phase 2 Demo!")
    logger.info("=" * 50)
    
    demos = [
        ("DoorDash Scraper", demo_doordash_scraper),
        ("Uber Eats Scraper", demo_ubereats_scraper),
        ("OCR Framework", demo_ocr_framework),
        ("Phase 2 Integration", demo_phase2_integration)
    ]
    
    for demo_name, demo_func in demos:
        try:
            await demo_func()
            await asyncio.sleep(1)  # Brief pause between demos
        except Exception as e:
            logger.error(f"❌ {demo_name} demo failed: {e}")
    
    logger.info("\n🎊 Phase 2 Demo Complete!")
    logger.info("=" * 50)
    logger.info("\n📚 Next Steps:")
    logger.info("   1. Run tests: python test_phase2_scrapers.py")
    logger.info("   2. Test DoorDash scraper with live URLs")
    logger.info("   3. Test Uber Eats scraper with live URLs")
    logger.info("   4. Implement full OCR engine (EasyOCR/Tesseract)")
    logger.info("   5. Add more platform-specific scrapers")
    
if __name__ == "__main__":
    asyncio.run(main())