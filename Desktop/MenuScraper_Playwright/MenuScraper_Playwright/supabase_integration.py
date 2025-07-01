import os
import json
import asyncio
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timezone
import uuid
from supabase import create_client, Client
import logging
from dataclasses import dataclass, asdict
from decimal import Decimal

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class RestaurantData:
    """Data class for restaurant information"""
    name: str
    url: str
    website_url: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: str = 'USA'
    cuisine_type: Optional[str] = None
    price_range: Optional[str] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    business_hours: Optional[Dict] = None
    features: Optional[Dict] = None
    source_platform: Optional[str] = None
    source_id: Optional[str] = None

@dataclass
class MenuItemData:
    """Data class for menu item information"""
    restaurant_id: str
    name: str
    description: Optional[str] = None
    price: Optional[float] = None
    price_range: Optional[str] = None
    currency: str = 'USD'
    calories: Optional[int] = None
    serving_size: Optional[str] = None
    preparation_time: Optional[int] = None
    spice_level: Optional[int] = None
    is_available: bool = True
    is_featured: bool = False
    image_url: Optional[str] = None
    confidence_score: Optional[float] = None
    extraction_method: Optional[str] = None
    raw_text: Optional[str] = None
    category_name: Optional[str] = None
    allergens: Optional[List[str]] = None
    dietary_tags: Optional[List[str]] = None
    allergen_risk_level: Optional[str] = None

