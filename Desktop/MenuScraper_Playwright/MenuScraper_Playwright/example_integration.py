#!/usr/bin/env python3
"""
Example integration script demonstrating how to use the MenuScraper with Supabase database storage.

This script shows how to:
1. Set up the Supabase integration
2. Run scrapers and save results to the database
3. Query the stored data
4. Start the API server for frontend integration

Usage:
    python example_integration.py --demo
    python example_integration.py --scrape-url https://example-restaurant.com
    python example_integration.py --start-api
"""

import asyncio
import argparse
import sys
import os
from typing import Dict, List, Any
from datetime import datetime
import json

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from supabase_integration import SupabaseIntegration, RestaurantData, MenuItemData
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MenuScraperIntegration:
    """Integration class that combines scraping with database storage"""
    
    def __init__(self):
        """Initialize the integration with Supabase connection"""
        load_dotenv()
        
        try:
            self.db = SupabaseIntegration()
            logger.info("Successfully connected to Supabase")
        except Exception as e:
            logger.error(f"Failed to connect to Supabase: {e}")
            logger.error("Please check your SUPABASE_URL and SUPABASE_KEY environment variables")
            sys.exit(1)
    
    async def scrape_and_store(self, restaurant_url: str, scraper_type: str = 'auto') -> Dict[str, Any]:
        """
        Scrape a restaurant and store results in Supabase
        
        Args:
            restaurant_url: URL of the restaurant to scrape
            scraper_type: Type of scraper to use
            
        Returns:
            Summary of the scraping and storage operation
        """
        logger.info(f"Starting scrape and store operation for: {restaurant_url}")
        
        try:
            # For demonstration, we'll create mock data
            # In a real implementation, you would call your actual scrapers here
            scraped_data = await self._mock_scrape_restaurant(restaurant_url)
            
            # Store the scraped data in Supabase
            summary = await self.db.save_scraping_results(scraped_data, scraper_type)
            
            logger.info(f"Scraping completed. Summary: {summary}")
            return summary
            
        except Exception as e:
            logger.error(f"Error during scrape and store: {e}")
            return {
                'success': False,
                'error': str(e),
                'restaurant_id': None,
                'menu_items_created': 0
            }
    
    async def _mock_scrape_restaurant(self, url: str) -> Dict[str, Any]:
        """
        Mock scraper that generates sample restaurant data
        In a real implementation, this would be replaced with actual scraping logic
        """
        logger.info("Running mock scraper (replace with actual scraper integration)")
        
        # Simulate scraping delay
        await asyncio.sleep(2)
        
        # Generate mock restaurant data
        restaurant_name = f"Restaurant from {url.split('//')[-1].split('/')[0]}"
        
        mock_data = {
            'name': restaurant_name,
            'url': url,
            'city': 'Chicago',
            'state': 'IL',
            'cuisine_type': 'American',
            'source_platform': 'mock_scraper',
            'items': [
                {
                    'name': 'Classic Burger',
                    'description': 'Beef patty with lettuce, tomato, and cheese',
                    'price': '12.99',
                    'category': 'Burgers',
                    'allergens': ['dairy', 'gluten'],
                    'dietary_tags': [],
                    'confidence_score': 0.95,
                    'extraction_method': 'mock_scraper'
                },
                {
                    'name': 'Caesar Salad',
                    'description': 'Romaine lettuce with parmesan and croutons',
                    'price': '9.99',
                    'category': 'Salads',
                    'allergens': ['dairy', 'eggs'],
                    'dietary_tags': ['vegetarian'],
                    'confidence_score': 0.88,
                    'extraction_method': 'mock_scraper'
                },
                {
                    'name': 'Grilled Chicken',
                    'description': 'Herb-seasoned grilled chicken breast',
                    'price': '15.99',
                    'category': 'Main Courses',
                    'allergens': [],
                    'dietary_tags': ['gluten-free', 'high-protein'],
                    'confidence_score': 0.92,
                    'extraction_method': 'mock_scraper'
                },
                {
                    'name': 'Chocolate Cake',
                    'description': 'Rich chocolate cake with frosting',
                    'price': '6.99',
                    'category': 'Desserts',
                    'allergens': ['dairy', 'eggs', 'gluten'],
                    'dietary_tags': ['vegetarian'],
                    'confidence_score': 0.90,
                    'extraction_method': 'mock_scraper'
                },
                {
                    'name': 'Vegan Buddha Bowl',
                    'description': 'Quinoa, vegetables, and tahini dressing',
                    'price': '13.99',
                    'category': 'Healthy Options',
                    'allergens': ['sesame'],
                    'dietary_tags': ['vegan', 'gluten-free', 'healthy'],
                    'confidence_score': 0.87,
                    'extraction_method': 'mock_scraper'
                }
            ]
        }
        
        logger.info(f"Mock scraper found {len(mock_data['items'])} menu items")
        return mock_data
    
    async def query_restaurants(self, city: str = None, cuisine_type: str = None) -> List[Dict]:
        """
        Query restaurants from the database
        
        Args:
            city: Filter by city
            cuisine_type: Filter by cuisine type
            
        Returns:
            List of restaurants
        """
        try:
            restaurants = await self.db.get_restaurants(city=city, cuisine_type=cuisine_type)
            logger.info(f"Found {len(restaurants)} restaurants")
            return restaurants
        except Exception as e:
            logger.error(f"Error querying restaurants: {e}")
            return []
    
    async def query_menu_items(self, restaurant_id: str, category: str = None) -> List[Dict]:
        """
        Query menu items for a restaurant
        
        Args:
            restaurant_id: Restaurant UUID
            category: Optional category filter
            
        Returns:
            List of menu items
        """
        try:
            menu_items = await self.db.get_menu_items(restaurant_id, category=category)
            logger.info(f"Found {len(menu_items)} menu items")
            return menu_items
        except Exception as e:
            logger.error(f"Error querying menu items: {e}")
            return []
    
    async def search_menu_items(self, search_term: str, exclude_allergens: List[str] = None) -> List[Dict]:
        """
        Search menu items across all restaurants
        
        Args:
            search_term: Search term
            exclude_allergens: Allergens to exclude
            
        Returns:
            List of matching menu items
        """
        try:
            results = await self.db.search_menu_items(search_term, allergen_filter=exclude_allergens)
            logger.info(f"Found {len(results)} matching menu items")
            return results
        except Exception as e:
            logger.error(f"Error searching menu items: {e}")
            return []
    
    async def run_demo(self):
        """
        Run a comprehensive demo of the integration
        """
        logger.info("Starting MenuScraper + Supabase integration demo")
        
        # Demo URLs (replace with real restaurant URLs)
        demo_urls = [
            "https://example-restaurant-1.com",
            "https://example-restaurant-2.com"
        ]
        
        restaurant_ids = []
        
        # Scrape and store demo restaurants
        for url in demo_urls:
            logger.info(f"\n--- Scraping {url} ---")
            summary = await self.scrape_and_store(url, 'demo_scraper')
            
            if summary['success']:
                restaurant_ids.append(summary['restaurant_id'])
                logger.info(f"✓ Successfully stored {summary['menu_items_created']} menu items")
            else:
                logger.error(f"✗ Failed to scrape {url}: {summary.get('error', 'Unknown error')}")
        
        # Query and display results
        logger.info("\n--- Querying stored data ---")
        
        # Get all restaurants
        restaurants = await self.query_restaurants()
        logger.info(f"Total restaurants in database: {len(restaurants)}")
        
        # Get restaurants in Chicago
        chicago_restaurants = await self.query_restaurants(city='Chicago')
        logger.info(f"Restaurants in Chicago: {len(chicago_restaurants)}")
        
        # Search for specific items
        burger_items = await self.search_menu_items('burger')
        logger.info(f"Menu items containing 'burger': {len(burger_items)}")
        
        # Search excluding allergens
        dairy_free_items = await self.search_menu_items('salad', exclude_allergens=['dairy'])
        logger.info(f"Dairy-free salad items: {len(dairy_free_items)}")
        
        # Display sample restaurant details
        if restaurant_ids:
            sample_restaurant_id = restaurant_ids[0]
            logger.info(f"\n--- Sample restaurant details ({sample_restaurant_id}) ---")
            
            menu_items = await self.query_menu_items(sample_restaurant_id)
            logger.info(f"Menu items: {len(menu_items)}")
            
            # Get restaurant stats
            stats = await self.db.get_restaurant_stats(sample_restaurant_id)
            logger.info(f"Restaurant stats: {stats}")
        
        logger.info("\n--- Demo completed successfully! ---")
        logger.info("You can now start the API server with: python example_integration.py --start-api")

