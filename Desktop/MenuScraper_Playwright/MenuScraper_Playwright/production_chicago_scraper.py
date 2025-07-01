#!/usr/bin/env python3
"""
Production Chicago Restaurant Menu Scraper
Scales the Practical ML Scraper for comprehensive Chicago restaurant data collection
"""

import asyncio
import json
import time
from datetime import datetime
from typing import List, Dict, Any
import logging
from pathlib import Path

# Import the best-performing scraper
from practical_ml_scraper import PracticalMLScraper

class ProductionChicagoScraper:
    def __init__(self, batch_size: int = 50, delay_between_batches: float = 30.0):
        """
        Initialize production scraper for Chicago restaurants
        
        Args:
            batch_size: Number of restaurants to process per batch
            delay_between_batches: Seconds to wait between batches
        """
        self.scraper = PracticalMLScraper()
        self.batch_size = batch_size
        self.delay_between_batches = delay_between_batches
        self.setup_logging()
        
    def setup_logging(self):
        """Setup comprehensive logging for production monitoring"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'production_scraping_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def load_chicago_restaurants(self) -> List[Dict[str, str]]:
        """Load comprehensive Chicago restaurant dataset"""
        # Extended Chicago restaurant list for production scraping
        chicago_restaurants = [
            # High-end dining
            {"name": "Alinea", "url": "https://www.yelp.com/biz/alinea-chicago"},
            {"name": "Girl & the Goat", "url": "https://www.yelp.com/biz/girl-and-the-goat-chicago"},
            {"name": "Au Cheval", "url": "https://www.yelp.com/biz/au-cheval-chicago"},
            {"name": "The Publican", "url": "https://www.yelp.com/biz/the-publican-chicago"},
            {"name": "Gibsons Bar & Steakhouse", "url": "https://www.yelp.com/biz/gibsons-bar-and-steakhouse-chicago"},
            {"name": "RPM Steak", "url": "https://www.yelp.com/biz/rpm-steak-chicago"},
            {"name": "The Purple Pig", "url": "https://www.yelp.com/biz/the-purple-pig-chicago"},
            {"name": "Blackbird", "url": "https://www.yelp.com/biz/blackbird-chicago"},
            {"name": "Next Restaurant", "url": "https://www.yelp.com/biz/next-restaurant-chicago"},
            {"name": "Oriole", "url": "https://www.yelp.com/biz/oriole-chicago"},
            
            # Popular casual dining
            {"name": "Portillo's", "url": "https://www.yelp.com/biz/portillos-chicago"},
            {"name": "Lou Malnati's Pizzeria", "url": "https://www.yelp.com/biz/lou-malnatis-pizzeria-chicago"},
            {"name": "Pequod's Pizza", "url": "https://www.yelp.com/biz/pequods-pizza-chicago"},
            {"name": "The Gage", "url": "https://www.yelp.com/biz/the-gage-chicago"},
            {"name": "Kuma's Corner", "url": "https://www.yelp.com/biz/kumas-corner-chicago"},
            {"name": "Big Star", "url": "https://www.yelp.com/biz/big-star-chicago"},
            {"name": "Wildberry Pancakes & Cafe", "url": "https://www.yelp.com/biz/wildberry-pancakes-and-cafe-chicago"},
            {"name": "The Bongo Room", "url": "https://www.yelp.com/biz/the-bongo-room-chicago"},
            {"name": "Xoco", "url": "https://www.yelp.com/biz/xoco-chicago"},
            {"name": "Frontera Grill", "url": "https://www.yelp.com/biz/frontera-grill-chicago"},
            
            # International cuisine
            {"name": "Arun's Thai Restaurant", "url": "https://www.yelp.com/biz/aruns-thai-restaurant-chicago"},
            {"name": "Spiaggia", "url": "https://www.yelp.com/biz/spiaggia-chicago"},
            {"name": "Monteverde", "url": "https://www.yelp.com/biz/monteverde-chicago"},
            {"name": "Smoque BBQ", "url": "https://www.yelp.com/biz/smoque-bbq-chicago"},
            {"name": "Hopleaf Bar", "url": "https://www.yelp.com/biz/hopleaf-bar-chicago"},
            {"name": "Lao Sze Chuan", "url": "https://www.yelp.com/biz/lao-sze-chuan-chicago"},
            {"name": "Avec", "url": "https://www.yelp.com/biz/avec-chicago"},
            {"name": "Longman & Eagle", "url": "https://www.yelp.com/biz/longman-and-eagle-chicago"},
            {"name": "Mindy's Bakery", "url": "https://www.yelp.com/biz/mindys-bakery-chicago"},
            {"name": "Spacca Napoli", "url": "https://www.yelp.com/biz/spacca-napoli-chicago"},
            
            # Breakfast & brunch
            {"name": "Ann Sather", "url": "https://www.yelp.com/biz/ann-sather-chicago"},
            {"name": "Yolk", "url": "https://www.yelp.com/biz/yolk-chicago"},
            {"name": "Lou Mitchell's", "url": "https://www.yelp.com/biz/lou-mitchells-chicago"},
            {"name": "Nookies", "url": "https://www.yelp.com/biz/nookies-chicago"},
            {"name": "Jam", "url": "https://www.yelp.com/biz/jam-chicago"},
            
            # Neighborhood gems
            {"name": "Hot Doug's", "url": "https://www.yelp.com/biz/hot-dougs-chicago"},
            {"name": "Al's Beef", "url": "https://www.yelp.com/biz/als-beef-chicago"},
            {"name": "Johnnie's Beef", "url": "https://www.yelp.com/biz/johnnies-beef-chicago"},
            {"name": "Superdawg Drive-In", "url": "https://www.yelp.com/biz/superdawg-drive-in-chicago"},
            {"name": "Chicago Pizza & Oven Grinder Co.", "url": "https://www.yelp.com/biz/chicago-pizza-and-oven-grinder-co-chicago"},
            {"name": "Pequod's Deep Dish", "url": "https://www.yelp.com/biz/pequods-deep-dish-chicago"},
            
            # Additional popular spots
            {"name": "The Aviary", "url": "https://www.yelp.com/biz/the-aviary-chicago"},
            {"name": "Roister", "url": "https://www.yelp.com/biz/roister-chicago"},
            {"name": "Smyth", "url": "https://www.yelp.com/biz/smyth-chicago"},
            {"name": "Boka", "url": "https://www.yelp.com/biz/boka-chicago"},
            {"name": "Topolobampo", "url": "https://www.yelp.com/biz/topolobampo-chicago"},
            {"name": "Schwa", "url": "https://www.yelp.com/biz/schwa-chicago"},
            {"name": "Acadia", "url": "https://www.yelp.com/biz/acadia-chicago"},
            {"name": "Everest", "url": "https://www.yelp.com/biz/everest-chicago"},
            {"name": "Grace", "url": "https://www.yelp.com/biz/grace-chicago"},
            {"name": "Sixteen", "url": "https://www.yelp.com/biz/sixteen-chicago"},
            
            # More neighborhood favorites
            {"name": "Kiki's Bistro", "url": "https://www.yelp.com/biz/kikis-bistro-chicago"},
            {"name": "Piece Brewery", "url": "https://www.yelp.com/biz/piece-brewery-chicago"},
            {"name": "Revolution Brewing", "url": "https://www.yelp.com/biz/revolution-brewing-chicago"},
            {"name": "Half Acre Beer Company", "url": "https://www.yelp.com/biz/half-acre-beer-company-chicago"},
            {"name": "Goose Island Brewery", "url": "https://www.yelp.com/biz/goose-island-brewery-chicago"},
            {"name": "Lagunitas Brewing Company", "url": "https://www.yelp.com/biz/lagunitas-brewing-company-chicago"},
            {"name": "Begyle Brewing", "url": "https://www.yelp.com/biz/begyle-brewing-chicago"},
            {"name": "Metropolitan Brewing", "url": "https://www.yelp.com/biz/metropolitan-brewing-chicago"},
            {"name": "Pipeworks Brewing Company", "url": "https://www.yelp.com/biz/pipeworks-brewing-company-chicago"},
            {"name": "Off Color Brewing", "url": "https://www.yelp.com/biz/off-color-brewing-chicago"},
            
            # Ethnic cuisine expansion
            {"name": "Parachute", "url": "https://www.yelp.com/biz/parachute-chicago"},
            {"name": "Sepia", "url": "https://www.yelp.com/biz/sepia-chicago"},
            {"name": "Nico Osteria", "url": "https://www.yelp.com/biz/nico-osteria-chicago"},
            {"name": "Dusek's", "url": "https://www.yelp.com/biz/duseks-chicago"},
            {"name": "Publican Quality Meats", "url": "https://www.yelp.com/biz/publican-quality-meats-chicago"},
            {"name": "Dove's Luncheonette", "url": "https://www.yelp.com/biz/doves-luncheonette-chicago"},
            {"name": "Passerotto", "url": "https://www.yelp.com/biz/passerotto-chicago"},
            {"name": "Osteria Langhe", "url": "https://www.yelp.com/biz/osteria-langhe-chicago"},
            {"name": "Coco Pazzo", "url": "https://www.yelp.com/biz/coco-pazzo-chicago"},
            {"name": "Quartino Ristorante", "url": "https://www.yelp.com/biz/quartino-ristorante-chicago"},
            
            # Additional diverse options
            {"name": "Mott St", "url": "https://www.yelp.com/biz/mott-st-chicago"},
            {"name": "Belly Q", "url": "https://www.yelp.com/biz/belly-q-chicago"},
            {"name": "Urban Belly", "url": "https://www.yelp.com/biz/urban-belly-chicago"},
            {"name": "Ruxbin Kitchen", "url": "https://www.yelp.com/biz/ruxbin-kitchen-chicago"},
            {"name": "Takashi", "url": "https://www.yelp.com/biz/takashi-chicago"},
            {"name": "Mirai Sushi", "url": "https://www.yelp.com/biz/mirai-sushi-chicago"},
            {"name": "Katsu Japanese Restaurant", "url": "https://www.yelp.com/biz/katsu-japanese-restaurant-chicago"},
            {"name": "Arami", "url": "https://www.yelp.com/biz/arami-chicago"},
            {"name": "Miku Sushi", "url": "https://www.yelp.com/biz/miku-sushi-chicago"},
            {"name": "Juno Sushi", "url": "https://www.yelp.com/biz/juno-sushi-chicago"},
            
            # Expanding to 100 total restaurants
            {"name": "Cafe Spiaggia", "url": "https://www.yelp.com/biz/cafe-spiaggia-chicago"},
            {"name": "Gibsons Italia", "url": "https://www.yelp.com/biz/gibsons-italia-chicago"},
            {"name": "RPM Italian", "url": "https://www.yelp.com/biz/rpm-italian-chicago"},
            {"name": "Maple & Ash", "url": "https://www.yelp.com/biz/maple-and-ash-chicago"},
            {"name": "Swift & Sons", "url": "https://www.yelp.com/biz/swift-and-sons-chicago"},
            {"name": "Bavette's Bar & Boeuf", "url": "https://www.yelp.com/biz/bavettes-bar-and-boeuf-chicago"},
            {"name": "Chicago Cut Steakhouse", "url": "https://www.yelp.com/biz/chicago-cut-steakhouse-chicago"},
            {"name": "Mastro's Steakhouse", "url": "https://www.yelp.com/biz/mastros-steakhouse-chicago"},
            {"name": "The Capital Grille", "url": "https://www.yelp.com/biz/the-capital-grille-chicago"},
            {"name": "Morton's The Steakhouse", "url": "https://www.yelp.com/biz/mortons-the-steakhouse-chicago"},
            {"name": "Ruth's Chris Steak House", "url": "https://www.yelp.com/biz/ruths-chris-steak-house-chicago"},
            {"name": "Joe's Seafood Prime Steak & Stone Crab", "url": "https://www.yelp.com/biz/joes-seafood-prime-steak-and-stone-crab-chicago"},
            {"name": "Shaw's Crab House", "url": "https://www.yelp.com/biz/shaws-crab-house-chicago"},
            {"name": "GT Fish & Oyster", "url": "https://www.yelp.com/biz/gt-fish-and-oyster-chicago"},
            {"name": "Oyster Bah", "url": "https://www.yelp.com/biz/oyster-bah-chicago"},
            {"name": "Lure Fishbar", "url": "https://www.yelp.com/biz/lure-fishbar-chicago"},
            {"name": "Catch 35", "url": "https://www.yelp.com/biz/catch-35-chicago"},
            {"name": "Riva Crabhouse", "url": "https://www.yelp.com/biz/riva-crabhouse-chicago"},
            {"name": "Chicago Fish House", "url": "https://www.yelp.com/biz/chicago-fish-house-chicago"},
            {"name": "Fulton Market Kitchen", "url": "https://www.yelp.com/biz/fulton-market-kitchen-chicago"}
        ]
        
        self.logger.info(f"Loaded {len(chicago_restaurants)} Chicago restaurants for production scraping")
        return chicago_restaurants
        
    async def scrape_batch(self, restaurants: List[Dict[str, str]], batch_num: int) -> List[Dict[str, Any]]:
        """Scrape a batch of restaurants with error handling and monitoring"""
        self.logger.info(f"Starting batch {batch_num} with {len(restaurants)} restaurants")
        batch_results = []
        
        # Setup browser for this batch
        if not await self.scraper.setup_browser():
            self.logger.error(f"Failed to setup browser for batch {batch_num}")
            return []
            
        for i, restaurant in enumerate(restaurants):
            try:
                self.logger.info(f"Batch {batch_num}, Restaurant {i+1}/{len(restaurants)}: {restaurant['name']}")
                start_time = time.time()
                
                # Scrape restaurant menu
                result = await self.scraper.extract_menu_items(
                    restaurant['url']
                )
                
                # Add restaurant name to result
                result['restaurant_name'] = restaurant['name']
                result['url'] = restaurant['url']
                
                processing_time = time.time() - start_time
                
                # Add batch metadata
                result.update({
                    'batch_number': batch_num,
                    'batch_position': i + 1,
                    'processing_time': processing_time,
                    'timestamp': datetime.now().isoformat()
                })
                
                batch_results.append(result)
                
                # Log progress
                if result.get('scraping_success', False):
                    items_count = result.get('total_items', 0)
                    self.logger.info(f"✓ Success: {restaurant['name']} - {items_count} items in {processing_time:.2f}s")
                else:
                    error = result.get('error', 'Unknown error')
                    self.logger.warning(f"✗ Failed: {restaurant['name']} - {error}")
                    
                # Small delay between restaurants to be respectful
                await asyncio.sleep(2)
                
            except Exception as e:
                self.logger.error(f"Critical error processing {restaurant['name']}: {str(e)}")
                batch_results.append({
                    'restaurant_name': restaurant['name'],
                    'url': restaurant['url'],
                    'scraping_success': False,
                    'error': f"Critical error: {str(e)}",
                    'batch_number': batch_num,
                    'batch_position': i + 1,
                    'timestamp': datetime.now().isoformat()
                })
                
        # Cleanup browser after batch
        await self.scraper.cleanup()
        
        self.logger.info(f"Completed batch {batch_num}")
        return batch_results
        
    def calculate_comprehensive_metrics(self, all_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate comprehensive production metrics"""
        total_restaurants = len(all_results)
        successful_scrapes = [r for r in all_results if r.get('scraping_success', False)]
        failed_scrapes = [r for r in all_results if not r.get('scraping_success', False)]
        
        total_items = sum(r.get('total_items', 0) for r in successful_scrapes)
        total_processing_time = sum(r.get('processing_time', 0) for r in all_results)
        
        # Success rate analysis
        success_rate = (len(successful_scrapes) / total_restaurants * 100) if total_restaurants > 0 else 0
        
        # Performance metrics
        processing_times = [r.get('processing_time', 0) for r in all_results if r.get('processing_time', 0) > 0]
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
        
        # Quality metrics
        items_with_prices = sum(1 for r in successful_scrapes 
                              if r.get('price_coverage', 0) > 0)
        
        # Allergen analysis
        total_allergen_detections = sum(len(r.get('allergen_summary', {})) for r in successful_scrapes)
        
        # Error analysis
        error_types = {}
        for result in failed_scrapes:
            error = result.get('error', 'Unknown error')
            error_types[error] = error_types.get(error, 0) + 1
            
        # Batch performance
        batch_performance = {}
        for result in all_results:
            batch_num = result.get('batch_number', 0)
            if batch_num not in batch_performance:
                batch_performance[batch_num] = {'total': 0, 'successful': 0}
            batch_performance[batch_num]['total'] += 1
            if result.get('scraping_success', False):
                batch_performance[batch_num]['successful'] += 1
                
        return {
            'production_summary': {
                'total_restaurants_processed': total_restaurants,
                'successful_scrapes': len(successful_scrapes),
                'failed_scrapes': len(failed_scrapes),
                'overall_success_rate': round(success_rate, 2),
                'total_menu_items_extracted': total_items,
                'avg_items_per_success': round(total_items / len(successful_scrapes), 2) if successful_scrapes else 0,
                'total_processing_time_minutes': round(total_processing_time / 60, 2),
                'avg_processing_time_seconds': round(avg_processing_time, 2)
            },
            'quality_metrics': {
                'restaurants_with_prices': items_with_prices,
                'price_coverage_rate': round(items_with_prices / len(successful_scrapes) * 100, 2) if successful_scrapes else 0,
                'total_allergen_detections': total_allergen_detections,
                'avg_allergens_per_restaurant': round(total_allergen_detections / len(successful_scrapes), 2) if successful_scrapes else 0
            },
            'performance_analysis': {
                'fastest_scrape_seconds': min(processing_times) if processing_times else 0,
                'slowest_scrape_seconds': max(processing_times) if processing_times else 0,
                'restaurants_per_hour': round(3600 / avg_processing_time, 2) if avg_processing_time > 0 else 0,
                'estimated_time_for_1000_restaurants_hours': round(1000 * avg_processing_time / 3600, 2) if avg_processing_time > 0 else 0
            },
            'error_analysis': error_types,
            'batch_performance': batch_performance,
            'production_recommendations': {
                'optimal_batch_size': 25 if success_rate > 30 else 15,
                'recommended_delay_between_batches_minutes': 2 if success_rate > 40 else 5,
                'estimated_daily_capacity': round(8 * 3600 / avg_processing_time, 0) if avg_processing_time > 0 else 0,
                'production_readiness_score': min(100, success_rate * 2) if success_rate > 0 else 0
            }
        }
        
    async def run_production_scraping(self) -> str:
        """Execute full production scraping of Chicago restaurants"""
        start_time = time.time()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        self.logger.info("=" * 80)
        self.logger.info("STARTING PRODUCTION CHICAGO RESTAURANT SCRAPING")
        self.logger.info(f"Timestamp: {timestamp}")
        self.logger.info(f"Batch size: {self.batch_size}")
        self.logger.info(f"Delay between batches: {self.delay_between_batches}s")
        self.logger.info("=" * 80)
        
        # Load restaurant list
        restaurants = self.load_chicago_restaurants()
        total_restaurants = len(restaurants)
        
        # Calculate number of batches
        num_batches = (total_restaurants + self.batch_size - 1) // self.batch_size
        self.logger.info(f"Processing {total_restaurants} restaurants in {num_batches} batches")
        
        all_results = []
        
        # Process restaurants in batches
        for batch_num in range(num_batches):
            start_idx = batch_num * self.batch_size
            end_idx = min(start_idx + self.batch_size, total_restaurants)
            batch_restaurants = restaurants[start_idx:end_idx]
            
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"BATCH {batch_num + 1}/{num_batches}")
            self.logger.info(f"Restaurants {start_idx + 1}-{end_idx} of {total_restaurants}")
            self.logger.info(f"{'='*60}")
            
            # Scrape batch
            batch_results = await self.scrape_batch(batch_restaurants, batch_num + 1)
            all_results.extend(batch_results)
            
            # Progress update
            completed = len(all_results)
            progress = (completed / total_restaurants) * 100
            self.logger.info(f"Progress: {completed}/{total_restaurants} ({progress:.1f}%)")
            
            # Delay between batches (except for the last batch)
            if batch_num < num_batches - 1:
                self.logger.info(f"Waiting {self.delay_between_batches}s before next batch...")
                await asyncio.sleep(self.delay_between_batches)
                
        # Calculate comprehensive metrics
        self.logger.info("\nCalculating production metrics...")
        metrics = self.calculate_comprehensive_metrics(all_results)
        
        # Prepare final results
        final_results = {
            'scraper_info': {
                'scraper_name': 'Production Chicago Scraper',
                'base_scraper': 'Practical ML-Inspired v1.0',
                'production_version': '1.0',
                'execution_timestamp': timestamp,
                'total_execution_time_minutes': round((time.time() - start_time) / 60, 2)
            },
            'production_metrics': metrics,
            'detailed_results': all_results
        }
        
        # Save results
        output_file = f"production_chicago_results_{timestamp}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(final_results, f, indent=2, ensure_ascii=False)
            
        # Final summary
        self.logger.info("\n" + "="*80)
        self.logger.info("PRODUCTION SCRAPING COMPLETED")
        self.logger.info(f"Results saved to: {output_file}")
        self.logger.info(f"Total restaurants processed: {metrics['production_summary']['total_restaurants_processed']}")
        self.logger.info(f"Success rate: {metrics['production_summary']['overall_success_rate']}%")
        self.logger.info(f"Total items extracted: {metrics['production_summary']['total_menu_items_extracted']}")
        self.logger.info(f"Total execution time: {final_results['scraper_info']['total_execution_time_minutes']} minutes")
        self.logger.info("="*80)
        
        return output_file

async def main():
    """Main execution function"""
    # Initialize production scraper with optimized settings
    scraper = ProductionChicagoScraper(
        batch_size=25,  # Moderate batch size for stability
        delay_between_batches=30.0  # 30 second delay between batches
    )
    
    # Run production scraping
    output_file = await scraper.run_production_scraping()
    print(f"\nProduction scraping completed. Results saved to: {output_file}")
    
if __name__ == "__main__":
    asyncio.run(main())