#!/usr/bin/env python3
"""
Quick launcher for Phase 1 Menu Scraper Improvements Demo

This script provides an easy way to test the Phase 1 improvements:
- Enhanced Yelp menu detection
- Official website discovery and fallback
- Improved price extraction
- Dynamic content handling

Usage:
    python run_phase1_demo.py
"""

import asyncio
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

try:
    from enhanced_dynamic_scraper import EnhancedDynamicScraper
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure you're in the correct directory and have installed dependencies.")
    print("Run: pip install -r requirements.txt")
    sys.exit(1)

async def quick_phase1_demo():
    """Quick demonstration of Phase 1 improvements"""
    print("🚀 MenuScraper Phase 1 Improvements - Quick Demo")
    print("="*60)
    
    # Test restaurant - you can modify this
    test_restaurant = {
        'name': 'The Cheesecake Factory',
        'url': 'https://www.yelp.com/biz/the-cheesecake-factory-beverly-hills'
    }
    
    print(f"🍽️  Testing: {test_restaurant['name']}")
    print(f"📍 URL: {test_restaurant['url']}")
    print("\n🔄 Initializing enhanced scraper...")
    
    # Initialize scraper with Phase 1 improvements
    scraper = EnhancedDynamicScraper(
        headless=True,  # Set to False to see browser in action
        timeout=30000   # 30 second timeout
    )
    
    try:
        # Setup browser
        print("🌐 Setting up browser...")
        if not await scraper.setup_browser():
            print("❌ Failed to setup browser")
            return
        
        print("✅ Browser ready!")
        print("\n🔍 Starting Phase 1 enhanced extraction...")
        
        # Use the new Phase 1 extract_menu_items method
        result = await scraper.extract_menu_items(
            url=test_restaurant['url'],
            restaurant_name=test_restaurant['name']
        )
        
        # Display results
        print("\n📊 PHASE 1 RESULTS:")
        print(f"   ✅ Success: {result.get('scraping_success', False)}")
        print(f"   📈 Total Items: {result.get('total_items', 0)}")
        print(f"   🔧 Extraction Method: {result.get('extraction_method', 'unknown')}")
        print(f"   🌐 Primary URL: {result.get('primary_url', 'N/A')}")
        
        # Check if fallback was used
        if result.get('fallback_url'):
            print(f"   🔄 Fallback URL: {result['fallback_url']}")
            print("   ✨ Phase 1 fallback logic was successfully used!")
        else:
            print("   🔄 Fallback: Not needed (primary extraction sufficient)")
        
        if result.get('error'):
            print(f"   ❌ Error: {result['error']}")
        
        # Show sample items
        items = result.get('items', [])
        if items:
            print(f"\n📋 SAMPLE MENU ITEMS (first 3):")
            for i, item in enumerate(items[:3], 1):
                print(f"\n   {i}. {item.get('name', 'Unknown Item')}")
                
                if item.get('price'):
                    print(f"      💰 Price: ${item['price']:.2f}")
                
                if item.get('description'):
                    desc = item['description'][:60] + "..." if len(item['description']) > 60 else item['description']
                    print(f"      📝 Description: {desc}")
                
                print(f"      🏷️  Category: {item.get('category', 'other')}")
            
            # Quick statistics
            with_prices = len([item for item in items if item.get('price')])
            with_descriptions = len([item for item in items if item.get('description')])
            
            print(f"\n📈 EXTRACTION QUALITY:")
            print(f"   💰 Items with prices: {with_prices}/{len(items)} ({with_prices/len(items)*100:.1f}%)")
            print(f"   📝 Items with descriptions: {with_descriptions}/{len(items)} ({with_descriptions/len(items)*100:.1f}%)")
        
        else:
            print("\n❌ No menu items were extracted")
            print("   This could be due to:")
            print("   - Website blocking automated requests")
            print("   - Changes in website structure")
            print("   - Network connectivity issues")
        
        print("\n✨ PHASE 1 IMPROVEMENTS DEMONSTRATED:")
        print("   🔍 Enhanced Yelp menu detection with better price patterns")
        print("   🌐 Google search for official restaurant website discovery")
        print("   🔄 Intelligent fallback when primary source is insufficient")
        print("   📈 Improved dynamic content handling and scrolling")
        print("   🎯 Better extraction accuracy and coverage")
        
    except Exception as e:
        print(f"❌ Demo failed with error: {str(e)}")
        print("\nTroubleshooting tips:")
        print("1. Check your internet connection")
        print("2. Ensure Playwright browsers are installed: playwright install")
        print("3. Try running with headless=False to see what's happening")
        print("4. Check if the target website is accessible")
    
    finally:
        # Always cleanup
        print("\n🧹 Cleaning up browser resources...")
        await scraper.cleanup()
        print("✅ Demo completed!")

def main():
    """Main entry point"""
    print("Starting Phase 1 Menu Scraper Demo...")
    print("Press Ctrl+C to stop at any time.\n")
    
    try:
        asyncio.run(quick_phase1_demo())
    except KeyboardInterrupt:
        print("\n\n⏹️  Demo stopped by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        print("Please check your setup and try again.")
    
    print("\n🎯 Want to run more comprehensive tests?")
    print("   Try: python test_phase1_improvements.py")
    print("\n📚 Check the README.md for more information about Phase 1 improvements.")

if __name__ == "__main__":
    main()