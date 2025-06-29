#!/usr/bin/env python3
"""
Simple demonstration of Phase 1 Menu Scraper Improvements

This script provides a quick demo of the enhanced scraper capabilities:
- Enhanced Yelp menu detection
- Official website discovery and fallback
- Improved price extraction
- Dynamic content handling
"""

import asyncio
from enhanced_dynamic_scraper import EnhancedDynamicScraper

async def demo_phase1_improvements():
    """Demonstrate Phase 1 improvements with a single restaurant"""
    print("🚀 Phase 1 Menu Scraper Improvements Demo")
    print("="*50)
    
    # Example restaurant (you can change this)
    restaurant_name = "The Cheesecake Factory"
    yelp_url = "https://www.yelp.com/biz/the-cheesecake-factory-beverly-hills"
    
    print(f"🍽️  Restaurant: {restaurant_name}")
    print(f"📍 Yelp URL: {yelp_url}")
    print("\n🔄 Starting enhanced scraping with fallback logic...")
    
    # Initialize the enhanced scraper
    scraper = EnhancedDynamicScraper(headless=True, timeout=30000)
    
    try:
        # Setup browser
        if not await scraper.setup_browser():
            print("❌ Failed to setup browser")
            return
        
        print("✅ Browser initialized successfully")
        
        # Use the new extract_menu_items method with fallback
        print("\n🔍 Phase 1: Attempting Yelp extraction...")
        result = await scraper.extract_menu_items(
            url=yelp_url,
            restaurant_name=restaurant_name
        )
        
        # Display results
        print("\n📊 EXTRACTION RESULTS:")
        print(f"   ✅ Success: {result.get('scraping_success', False)}")
        print(f"   📈 Total Items: {result.get('total_items', 0)}")
        print(f"   🔧 Method: {result.get('extraction_method', 'unknown')}")
        print(f"   🌐 Primary URL: {result.get('primary_url', 'N/A')}")
        
        if result.get('fallback_url'):
            print(f"   🔄 Fallback URL: {result['fallback_url']}")
            print("   ✨ Fallback logic was used!")
        else:
            print("   🔄 Fallback URL: Not needed")
        
        if result.get('error'):
            print(f"   ❌ Error: {result['error']}")
        
        # Show sample menu items
        items = result.get('items', [])
        if items:
            print(f"\n📋 SAMPLE MENU ITEMS (first 5):")
            for i, item in enumerate(items[:5], 1):
                print(f"\n   {i}. {item.get('name', 'Unknown Item')}")
                
                if item.get('price'):
                    print(f"      💰 Price: ${item['price']:.2f}")
                
                if item.get('description'):
                    desc = item['description'][:80] + "..." if len(item['description']) > 80 else item['description']
                    print(f"      📝 Description: {desc}")
                
                print(f"      🏷️  Category: {item.get('category', 'other')}")
                print(f"      🔍 Extracted via: {item.get('extraction_method', 'unknown')}")
            
            # Quick stats
            with_prices = len([item for item in items if item.get('price')])
            with_descriptions = len([item for item in items if item.get('description')])
            
            print(f"\n📈 QUICK STATS:")
            print(f"   💰 Items with prices: {with_prices}/{len(items)} ({with_prices/len(items)*100:.1f}%)")
            print(f"   📝 Items with descriptions: {with_descriptions}/{len(items)} ({with_descriptions/len(items)*100:.1f}%)")
            
            if with_prices > 0:
                prices = [item['price'] for item in items if item.get('price')]
                print(f"   💵 Price range: ${min(prices):.2f} - ${max(prices):.2f}")
        
        else:
            print("\n❌ No menu items were extracted")
        
        print("\n✨ PHASE 1 IMPROVEMENTS DEMONSTRATED:")
        print("   🔍 Enhanced Yelp menu detection with better price patterns")
        print("   🌐 Google search for official restaurant website")
        print("   🔄 Intelligent fallback when primary source is insufficient")
        print("   📈 Improved dynamic content handling and scrolling")
        print("   🎯 Better extraction accuracy and coverage")
        
    except Exception as e:
        print(f"❌ Demo failed: {str(e)}")
    
    finally:
        # Cleanup
        await scraper.cleanup()
        print("\n🧹 Browser cleanup completed")
        print("✅ Demo finished!")

if __name__ == "__main__":
    print("Starting Phase 1 Menu Scraper Demo...")
    asyncio.run(demo_phase1_improvements())