async def start_api_server():
    """
    Start the FastAPI server for frontend integration
    """
    logger.info("Starting API server...")
    
    try:
        import uvicorn
        from api_server import app
        
        # Start the server
        config = uvicorn.Config(
            app=app,
            host="0.0.0.0",
            port=8000,
            log_level="info",
            reload=True
        )
        
        server = uvicorn.Server(config)
        logger.info("API server starting at http://localhost:8000")
        logger.info("API documentation available at http://localhost:8000/docs")
        
        await server.serve()
        
    except ImportError:
        logger.error("FastAPI dependencies not installed. Run: pip install fastapi uvicorn")
    except Exception as e:
        logger.error(f"Error starting API server: {e}")

def main():
    """
    Main entry point with command line argument parsing
    """
    parser = argparse.ArgumentParser(description='MenuScraper + Supabase Integration')
    parser.add_argument('--demo', action='store_true', help='Run integration demo')
    parser.add_argument('--scrape-url', type=str, help='Scrape a specific restaurant URL')
    parser.add_argument('--start-api', action='store_true', help='Start the API server')
    parser.add_argument('--query-restaurants', action='store_true', help='Query and display restaurants')
    parser.add_argument('--city', type=str, help='Filter restaurants by city')
    parser.add_argument('--cuisine', type=str, help='Filter restaurants by cuisine type')
    
    args = parser.parse_args()
    
    if args.start_api:
        asyncio.run(start_api_server())
        return
    
    # Initialize integration
    integration = MenuScraperIntegration()
    
    async def run_commands():
        if args.demo:
            await integration.run_demo()
        
        elif args.scrape_url:
            logger.info(f"Scraping URL: {args.scrape_url}")
            summary = await integration.scrape_and_store(args.scrape_url)
            print(json.dumps(summary, indent=2, default=str))
        
        elif args.query_restaurants:
            restaurants = await integration.query_restaurants(city=args.city, cuisine_type=args.cuisine)
            print(json.dumps(restaurants, indent=2, default=str))
        
        else:
            parser.print_help()
            print("\nExamples:")
            print("  python example_integration.py --demo")
            print("  python example_integration.py --scrape-url https://restaurant.com")
            print("  python example_integration.py --start-api")
            print("  python example_integration.py --query-restaurants --city Chicago")
    
    asyncio.run(run_commands())

if __name__ == "__main__":
    main()