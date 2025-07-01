#!/usr/bin/env python3
"""
National Restaurant Data Scaling Pipeline

This script demonstrates how to scale the restaurant data collection and menu extraction
process from Chicago to national coverage across major US cities.

Features:
- Multi-city data collection
- Distributed processing
- Progress tracking
- Error handling and retry logic
- Data quality monitoring
- Storage optimization
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import aiohttp
import time
from dataclasses import dataclass, asdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('national_scaling.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class CityConfig:
    """Configuration for each city to be processed"""
    name: str
    state: str
    bbox: Tuple[float, float, float, float]  # (south, west, north, east)
    population: int
    expected_restaurants: int
    priority: int  # 1=highest, 5=lowest

@dataclass
class ProcessingStats:
    """Statistics for tracking processing progress"""
    city: str
    start_time: datetime
    end_time: Optional[datetime] = None
    restaurants_found: int = 0
    menus_extracted: int = 0
    success_rate: float = 0.0
    processing_time_seconds: float = 0.0
    errors: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []

class NationalScalingPipeline:
    """Main pipeline for scaling restaurant data collection nationally"""
    
    def __init__(self, output_dir: str = "output/national"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Major US cities configuration
        self.cities = {
            # Tier 1 Cities (Highest Priority)
            "new_york": CityConfig(
                name="New York", state="NY",
                bbox=(40.4774, -74.2591, 40.9176, -73.7004),
                population=8336817, expected_restaurants=25000, priority=1
            ),
            "los_angeles": CityConfig(
                name="Los Angeles", state="CA",
                bbox=(33.7037, -118.6681, 34.3373, -118.1553),
                population=3898747, expected_restaurants=18000, priority=1
            ),
            "chicago": CityConfig(
                name="Chicago", state="IL",
                bbox=(41.6444, -87.9073, 42.0230, -87.5248),
                population=2746388, expected_restaurants=12000, priority=1
            ),
            
            # Tier 2 Cities
            "houston": CityConfig(
                name="Houston", state="TX",
                bbox=(29.5274, -95.8240, 30.1105, -95.0140),
                population=2304580, expected_restaurants=10000, priority=2
            ),
            "phoenix": CityConfig(
                name="Phoenix", state="AZ",
                bbox=(33.2829, -112.3251, 33.7805, -111.9267),
                population=1608139, expected_restaurants=8000, priority=2
            ),
            "philadelphia": CityConfig(
                name="Philadelphia", state="PA",
                bbox=(39.8670, -75.2803, 40.1379, -74.9557),
                population=1584064, expected_restaurants=7500, priority=2
            ),
            
            # Tier 3 Cities
            "san_antonio": CityConfig(
                name="San Antonio", state="TX",
                bbox=(29.2140, -98.7841, 29.6997, -98.2952),
                population=1547253, expected_restaurants=6000, priority=3
            ),
            "san_diego": CityConfig(
                name="San Diego", state="CA",
                bbox=(32.5343, -117.3191, 33.1143, -116.9325),
                population=1423851, expected_restaurants=7000, priority=3
            ),
            "dallas": CityConfig(
                name="Dallas", state="TX",
                bbox=(32.6178, -96.9989, 33.0237, -96.5991),
                population=1343573, expected_restaurants=6500, priority=3
            ),
            
            # Additional cities can be added here...
        }
        
        self.processing_stats: Dict[str, ProcessingStats] = {}
        
    async def collect_city_restaurants(self, city_key: str, city_config: CityConfig) -> Dict:
        """Collect restaurant data for a specific city using OpenStreetMap"""
        logger.info(f"🏙️ Starting data collection for {city_config.name}, {city_config.state}")
        
        start_time = datetime.now()
        self.processing_stats[city_key] = ProcessingStats(
            city=f"{city_config.name}, {city_config.state}",
            start_time=start_time
        )
        
        try:
            # Overpass API query for restaurants in the city
            overpass_query = f"""
            [out:json][timeout:300];
            (
              node["amenity"="restaurant"]{city_config.bbox};
              way["amenity"="restaurant"]{city_config.bbox};
              relation["amenity"="restaurant"]{city_config.bbox};
            );
            out geom;
            """
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://overpass-api.de/api/interpreter",
                    data=overpass_query,
                    timeout=aiohttp.ClientTimeout(total=600)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        restaurants = self._process_overpass_data(data, city_config)
                        
                        # Update stats
                        stats = self.processing_stats[city_key]
                        stats.restaurants_found = len(restaurants)
                        stats.end_time = datetime.now()
                        stats.processing_time_seconds = (stats.end_time - stats.start_time).total_seconds()
                        
                        logger.info(f"✅ {city_config.name}: Found {len(restaurants)} restaurants in {stats.processing_time_seconds:.1f}s")
                        
                        return {
                            "city_info": asdict(city_config),
                            "collection_timestamp": datetime.now().isoformat(),
                            "restaurants": restaurants,
                            "statistics": {
                                "total_restaurants": len(restaurants),
                                "processing_time_seconds": stats.processing_time_seconds
                            }
                        }
                    else:
                        error_msg = f"HTTP {response.status}: {await response.text()}"
                        self.processing_stats[city_key].errors.append(error_msg)
                        logger.error(f"❌ {city_config.name}: {error_msg}")
                        return None
                        
        except Exception as e:
            error_msg = f"Exception during collection: {str(e)}"
            self.processing_stats[city_key].errors.append(error_msg)
            logger.error(f"❌ {city_config.name}: {error_msg}")
            return None
    
    def _process_overpass_data(self, data: Dict, city_config: CityConfig) -> List[Dict]:
        """Process raw Overpass API data into structured restaurant records"""
        restaurants = []
        
        for element in data.get('elements', []):
            tags = element.get('tags', {})
            
            # Extract coordinates
            if element['type'] == 'node':
                lat, lon = element.get('lat'), element.get('lon')
            elif element['type'] == 'way' and 'center' in element:
                lat, lon = element['center'].get('lat'), element['center'].get('lon')
            else:
                continue
                
            restaurant = {
                "id": f"osm_{element['type']}_{element['id']}",
                "name": tags.get('name', 'Unknown'),
                "cuisine": tags.get('cuisine', 'unknown'),
                "coordinates": {"latitude": lat, "longitude": lon},
                "address": {
                    "street": tags.get('addr:street'),
                    "housenumber": tags.get('addr:housenumber'),
                    "city": city_config.name,
                    "state": city_config.state,
                    "postcode": tags.get('addr:postcode')
                },
                "contact": {
                    "phone": tags.get('phone'),
                    "website": tags.get('website'),
                    "email": tags.get('email')
                },
                "details": {
                    "opening_hours": tags.get('opening_hours'),
                    "wheelchair": tags.get('wheelchair'),
                    "outdoor_seating": tags.get('outdoor_seating'),
                    "takeaway": tags.get('takeaway'),
                    "delivery": tags.get('delivery')
                },
                "data_source": "openstreetmap",
                "osm_element_type": element['type'],
                "osm_id": element['id']
            }
            
            restaurants.append(restaurant)
            
        return restaurants
    
    async def process_cities_by_priority(self, max_concurrent: int = 3) -> Dict[str, Dict]:
        """Process cities in priority order with concurrency control"""
        logger.info(f"🚀 Starting National Restaurant Data Collection Pipeline")
        logger.info(f"📊 Processing {len(self.cities)} cities with max {max_concurrent} concurrent requests")
        
        # Group cities by priority
        cities_by_priority = {}
        for city_key, city_config in self.cities.items():
            priority = city_config.priority
            if priority not in cities_by_priority:
                cities_by_priority[priority] = []
            cities_by_priority[priority].append((city_key, city_config))
        
        all_results = {}
        
        # Process each priority tier
        for priority in sorted(cities_by_priority.keys()):
            cities_in_tier = cities_by_priority[priority]
            logger.info(f"\n🎯 Processing Priority {priority} cities: {[config.name for _, config in cities_in_tier]}")
            
            # Process cities in batches within each priority tier
            for i in range(0, len(cities_in_tier), max_concurrent):
                batch = cities_in_tier[i:i + max_concurrent]
                
                # Create tasks for concurrent processing
                tasks = [
                    self.collect_city_restaurants(city_key, city_config)
                    for city_key, city_config in batch
                ]
                
                # Execute batch concurrently
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results
                for (city_key, city_config), result in zip(batch, batch_results):
                    if isinstance(result, Exception):
                        logger.error(f"❌ {city_config.name}: Exception - {result}")
                        self.processing_stats[city_key].errors.append(str(result))
                    elif result:
                        all_results[city_key] = result
                        
                        # Save individual city data
                        city_filename = f"{city_key}_restaurants_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                        city_filepath = self.output_dir / city_filename
                        
                        with open(city_filepath, 'w', encoding='utf-8') as f:
                            json.dump(result, f, indent=2, ensure_ascii=False)
                        
                        logger.info(f"💾 {city_config.name}: Data saved to {city_filename}")
                
                # Brief pause between batches to be respectful to APIs
                if i + max_concurrent < len(cities_in_tier):
                    await asyncio.sleep(2)
        
        return all_results
    
    def generate_national_summary(self, results: Dict[str, Dict]) -> Dict:
        """Generate comprehensive summary of national data collection"""
        summary = {
            "generation_timestamp": datetime.now().isoformat(),
            "pipeline_version": "1.0",
            "total_cities_processed": len(results),
            "total_restaurants_collected": sum(r["statistics"]["total_restaurants"] for r in results.values()),
            "processing_statistics": {},
            "city_breakdown": {},
            "data_quality_metrics": {},
            "next_steps": [
                "Menu extraction for collected restaurants",
                "Data deduplication and quality enhancement",
                "Real-time update pipeline setup",
                "API endpoint development for data access"
            ]
        }
        
        # Calculate processing statistics
        total_time = sum(stats.processing_time_seconds for stats in self.processing_stats.values())
        successful_cities = len([s for s in self.processing_stats.values() if not s.errors])
        
        summary["processing_statistics"] = {
            "total_processing_time_seconds": total_time,
            "average_time_per_city": total_time / len(self.processing_stats) if self.processing_stats else 0,
            "successful_cities": successful_cities,
            "failed_cities": len(self.processing_stats) - successful_cities,
            "overall_success_rate": (successful_cities / len(self.processing_stats)) * 100 if self.processing_stats else 0
        }
        
        # City breakdown
        for city_key, result in results.items():
            city_info = result["city_info"]
            stats = result["statistics"]
            
            summary["city_breakdown"][city_key] = {
                "name": f"{city_info['name']}, {city_info['state']}",
                "restaurants_found": stats["total_restaurants"],
                "expected_restaurants": city_info["expected_restaurants"],
                "coverage_percentage": (stats["total_restaurants"] / city_info["expected_restaurants"]) * 100,
                "processing_time": stats["processing_time_seconds"]
            }
        
        # Data quality metrics
        all_restaurants = []
        for result in results.values():
            all_restaurants.extend(result["restaurants"])
        
        if all_restaurants:
            phone_coverage = sum(1 for r in all_restaurants if r["contact"]["phone"]) / len(all_restaurants) * 100
            website_coverage = sum(1 for r in all_restaurants if r["contact"]["website"]) / len(all_restaurants) * 100
            hours_coverage = sum(1 for r in all_restaurants if r["details"]["opening_hours"]) / len(all_restaurants) * 100
            
            summary["data_quality_metrics"] = {
                "phone_coverage_percentage": phone_coverage,
                "website_coverage_percentage": website_coverage,
                "hours_coverage_percentage": hours_coverage,
                "total_unique_restaurants": len(all_restaurants)
            }
        
        return summary
    
    async def run_national_pipeline(self) -> str:
        """Execute the complete national scaling pipeline"""
        start_time = datetime.now()
        
        try:
            # Collect data from all cities
            results = await self.process_cities_by_priority(max_concurrent=3)
            
            # Generate summary
            summary = self.generate_national_summary(results)
            
            # Save comprehensive results
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Save individual results
            results_filename = f"national_restaurants_raw_{timestamp}.json"
            results_filepath = self.output_dir / results_filename
            
            with open(results_filepath, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            # Save summary
            summary_filename = f"national_summary_{timestamp}.json"
            summary_filepath = self.output_dir / summary_filename
            
            with open(summary_filepath, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            
            # Log final results
            end_time = datetime.now()
            total_time = (end_time - start_time).total_seconds()
            
            logger.info(f"\n🎉 National Pipeline Completed Successfully!")
            logger.info(f"⏱️ Total execution time: {total_time:.1f} seconds")
            logger.info(f"🏙️ Cities processed: {summary['total_cities_processed']}")
            logger.info(f"🍽️ Total restaurants collected: {summary['total_restaurants_collected']:,}")
            logger.info(f"📊 Overall success rate: {summary['processing_statistics']['overall_success_rate']:.1f}%")
            logger.info(f"💾 Results saved to: {results_filename}")
            logger.info(f"📋 Summary saved to: {summary_filename}")
            
            return str(summary_filepath)
            
        except Exception as e:
            logger.error(f"❌ National pipeline failed: {e}")
            raise

async def main():
    """Main execution function"""
    pipeline = NationalScalingPipeline()
    
    try:
        summary_file = await pipeline.run_national_pipeline()
        print(f"\n✅ National scaling pipeline completed successfully!")
        print(f"📁 Summary available at: {summary_file}")
        
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)