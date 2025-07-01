#!/usr/bin/env python3
"""
Comprehensive Chicago Restaurant Scraper
Collects thousands of Chicago restaurants using multiple data sources and APIs
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import requests
from dataclasses import dataclass

# Import existing scrapers
from yelp_optimized_chicago_scraper import scrape_all_chicago_restaurants_optimized
from foursquare_api_chicago_scraper import scrape_all_chicago_restaurants_foursquare
from practical_ml_scraper import PracticalMLScraper

@dataclass
class RestaurantData:
    """Standardized restaurant data structure"""
    name: str
    url: str
    source: str
    rating: float = 0.0
    review_count: int = 0
    price_range: str = ""
    phone: str = ""
    address: str = ""
    categories: List[str] = None
    coordinates: Dict[str, float] = None
    
    def __post_init__(self):
        if self.categories is None:
            self.categories = []
        if self.coordinates is None:
            self.coordinates = {}

class ComprehensiveChicagoScraper:
    """Comprehensive scraper for thousands of Chicago restaurants"""
    
    def __init__(self):
        self.setup_logging()
        self.restaurants = {}
        self.stats = {
            'total_collected': 0,
            'yelp_count': 0,
            'foursquare_count': 0,
            'duplicates_removed': 0,
            'api_calls_used': 0,
            'start_time': None,
            'end_time': None
        }
        
    def setup_logging(self):
        """Setup comprehensive logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'comprehensive_chicago_scraping_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def normalize_restaurant_name(self, name: str) -> str:
        """Normalize restaurant names for duplicate detection"""
        return name.lower().strip().replace("'", "").replace("-", " ").replace("&", "and")
        
    def is_duplicate(self, restaurant: Dict[str, Any], existing_restaurants: Dict[str, Any]) -> bool:
        """Check if restaurant is a duplicate based on name and location"""
        normalized_name = self.normalize_restaurant_name(restaurant.get('name', ''))
        
        for existing_id, existing in existing_restaurants.items():
            existing_normalized = self.normalize_restaurant_name(existing.get('name', ''))
            
            # Check name similarity
            if normalized_name == existing_normalized:
                return True
                
            # Check location proximity (if coordinates available)
            if ('coordinates' in restaurant and 'coordinates' in existing and
                restaurant['coordinates'] and existing['coordinates']):
                
                lat1, lng1 = restaurant['coordinates'].get('latitude', 0), restaurant['coordinates'].get('longitude', 0)
                lat2, lng2 = existing['coordinates'].get('latitude', 0), existing['coordinates'].get('longitude', 0)
                
                # Simple distance check (approximately 100 meters)
                if abs(lat1 - lat2) < 0.001 and abs(lng1 - lng2) < 0.001:
                    if normalized_name in existing_normalized or existing_normalized in normalized_name:
                        return True
                        
        return False
        
    async def collect_yelp_restaurants(self, max_restaurants: int = 10000) -> Dict[str, Any]:
        """Collect restaurants from Yelp API using optimized scraper"""
        self.logger.info(f"🔍 Starting Yelp API collection (target: {max_restaurants} restaurants)")
        
        try:
            yelp_data = scrape_all_chicago_restaurants_optimized(max_restaurants)
            
            if yelp_data and 'restaurants' in yelp_data:
                restaurants = yelp_data['restaurants']
                self.stats['yelp_count'] = len(restaurants)
                self.stats['api_calls_used'] += yelp_data.get('api_calls_used', 0)
                
                self.logger.info(f"✅ Yelp API: Collected {len(restaurants)} restaurants")
                return restaurants
            else:
                self.logger.warning("❌ Yelp API: No data returned")
                return {}
                
        except Exception as e:
            self.logger.error(f"❌ Yelp API collection failed: {e}")
            return {}
            
    async def collect_foursquare_restaurants(self) -> Dict[str, Any]:
        """Collect restaurants from Foursquare API"""
        self.logger.info("🔍 Starting Foursquare API collection")
        
        try:
            foursquare_data = scrape_all_chicago_restaurants_foursquare()
            
            if foursquare_data and 'restaurants' in foursquare_data:
                restaurants = foursquare_data['restaurants']
                self.stats['foursquare_count'] = len(restaurants)
                
                self.logger.info(f"✅ Foursquare API: Collected {len(restaurants)} restaurants")
                return restaurants
            else:
                self.logger.warning("❌ Foursquare API: No data returned")
                return {}
                
        except Exception as e:
            self.logger.error(f"❌ Foursquare API collection failed: {e}")
            return {}
            
    def merge_restaurant_data(self, yelp_restaurants: Dict[str, Any], foursquare_restaurants: Dict[str, Any]) -> Dict[str, Any]:
        """Merge restaurant data from multiple sources, removing duplicates"""
        self.logger.info("🔄 Merging restaurant data from multiple sources")
        
        merged_restaurants = {}
        duplicate_count = 0
        
        # Add Yelp restaurants first
        for restaurant_id, restaurant in yelp_restaurants.items():
            restaurant['source'] = 'yelp'
            merged_restaurants[restaurant_id] = restaurant
            
        # Add Foursquare restaurants, checking for duplicates
        for restaurant_id, restaurant in foursquare_restaurants.items():
            restaurant['source'] = 'foursquare'
            
            if not self.is_duplicate(restaurant, merged_restaurants):
                # Create unique ID for Foursquare restaurants
                unique_id = f"foursquare_{restaurant_id}"
                merged_restaurants[unique_id] = restaurant
            else:
                duplicate_count += 1
                
        self.stats['duplicates_removed'] = duplicate_count
        self.stats['total_collected'] = len(merged_restaurants)
        
        self.logger.info(f"✅ Merged data: {len(merged_restaurants)} unique restaurants")
        self.logger.info(f"🗑️ Removed {duplicate_count} duplicates")
        
        return merged_restaurants
        
    def generate_restaurant_list_for_scraping(self, restaurants: Dict[str, Any], max_for_scraping: int = 500) -> List[Dict[str, str]]:
        """Generate a prioritized list of restaurants for menu scraping"""
        self.logger.info(f"📋 Generating prioritized list for menu scraping (max: {max_for_scraping})")
        
        restaurant_list = []
        
        for restaurant_id, restaurant in restaurants.items():
            # Prioritize restaurants with higher ratings and more reviews
            priority_score = (restaurant.get('rating', 0) * 0.7 + 
                            min(restaurant.get('review_count', 0) / 100, 5) * 0.3)
            
            restaurant_entry = {
                'name': restaurant.get('name', 'Unknown'),
                'url': restaurant.get('url', ''),
                'source': restaurant.get('source', 'unknown'),
                'priority_score': priority_score,
                'rating': restaurant.get('rating', 0),
                'review_count': restaurant.get('review_count', 0)
            }
            
            if restaurant_entry['url']:  # Only include restaurants with URLs
                restaurant_list.append(restaurant_entry)
                
        # Sort by priority score (highest first)
        restaurant_list.sort(key=lambda x: x['priority_score'], reverse=True)
        
        # Return top restaurants for scraping
        selected_restaurants = restaurant_list[:max_for_scraping]
        
        self.logger.info(f"📊 Selected {len(selected_restaurants)} restaurants for menu scraping")
        self.logger.info(f"📈 Average rating: {sum(r['rating'] for r in selected_restaurants) / len(selected_restaurants):.2f}")
        
        return selected_restaurants
        
    async def scrape_sample_menus(self, restaurant_list: List[Dict[str, str]], sample_size: int = 50) -> Dict[str, Any]:
        """Scrape menus from a sample of restaurants to demonstrate capabilities"""
        self.logger.info(f"🍽️ Starting menu scraping for {sample_size} sample restaurants")
        
        scraper = PracticalMLScraper()
        await scraper.setup_browser()
        
        menu_results = []
        successful_scrapes = 0
        
        try:
            for i, restaurant in enumerate(restaurant_list[:sample_size]):
                self.logger.info(f"Scraping {i+1}/{sample_size}: {restaurant['name']}")
                
                try:
                    result = await scraper.extract_menu_items(restaurant['url'])
                    
                    if result and result.get('extracted_items'):
                        successful_scrapes += 1
                        self.logger.info(f"✅ Success: {restaurant['name']} - {len(result['extracted_items'])} items")
                    else:
                        self.logger.warning(f"❌ Failed: {restaurant['name']} - No menu items found")
                        
                    # Add restaurant metadata to result
                    result['restaurant_name'] = restaurant['name']
                    result['restaurant_url'] = restaurant['url']
                    result['source'] = restaurant['source']
                    result['rating'] = restaurant['rating']
                    result['review_count'] = restaurant['review_count']
                    
                    menu_results.append(result)
                    
                    # Small delay between requests
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    self.logger.error(f"❌ Error scraping {restaurant['name']}: {e}")
                    menu_results.append({
                        'restaurant_name': restaurant['name'],
                        'restaurant_url': restaurant['url'],
                        'error': str(e),
                        'success': False
                    })
                    
        finally:
            await scraper.cleanup()
            
        success_rate = (successful_scrapes / sample_size) * 100 if sample_size > 0 else 0
        self.logger.info(f"🎯 Menu scraping complete: {successful_scrapes}/{sample_size} successful ({success_rate:.1f}%)")
        
        return {
            'menu_results': menu_results,
            'successful_scrapes': successful_scrapes,
            'total_attempted': sample_size,
            'success_rate': success_rate
        }
        
    async def run_comprehensive_collection(self, max_restaurants: int = 15000, menu_sample_size: int = 100) -> str:
        """Run comprehensive Chicago restaurant collection"""
        self.stats['start_time'] = datetime.now()
        
        self.logger.info("🚀 STARTING COMPREHENSIVE CHICAGO RESTAURANT COLLECTION")
        self.logger.info(f"📊 Target: {max_restaurants} restaurants with {menu_sample_size} menu samples")
        self.logger.info("=" * 80)
        
        # Step 1: Collect from Yelp API
        yelp_restaurants = await self.collect_yelp_restaurants(max_restaurants)
        
        # Step 2: Collect from Foursquare API
        foursquare_restaurants = await self.collect_foursquare_restaurants()
        
        # Step 3: Merge and deduplicate
        all_restaurants = self.merge_restaurant_data(yelp_restaurants, foursquare_restaurants)
        
        # Step 4: Generate prioritized list for menu scraping
        restaurant_list = self.generate_restaurant_list_for_scraping(all_restaurants, max_for_scraping=1000)
        
        # Step 5: Scrape sample menus
        menu_data = await self.scrape_sample_menus(restaurant_list, menu_sample_size)
        
        # Step 6: Compile final results
        self.stats['end_time'] = datetime.now()
        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        
        final_results = {
            'collection_metadata': {
                'timestamp': self.stats['start_time'].isoformat(),
                'duration_seconds': duration,
                'target_restaurants': max_restaurants,
                'menu_sample_size': menu_sample_size
            },
            'collection_stats': self.stats,
            'restaurant_database': all_restaurants,
            'prioritized_restaurant_list': restaurant_list,
            'menu_scraping_results': menu_data,
            'summary': {
                'total_restaurants_collected': len(all_restaurants),
                'yelp_restaurants': self.stats['yelp_count'],
                'foursquare_restaurants': self.stats['foursquare_count'],
                'duplicates_removed': self.stats['duplicates_removed'],
                'menu_scraping_success_rate': menu_data.get('success_rate', 0),
                'estimated_chicago_coverage': min(100, (len(all_restaurants) / 8000) * 100)
            }
        }
        
        # Save results
        output_file = f"comprehensive_chicago_restaurants_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(final_results, f, indent=2, ensure_ascii=False)
            
        self.logger.info("=" * 80)
        self.logger.info("🎉 COMPREHENSIVE COLLECTION COMPLETE!")
        self.logger.info(f"📁 Results saved to: {output_file}")
        self.logger.info(f"📊 Total restaurants: {len(all_restaurants)}")
        self.logger.info(f"🍽️ Menu samples: {menu_data.get('successful_scrapes', 0)}/{menu_sample_size}")
        self.logger.info(f"⏱️ Duration: {duration:.1f} seconds")
        self.logger.info(f"📈 Estimated Chicago coverage: {min(100, (len(all_restaurants) / 8000) * 100):.1f}%")
        
        return output_file

async def main():
    """Main execution function"""
    scraper = ComprehensiveChicagoScraper()
    
    # Run comprehensive collection
    # Targeting 15,000 restaurants with 100 menu samples
    output_file = await scraper.run_comprehensive_collection(
        max_restaurants=15000,
        menu_sample_size=100
    )
    
    print(f"\n🎊 Collection complete! Results saved to: {output_file}")
    print("\n📋 This comprehensive database includes:")
    print("   • Thousands of Chicago restaurants from multiple APIs")
    print("   • Deduplicated and prioritized restaurant data")
    print("   • Sample menu extractions with ML analysis")
    print("   • Comprehensive performance metrics")
    print("   • Ready for production menu scraping at scale")

if __name__ == "__main__":
    asyncio.run(main())