class SupabaseIntegration:
    """Comprehensive Supabase integration for MenuScraper data pipeline"""
    
    def __init__(self, supabase_url: str = None, supabase_key: str = None):
        """
        Initialize Supabase client
        
        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase anon/service key
        """
        self.supabase_url = supabase_url or os.getenv('SUPABASE_URL')
        self.supabase_key = supabase_key or os.getenv('SUPABASE_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Supabase URL and key must be provided via parameters or environment variables")
        
        self.client: Client = create_client(self.supabase_url, self.supabase_key)
        self.current_session_id: Optional[str] = None
        
        logger.info(f"Supabase client initialized for {self.supabase_url}")
    
    async def create_restaurant(self, restaurant_data: Union[RestaurantData, Dict]) -> Optional[str]:
        """
        Create or update restaurant record
        
        Args:
            restaurant_data: Restaurant information
            
        Returns:
            Restaurant ID if successful, None otherwise
        """
        try:
            if isinstance(restaurant_data, dict):
                restaurant_data = RestaurantData(**restaurant_data)
            
            # Check if restaurant already exists
            existing = self.client.table('restaurants').select('id').eq('url', restaurant_data.url).execute()
            
            restaurant_dict = asdict(restaurant_data)
            restaurant_dict['last_scraped_at'] = datetime.now(timezone.utc).isoformat()
            
            if existing.data:
                # Update existing restaurant
                restaurant_id = existing.data[0]['id']
                result = self.client.table('restaurants').update(restaurant_dict).eq('id', restaurant_id).execute()
                logger.info(f"Updated restaurant: {restaurant_data.name} (ID: {restaurant_id})")
            else:
                # Create new restaurant
                result = self.client.table('restaurants').insert(restaurant_dict).execute()
                restaurant_id = result.data[0]['id']
                logger.info(f"Created restaurant: {restaurant_data.name} (ID: {restaurant_id})")
            
            return restaurant_id
            
        except Exception as e:
            logger.error(f"Error creating/updating restaurant: {e}")
            return None
    
    async def create_menu_category(self, restaurant_id: str, category_name: str, description: str = None) -> Optional[str]:
        """
        Create menu category if it doesn't exist
        
        Args:
            restaurant_id: Restaurant UUID
            category_name: Category name
            description: Category description
            
        Returns:
            Category ID if successful
        """
        try:
            # Check if category exists
            existing = self.client.table('menu_categories').select('id').eq('restaurant_id', restaurant_id).eq('name', category_name).execute()
            
            if existing.data:
                return existing.data[0]['id']
            
            # Create new category
            category_data = {
                'restaurant_id': restaurant_id,
                'name': category_name,
                'description': description
            }
            
            result = self.client.table('menu_categories').insert(category_data).execute()
            category_id = result.data[0]['id']
            logger.info(f"Created menu category: {category_name} (ID: {category_id})")
            
            return category_id
            
        except Exception as e:
            logger.error(f"Error creating menu category: {e}")
            return None
    
    async def create_menu_item(self, menu_item_data: Union[MenuItemData, Dict]) -> Optional[str]:
        """
        Create menu item with allergens and dietary tags
        
        Args:
            menu_item_data: Menu item information
            
        Returns:
            Menu item ID if successful
        """
        try:
            if isinstance(menu_item_data, dict):
                menu_item_data = MenuItemData(**menu_item_data)
            
            # Handle category
            category_id = None
            if menu_item_data.category_name:
                category_id = await self.create_menu_category(
                    menu_item_data.restaurant_id, 
                    menu_item_data.category_name
                )
            
            # Prepare menu item data
            item_dict = asdict(menu_item_data)
            item_dict['category_id'] = category_id
            
            # Remove fields that don't belong in menu_items table
            fields_to_remove = ['category_name', 'allergens', 'dietary_tags', 'allergen_risk_level']
            for field in fields_to_remove:
                item_dict.pop(field, None)
            
            # Insert menu item
            result = self.client.table('menu_items').insert(item_dict).execute()
            menu_item_id = result.data[0]['id']
            
            # Handle allergens
            if menu_item_data.allergens:
                await self._link_allergens(menu_item_id, menu_item_data.allergens, menu_item_data.allergen_risk_level)
            
            # Handle dietary tags
            if menu_item_data.dietary_tags:
                await self._link_dietary_tags(menu_item_id, menu_item_data.dietary_tags)
            
            logger.info(f"Created menu item: {menu_item_data.name} (ID: {menu_item_id})")
            return menu_item_id
            
        except Exception as e:
            logger.error(f"Error creating menu item: {e}")
            return None
    
    async def _link_allergens(self, menu_item_id: str, allergens: List[str], risk_level: str = 'medium'):
        """
        Link allergens to menu item
        
        Args:
            menu_item_id: Menu item UUID
            allergens: List of allergen names
            risk_level: Risk level for allergens
        """
        try:
            # Get allergen IDs
            allergen_result = self.client.table('allergens').select('id, name').in_('name', allergens).execute()
            allergen_map = {item['name']: item['id'] for item in allergen_result.data}
            
            # Create allergen links
            allergen_links = []
            for allergen_name in allergens:
                if allergen_name in allergen_map:
                    allergen_links.append({
                        'menu_item_id': menu_item_id,
                        'allergen_id': allergen_map[allergen_name],
                        'risk_level': risk_level,
                        'detection_method': 'ml_pattern'
                    })
            
            if allergen_links:
                self.client.table('menu_item_allergens').insert(allergen_links).execute()
                logger.info(f"Linked {len(allergen_links)} allergens to menu item {menu_item_id}")
                
        except Exception as e:
            logger.error(f"Error linking allergens: {e}")
    
    async def _link_dietary_tags(self, menu_item_id: str, dietary_tags: List[str]):
        """
        Link dietary tags to menu item
        
        Args:
            menu_item_id: Menu item UUID
            dietary_tags: List of dietary tag names
        """
        try:
            # Get dietary tag IDs
            tag_result = self.client.table('dietary_tags').select('id, name').in_('name', dietary_tags).execute()
            tag_map = {item['name']: item['id'] for item in tag_result.data}
            
            # Create dietary tag links
            tag_links = []
            for tag_name in dietary_tags:
                if tag_name in tag_map:
                    tag_links.append({
                        'menu_item_id': menu_item_id,
                        'dietary_tag_id': tag_map[tag_name],
                        'detection_method': 'ml_pattern'
                    })
            
            if tag_links:
                self.client.table('menu_item_dietary_tags').insert(tag_links).execute()
                logger.info(f"Linked {len(tag_links)} dietary tags to menu item {menu_item_id}")
                
        except Exception as e:
            logger.error(f"Error linking dietary tags: {e}")
    
    async def start_scraping_session(self, restaurant_id: str, scraper_type: str, scraper_version: str = '1.0') -> str:
        """
        Start a new scraping session
        
        Args:
            restaurant_id: Restaurant UUID
            scraper_type: Type of scraper being used
            scraper_version: Version of the scraper
            
        Returns:
            Session ID
        """
        try:
            session_data = {
                'restaurant_id': restaurant_id,
                'scraper_type': scraper_type,
                'scraper_version': scraper_version,
                'status': 'running',
                'start_time': datetime.now(timezone.utc).isoformat()
            }
            
            result = self.client.table('scraping_sessions').insert(session_data).execute()
            session_id = result.data[0]['id']
            self.current_session_id = session_id
            
            logger.info(f"Started scraping session: {session_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"Error starting scraping session: {e}")
            return str(uuid.uuid4())  # Fallback to local UUID
    
    async def end_scraping_session(self, session_id: str, status: str, metrics: Dict = None, error_log: str = None):
        """
        End scraping session with results
        
        Args:
            session_id: Session UUID
            status: Final status (completed, failed, partial)
            metrics: Performance metrics
            error_log: Error information if any
        """
        try:
            update_data = {
                'end_time': datetime.now(timezone.utc).isoformat(),
                'status': status
            }
            
            if metrics:
                update_data.update({
                    'total_items_found': metrics.get('total_items', 0),
                    'items_processed': metrics.get('items_processed', 0),
                    'items_with_prices': metrics.get('items_with_prices', 0),
                    'items_with_allergens': metrics.get('items_with_allergens', 0),
                    'average_confidence': metrics.get('average_confidence', 0),
                    'extraction_methods': metrics.get('extraction_methods', {}),
                    'performance_metrics': metrics
                })
            
            if error_log:
                update_data['error_log'] = error_log
            
            self.client.table('scraping_sessions').update(update_data).eq('id', session_id).execute()
            logger.info(f"Ended scraping session: {session_id} with status: {status}")
            
        except Exception as e:
            logger.error(f"Error ending scraping session: {e}")
    
    async def save_scraping_results(self, restaurant_data: Dict, scraper_type: str = 'unknown') -> Dict[str, Any]:
        """
        Save complete scraping results to database
        
        Args:
            restaurant_data: Complete restaurant and menu data
            scraper_type: Type of scraper used
            
        Returns:
            Summary of saved data
        """
        summary = {
            'restaurant_id': None,
            'menu_items_created': 0,
            'categories_created': 0,
            'allergens_linked': 0,
            'session_id': None,
            'success': False,
            'errors': []
        }
        
        try:
            # Create restaurant
            restaurant_info = RestaurantData(
                name=restaurant_data.get('name', 'Unknown Restaurant'),
                url=restaurant_data.get('url', ''),
                cuisine_type=restaurant_data.get('cuisine_type'),
                city=restaurant_data.get('city'),
                state=restaurant_data.get('state'),
                source_platform=restaurant_data.get('source_platform', 'web_scraper')
            )
            
            restaurant_id = await self.create_restaurant(restaurant_info)
            if not restaurant_id:
                summary['errors'].append('Failed to create restaurant')
                return summary
            
            summary['restaurant_id'] = restaurant_id
            
            # Start scraping session
            session_id = await self.start_scraping_session(restaurant_id, scraper_type)
            summary['session_id'] = session_id
            
            # Process menu items
            menu_items = restaurant_data.get('items', [])
            categories_created = set()
            
            for item_data in menu_items:
                try:
                    # Prepare menu item data
                    menu_item = MenuItemData(
                        restaurant_id=restaurant_id,
                        name=item_data.get('name', 'Unknown Item'),
                        description=item_data.get('description'),
                        price=self._safe_float(item_data.get('price')),
                        confidence_score=self._safe_float(item_data.get('confidence_score')),
                        extraction_method=item_data.get('extraction_method'),
                        raw_text=item_data.get('raw_text'),
                        category_name=item_data.get('category'),
                        allergens=item_data.get('allergens', []),
                        dietary_tags=item_data.get('dietary_tags', []),
                        allergen_risk_level=item_data.get('allergen_risk_level', 'medium')
                    )
                    
                    menu_item_id = await self.create_menu_item(menu_item)
                    if menu_item_id:
                        summary['menu_items_created'] += 1
                        if menu_item.category_name:
                            categories_created.add(menu_item.category_name)
                        if menu_item.allergens:
                            summary['allergens_linked'] += len(menu_item.allergens)
                    
                except Exception as e:
                    summary['errors'].append(f"Error processing menu item: {e}")
                    continue
            
            summary['categories_created'] = len(categories_created)
            
            # Calculate session metrics
            metrics = {
                'total_items': len(menu_items),
                'items_processed': summary['menu_items_created'],
                'items_with_prices': len([item for item in menu_items if item.get('price')]),
                'items_with_allergens': len([item for item in menu_items if item.get('allergens')]),
                'average_confidence': self._calculate_average_confidence(menu_items),
                'extraction_methods': self._get_extraction_methods(menu_items)
            }
            
            # End scraping session
            status = 'completed' if summary['menu_items_created'] > 0 else 'failed'
            await self.end_scraping_session(session_id, status, metrics)
            
            summary['success'] = summary['menu_items_created'] > 0
            logger.info(f"Saved scraping results: {summary['menu_items_created']} items for restaurant {restaurant_id}")
            
        except Exception as e:
            summary['errors'].append(f"Critical error: {e}")
            logger.error(f"Error saving scraping results: {e}")
            
            # End session with error
            if summary['session_id']:
                await self.end_scraping_session(summary['session_id'], 'failed', error_log=str(e))
        
        return summary
    
    def _safe_float(self, value: Any) -> Optional[float]:
        """Safely convert value to float"""
        if value is None:
            return None
        try:
            if isinstance(value, str):
                # Remove currency symbols and commas
                value = value.replace('$', '').replace(',', '').strip()
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def _calculate_average_confidence(self, items: List[Dict]) -> float:
        """Calculate average confidence score"""
        confidence_scores = [self._safe_float(item.get('confidence_score')) for item in items]
        valid_scores = [score for score in confidence_scores if score is not None]
        return sum(valid_scores) / len(valid_scores) if valid_scores else 0.0
    
    def _get_extraction_methods(self, items: List[Dict]) -> Dict[str, int]:
        """Get extraction method statistics"""
        methods = {}
        for item in items:
            method = item.get('extraction_method', 'unknown')
            methods[method] = methods.get(method, 0) + 1
        return methods
    
    # API Query Methods for Frontend Integration
    
    async def get_restaurants(self, city: str = None, cuisine_type: str = None, limit: int = 50) -> List[Dict]:
        """
        Get restaurants with optional filtering
        
        Args:
            city: Filter by city
            cuisine_type: Filter by cuisine type
            limit: Maximum number of results
            
        Returns:
            List of restaurant data
        """
        try:
            query = self.client.table('restaurant_summary').select('*')
            
            if city:
                query = query.eq('city', city)
            if cuisine_type:
                query = query.eq('cuisine_type', cuisine_type)
            
            result = query.limit(limit).execute()
            return result.data
            
        except Exception as e:
            logger.error(f"Error fetching restaurants: {e}")
            return []
    
    async def get_menu_items(self, restaurant_id: str, category: str = None) -> List[Dict]:
        """
        Get menu items for a restaurant
        
        Args:
            restaurant_id: Restaurant UUID
            category: Optional category filter
            
        Returns:
            List of menu items with details
        """
        try:
            query = self.client.table('menu_items_with_details').select('*').eq('restaurant_id', restaurant_id)
            
            if category:
                query = query.eq('category_name', category)
            
            result = query.execute()
            return result.data
            
        except Exception as e:
            logger.error(f"Error fetching menu items: {e}")
            return []
    
    async def search_menu_items(self, search_term: str, allergen_filter: List[str] = None) -> List[Dict]:
        """
        Search menu items by name/description with allergen filtering
        
        Args:
            search_term: Search term for menu items
            allergen_filter: List of allergens to exclude
            
        Returns:
            List of matching menu items
        """
        try:
            # Use full-text search
            query = self.client.table('menu_items_with_details').select('*')
            
            # Add text search (this would need to be implemented with proper FTS)
            # For now, use simple text matching
            result = query.execute()
            
            # Filter results in Python (could be optimized with database queries)
            filtered_results = []
            for item in result.data:
                # Text search
                if search_term.lower() in item['name'].lower() or \
                   (item['description'] and search_term.lower() in item['description'].lower()):
                    
                    # Allergen filter
                    if allergen_filter:
                        item_allergens = item.get('allergens', [])
                        if any(allergen in item_allergens for allergen in allergen_filter):
                            continue  # Skip items with filtered allergens
                    
                    filtered_results.append(item)
            
            return filtered_results[:50]  # Limit results
            
        except Exception as e:
            logger.error(f"Error searching menu items: {e}")
            return []
    
    async def get_restaurant_stats(self, restaurant_id: str) -> Dict:
        """
        Get comprehensive restaurant statistics
        
        Args:
            restaurant_id: Restaurant UUID
            
        Returns:
            Restaurant statistics
        """
        try:
            result = self.client.rpc('get_restaurant_stats', {'restaurant_uuid': restaurant_id}).execute()
            return result.data if result.data else {}
            
        except Exception as e:
            logger.error(f"Error fetching restaurant stats: {e}")
            return {}
    
    async def log_api_usage(self, endpoint: str, method: str, response_status: int, 
                           response_time_ms: int, error_message: str = None):
        """
        Log API usage for monitoring
        
        Args:
            endpoint: API endpoint called
            method: HTTP method
            response_status: HTTP response status
            response_time_ms: Response time in milliseconds
            error_message: Error message if any
        """
        try:
            log_data = {
                'endpoint': endpoint,
                'method': method,
                'response_status': response_status,
                'response_time_ms': response_time_ms,
                'error_message': error_message
            }
            
            self.client.table('api_usage_logs').insert(log_data).execute()
            
        except Exception as e:
            logger.error(f"Error logging API usage: {e}")

# Example usage and testing
if __name__ == "__main__":
    async def test_integration():
        # Initialize with environment variables
        db = SupabaseIntegration()
        
        # Test restaurant creation
        restaurant_data = {
            'name': 'Test Restaurant',
            'url': 'https://example.com/restaurant',
            'city': 'Chicago',
            'state': 'IL',
            'cuisine_type': 'Italian',
            'source_platform': 'test'
        }
        
        # Test menu items
        menu_items = [
            {
                'name': 'Margherita Pizza',
                'description': 'Fresh mozzarella, tomato sauce, basil',
                'price': '18.99',
                'category': 'Pizza',
                'allergens': ['dairy', 'gluten'],
                'dietary_tags': ['vegetarian'],
                'confidence_score': 0.95
            },
            {
                'name': 'Caesar Salad',
                'description': 'Romaine lettuce, parmesan, croutons',
                'price': '12.99',
                'category': 'Salads',
                'allergens': ['dairy', 'eggs'],
                'confidence_score': 0.88
            }
        ]
        
        scraping_result = {
            **restaurant_data,
            'items': menu_items
        }
        
        # Save to database
        summary = await db.save_scraping_results(scraping_result, 'test_scraper')
        print(f"Scraping summary: {summary}")
        
        # Test queries
        if summary['restaurant_id']:
            restaurants = await db.get_restaurants(city='Chicago')
            print(f"Found {len(restaurants)} restaurants in Chicago")
            
            menu_items = await db.get_menu_items(summary['restaurant_id'])
            print(f"Found {len(menu_items)} menu items")
            
            stats = await db.get_restaurant_stats(summary['restaurant_id'])
            print(f"Restaurant stats: {stats}")
    
    # Run test
    # asyncio.run(test_integration())
    print("Supabase integration module loaded. Use test_integration() to test.")