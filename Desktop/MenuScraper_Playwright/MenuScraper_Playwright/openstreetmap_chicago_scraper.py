#!/usr/bin/env python3
"""
OpenStreetMap API Chicago Restaurant Scraper
Collects restaurant data from OpenStreetMap using Overpass API
"""

import requests
import json
import os
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio
import aiohttp
from dataclasses import dataclass

@dataclass
class ChicagoBounds:
    """Chicago city boundaries for geographic search"""
    north: float = 42.0677
    south: float = 41.6445
    east: float = -87.5244
    west: float = -87.9073

class OpenStreetMapChicagoScraper:
    """OpenStreetMap API scraper for Chicago restaurants"""
    
    def __init__(self):
        # OpenStreetMap OAuth credentials
        # SECURITY: OAuth credentials moved to environment variables
        self.client_id = os.getenv('OSM_CLIENT_ID', '')
        self.client_secret = os.getenv('OSM_CLIENT_SECRET', '')
        
        # Overpass API endpoint (no authentication required for basic queries)
        self.overpass_url = "https://overpass-api.de/api/interpreter"
        
        # Chicago boundaries
        self.bounds = ChicagoBounds()
        
        # Rate limiting
        self.request_delay = 1.0  # 1 second between requests
        self.max_retries = 3
        
        # Results storage
        self.restaurants = {}
        self.total_found = 0
        
    def create_overpass_query(self, amenity_type: str = "restaurant") -> str:
        """Create Overpass QL query for Chicago restaurants"""
        query = f"""
        [out:json][timeout:60];
        (
          node["amenity"="{amenity_type}"]({self.bounds.south},{self.bounds.west},{self.bounds.north},{self.bounds.east});
          way["amenity"="{amenity_type}"]({self.bounds.south},{self.bounds.west},{self.bounds.north},{self.bounds.east});
          relation["amenity"="{amenity_type}"]({self.bounds.south},{self.bounds.west},{self.bounds.north},{self.bounds.east});
        );
        out center meta;
        """
        return query
    
    def create_cuisine_query(self, cuisine_type: str) -> str:
        """Create query for specific cuisine types"""
        query = f"""
        [out:json][timeout:60];
        (
          node["amenity"="restaurant"]["cuisine"~"{cuisine_type}",i]({self.bounds.south},{self.bounds.west},{self.bounds.north},{self.bounds.east});
          way["amenity"="restaurant"]["cuisine"~"{cuisine_type}",i]({self.bounds.south},{self.bounds.west},{self.bounds.north},{self.bounds.east});
          node["amenity"="fast_food"]["cuisine"~"{cuisine_type}",i]({self.bounds.south},{self.bounds.west},{self.bounds.north},{self.bounds.east});
          way["amenity"="fast_food"]["cuisine"~"{cuisine_type}",i]({self.bounds.south},{self.bounds.west},{self.bounds.north},{self.bounds.east});
        );
        out center meta;
        """
        return query
    
    async def execute_overpass_query(self, query: str) -> Optional[Dict[str, Any]]:
        """Execute Overpass API query with error handling"""
        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        self.overpass_url,
                        data=query,
                        headers={'Content-Type': 'text/plain'},
                        timeout=aiohttp.ClientTimeout(total=120)
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            return data
                        else:
                            print(f"⚠️ Overpass API returned status {response.status}")
                            
            except Exception as e:
                print(f"❌ Query attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    
        return None
    
    def parse_restaurant_data(self, element: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse OpenStreetMap element into restaurant data"""
        try:
            tags = element.get('tags', {})
            
            # Skip if no name
            name = tags.get('name')
            if not name:
                return None
            
            # Get coordinates
            if element['type'] == 'node':
                lat, lon = element['lat'], element['lon']
            elif 'center' in element:
                lat, lon = element['center']['lat'], element['center']['lon']
            else:
                lat, lon = None, None
            
            # Extract restaurant information
            restaurant = {
                'id': f"osm_{element['type']}_{element['id']}",
                'name': name,
                'latitude': lat,
                'longitude': lon,
                'amenity': tags.get('amenity', 'restaurant'),
                'cuisine': tags.get('cuisine', 'unknown'),
                'address': self._build_address(tags),
                'phone': tags.get('phone'),
                'website': tags.get('website'),
                'opening_hours': tags.get('opening_hours'),
                'wheelchair': tags.get('wheelchair'),
                'outdoor_seating': tags.get('outdoor_seating'),
                'takeaway': tags.get('takeaway'),
                'delivery': tags.get('delivery'),
                'payment_methods': self._extract_payment_methods(tags),
                'dietary_options': self._extract_dietary_options(tags),
                'osm_type': element['type'],
                'osm_id': element['id'],
                'last_modified': element.get('timestamp'),
                'data_source': 'OpenStreetMap'
            }
            
            return restaurant
            
        except Exception as e:
            print(f"❌ Error parsing restaurant data: {e}")
            return None
    
    def _build_address(self, tags: Dict[str, str]) -> str:
        """Build address from OSM tags"""
        address_parts = []
        
        # House number and street
        if tags.get('addr:housenumber') and tags.get('addr:street'):
            address_parts.append(f"{tags['addr:housenumber']} {tags['addr:street']}")
        elif tags.get('addr:street'):
            address_parts.append(tags['addr:street'])
        
        # City
        if tags.get('addr:city'):
            address_parts.append(tags['addr:city'])
        
        # State and postal code
        if tags.get('addr:state'):
            state_zip = tags['addr:state']
            if tags.get('addr:postcode'):
                state_zip += f" {tags['addr:postcode']}"
            address_parts.append(state_zip)
        
        return ', '.join(address_parts) if address_parts else None
    
    def _extract_payment_methods(self, tags: Dict[str, str]) -> List[str]:
        """Extract payment methods from tags"""
        methods = []
        
        payment_tags = {
            'payment:cash': 'cash',
            'payment:cards': 'cards',
            'payment:credit_cards': 'credit_cards',
            'payment:debit_cards': 'debit_cards',
            'payment:contactless': 'contactless',
            'payment:mobile_payment': 'mobile_payment'
        }
        
        for tag, method in payment_tags.items():
            if tags.get(tag) == 'yes':
                methods.append(method)
        
        return methods
    
    def _extract_dietary_options(self, tags: Dict[str, str]) -> List[str]:
        """Extract dietary options from tags"""
        options = []
        
        dietary_tags = {
            'diet:vegetarian': 'vegetarian',
            'diet:vegan': 'vegan',
            'diet:gluten_free': 'gluten_free',
            'diet:halal': 'halal',
            'diet:kosher': 'kosher'
        }
        
        for tag, option in dietary_tags.items():
            if tags.get(tag) == 'yes':
                options.append(option)
        
        return options
    
    async def scrape_restaurants_by_amenity(self) -> int:
        """Scrape restaurants by amenity type"""
        print("🍽️ Scraping restaurants by amenity type...")
        
        amenity_types = ['restaurant', 'fast_food', 'cafe', 'bar', 'pub']
        
        for amenity in amenity_types:
            print(f"\n📍 Searching for amenity: {amenity}")
            
            query = self.create_overpass_query(amenity)
            data = await self.execute_overpass_query(query)
            
            if data and 'elements' in data:
                count = 0
                for element in data['elements']:
                    restaurant = self.parse_restaurant_data(element)
                    if restaurant:
                        restaurant_id = restaurant['id']
                        if restaurant_id not in self.restaurants:
                            self.restaurants[restaurant_id] = restaurant
                            count += 1
                
                print(f"✅ Found {count} new {amenity} establishments")
                print(f"📊 Total unique restaurants: {len(self.restaurants)}")
            
            # Rate limiting
            await asyncio.sleep(self.request_delay)
        
        return len(self.restaurants)
    
    async def scrape_restaurants_by_cuisine(self) -> int:
        """Scrape restaurants by cuisine type"""
        print("\n🌍 Scraping restaurants by cuisine type...")
        
        cuisine_types = [
            'italian', 'mexican', 'chinese', 'japanese', 'indian', 'thai',
            'american', 'pizza', 'burger', 'seafood', 'steakhouse',
            'mediterranean', 'greek', 'french', 'korean', 'vietnamese'
        ]
        
        for cuisine in cuisine_types:
            print(f"\n🍜 Searching for cuisine: {cuisine}")
            
            query = self.create_cuisine_query(cuisine)
            data = await self.execute_overpass_query(query)
            
            if data and 'elements' in data:
                count = 0
                for element in data['elements']:
                    restaurant = self.parse_restaurant_data(element)
                    if restaurant:
                        restaurant_id = restaurant['id']
                        if restaurant_id not in self.restaurants:
                            self.restaurants[restaurant_id] = restaurant
                            count += 1
                        else:
                            # Update cuisine info if more specific
                            existing = self.restaurants[restaurant_id]
                            if existing['cuisine'] == 'unknown' and restaurant['cuisine'] != 'unknown':
                                existing['cuisine'] = restaurant['cuisine']
                
                print(f"✅ Found {count} new {cuisine} restaurants")
                print(f"📊 Total unique restaurants: {len(self.restaurants)}")
            
            # Rate limiting
            await asyncio.sleep(self.request_delay)
        
        return len(self.restaurants)
    
    def calculate_statistics(self) -> Dict[str, Any]:
        """Calculate scraping statistics"""
        if not self.restaurants:
            return {}
        
        # Cuisine distribution
        cuisine_counts = {}
        amenity_counts = {}
        
        for restaurant in self.restaurants.values():
            cuisine = restaurant.get('cuisine', 'unknown')
            amenity = restaurant.get('amenity', 'restaurant')
            
            cuisine_counts[cuisine] = cuisine_counts.get(cuisine, 0) + 1
            amenity_counts[amenity] = amenity_counts.get(amenity, 0) + 1
        
        # Geographic distribution
        with_coordinates = sum(1 for r in self.restaurants.values() 
                             if r.get('latitude') and r.get('longitude'))
        
        # Contact information
        with_phone = sum(1 for r in self.restaurants.values() if r.get('phone'))
        with_website = sum(1 for r in self.restaurants.values() if r.get('website'))
        with_hours = sum(1 for r in self.restaurants.values() if r.get('opening_hours'))
        
        return {
            'total_restaurants': len(self.restaurants),
            'cuisine_distribution': dict(sorted(cuisine_counts.items(), key=lambda x: x[1], reverse=True)),
            'amenity_distribution': amenity_counts,
            'data_completeness': {
                'with_coordinates': with_coordinates,
                'with_phone': with_phone,
                'with_website': with_website,
                'with_opening_hours': with_hours,
                'coordinate_coverage': round(with_coordinates / len(self.restaurants) * 100, 1),
                'phone_coverage': round(with_phone / len(self.restaurants) * 100, 1),
                'website_coverage': round(with_website / len(self.restaurants) * 100, 1),
                'hours_coverage': round(with_hours / len(self.restaurants) * 100, 1)
            }
        }
    
    def save_results(self, filename: str = None) -> str:
        """Save scraping results to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"output/chicago_restaurants_openstreetmap_{timestamp}.json"
        
        # Create output directory if it doesn't exist
        import os
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Prepare data for saving
        results = {
            'scraping_info': {
                'timestamp': datetime.now().isoformat(),
                'data_source': 'OpenStreetMap',
                'api_endpoint': self.overpass_url,
                'search_area': 'Chicago, IL',
                'bounds': {
                    'north': self.bounds.north,
                    'south': self.bounds.south,
                    'east': self.bounds.east,
                    'west': self.bounds.west
                }
            },
            'statistics': self.calculate_statistics(),
            'restaurants': list(self.restaurants.values())
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Results saved to: {filename}")
        return filename
    
    async def scrape_all_chicago_restaurants(self) -> Dict[str, Any]:
        """Main scraping method - comprehensive Chicago restaurant collection"""
        start_time = time.time()
        
        print("🏙️ Starting OpenStreetMap Chicago Restaurant Scraper")
        print(f"📍 Search area: Chicago, IL ({self.bounds.south}, {self.bounds.west}) to ({self.bounds.north}, {self.bounds.east})")
        print(f"🌐 API endpoint: {self.overpass_url}")
        
        try:
            # Phase 1: Scrape by amenity type
            amenity_count = await self.scrape_restaurants_by_amenity()
            
            # Phase 2: Scrape by cuisine type
            cuisine_count = await self.scrape_restaurants_by_cuisine()
            
            # Calculate final statistics
            stats = self.calculate_statistics()
            
            # Save results
            filename = self.save_results()
            
            # Calculate processing time
            processing_time = round(time.time() - start_time, 2)
            
            print(f"\n🎉 OpenStreetMap scraping completed!")
            print(f"📊 Total restaurants found: {len(self.restaurants)}")
            print(f"⏱️ Processing time: {processing_time} seconds")
            print(f"💾 Data saved to: {filename}")
            
            return {
                'success': True,
                'total_restaurants': len(self.restaurants),
                'processing_time': processing_time,
                'filename': filename,
                'statistics': stats,
                'data_source': 'OpenStreetMap'
            }
            
        except Exception as e:
            print(f"❌ Scraping failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'total_restaurants': len(self.restaurants),
                'processing_time': round(time.time() - start_time, 2)
            }

async def main():
    """Main execution function"""
    scraper = OpenStreetMapChicagoScraper()
    results = await scraper.scrape_all_chicago_restaurants()
    
    if results['success']:
        print(f"\n✅ Successfully collected {results['total_restaurants']} Chicago restaurants from OpenStreetMap")
        print(f"📈 Data completeness metrics available in saved file")
    else:
        print(f"\n❌ Scraping failed: {results.get('error', 'Unknown error')}")

if __name__ == "__main__":
    asyncio.run(main())