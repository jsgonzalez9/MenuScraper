from fastapi import FastAPI, HTTPException, Query, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import asyncio
import time
from datetime import datetime
import logging
from supabase_integration import SupabaseIntegration
import os
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models for API requests/responses
class RestaurantResponse(BaseModel):
    id: str
    name: str
    url: str
    city: Optional[str] = None
    state: Optional[str] = None
    cuisine_type: Optional[str] = None
    price_range: Optional[str] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    total_menu_items: Optional[int] = None
    last_scraped_at: Optional[datetime] = None

class MenuItemResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    price: Optional[float] = None
    currency: str = 'USD'
    category_name: Optional[str] = None
    allergens: List[str] = []
    dietary_tags: List[str] = []
    confidence_score: Optional[float] = None
    is_available: bool = True
    image_url: Optional[str] = None

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=100)
    city: Optional[str] = None
    cuisine_type: Optional[str] = None
    exclude_allergens: List[str] = []
    dietary_requirements: List[str] = []
    price_range: Optional[str] = None
    limit: int = Field(default=20, ge=1, le=100)

class ScrapingRequest(BaseModel):
    restaurant_url: str = Field(..., description="URL of the restaurant to scrape")
    scraper_type: str = Field(default="auto", description="Type of scraper to use")
    options: Dict[str, Any] = Field(default_factory=dict, description="Additional scraping options")

class APIResponse(BaseModel):
    success: bool
    data: Any = None
    message: str = ""
    timestamp: datetime = Field(default_factory=datetime.now)
    request_id: Optional[str] = None

# Global database instance
db_instance = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global db_instance
    try:
        db_instance = SupabaseIntegration()
        logger.info("Database connection established")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        db_instance = None
    
    yield
    
    # Shutdown
    logger.info("API server shutting down")

# Initialize FastAPI app
app = FastAPI(
    title="MenuScraper API",
    description="RESTful API for restaurant menu data scraped from various platforms",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get database instance
async def get_database() -> SupabaseIntegration:
    if db_instance is None:
        raise HTTPException(status_code=503, detail="Database connection not available")
    return db_instance

# Middleware for API usage logging
@app.middleware("http")
async def log_requests(request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = int((time.time() - start_time) * 1000)
    
    # Log API usage (background task to avoid blocking)
    if db_instance:
        try:
            await db_instance.log_api_usage(
                endpoint=str(request.url.path),
                method=request.method,
                response_status=response.status_code,
                response_time_ms=process_time
            )
        except Exception as e:
            logger.warning(f"Failed to log API usage: {e}")
    
    return response

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "database_connected": db_instance is not None
    }

# Restaurant endpoints
@app.get("/api/restaurants", response_model=List[RestaurantResponse])
async def get_restaurants(
    city: Optional[str] = Query(None, description="Filter by city"),
    cuisine_type: Optional[str] = Query(None, description="Filter by cuisine type"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    db: SupabaseIntegration = Depends(get_database)
):
    """Get list of restaurants with optional filtering"""
    try:
        restaurants = await db.get_restaurants(city=city, cuisine_type=cuisine_type, limit=limit)
        return restaurants
    except Exception as e:
        logger.error(f"Error fetching restaurants: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch restaurants")

@app.get("/api/restaurants/{restaurant_id}", response_model=RestaurantResponse)
async def get_restaurant(
    restaurant_id: str,
    db: SupabaseIntegration = Depends(get_database)
):
    """Get specific restaurant details"""
    try:
        restaurants = await db.get_restaurants()
        restaurant = next((r for r in restaurants if r['id'] == restaurant_id), None)
        
        if not restaurant:
            raise HTTPException(status_code=404, detail="Restaurant not found")
        
        return restaurant
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching restaurant {restaurant_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch restaurant")

@app.get("/api/restaurants/{restaurant_id}/stats")
async def get_restaurant_stats(
    restaurant_id: str,
    db: SupabaseIntegration = Depends(get_database)
):
    """Get comprehensive restaurant statistics"""
    try:
        stats = await db.get_restaurant_stats(restaurant_id)
        if not stats:
            raise HTTPException(status_code=404, detail="Restaurant not found")
        return stats
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching restaurant stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch restaurant statistics")

# Menu item endpoints
@app.get("/api/restaurants/{restaurant_id}/menu", response_model=List[MenuItemResponse])
async def get_menu_items(
    restaurant_id: str,
    category: Optional[str] = Query(None, description="Filter by menu category"),
    db: SupabaseIntegration = Depends(get_database)
):
    """Get menu items for a specific restaurant"""
    try:
        menu_items = await db.get_menu_items(restaurant_id, category=category)
        return menu_items
    except Exception as e:
        logger.error(f"Error fetching menu items: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch menu items")

@app.post("/api/search/menu-items", response_model=List[MenuItemResponse])
async def search_menu_items(
    search_request: SearchRequest,
    db: SupabaseIntegration = Depends(get_database)
):
    """Search menu items across all restaurants"""
    try:
        results = await db.search_menu_items(
            search_term=search_request.query,
            allergen_filter=search_request.exclude_allergens
        )
        
        # Additional filtering based on request parameters
        if search_request.city:
            results = [item for item in results if item.get('city') == search_request.city]
        
        if search_request.cuisine_type:
            results = [item for item in results if item.get('cuisine_type') == search_request.cuisine_type]
        
        if search_request.price_range:
            results = [item for item in results if item.get('price_range') == search_request.price_range]
        
        # Apply dietary requirements filter
        if search_request.dietary_requirements:
            filtered_results = []
            for item in results:
                item_tags = item.get('dietary_tags', [])
                if all(req in item_tags for req in search_request.dietary_requirements):
                    filtered_results.append(item)
            results = filtered_results
        
        return results[:search_request.limit]
        
    except Exception as e:
        logger.error(f"Error searching menu items: {e}")
        raise HTTPException(status_code=500, detail="Failed to search menu items")

# Data aggregation endpoints
@app.get("/api/analytics/cuisine-types")
async def get_cuisine_types(
    db: SupabaseIntegration = Depends(get_database)
):
    """Get available cuisine types with restaurant counts"""
    try:
        restaurants = await db.get_restaurants(limit=1000)
        cuisine_counts = {}
        
        for restaurant in restaurants:
            cuisine = restaurant.get('cuisine_type', 'Unknown')
            cuisine_counts[cuisine] = cuisine_counts.get(cuisine, 0) + 1
        
        return {
            "cuisine_types": [
                {"name": cuisine, "restaurant_count": count}
                for cuisine, count in sorted(cuisine_counts.items())
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching cuisine types: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch cuisine types")

@app.get("/api/analytics/cities")
async def get_cities(
    db: SupabaseIntegration = Depends(get_database)
):
    """Get available cities with restaurant counts"""
    try:
        restaurants = await db.get_restaurants(limit=1000)
        city_counts = {}
        
        for restaurant in restaurants:
            city = restaurant.get('city', 'Unknown')
            city_counts[city] = city_counts.get(city, 0) + 1
        
        return {
            "cities": [
                {"name": city, "restaurant_count": count}
                for city, count in sorted(city_counts.items())
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching cities: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch cities")

@app.get("/api/analytics/allergens")
async def get_allergen_stats(
    db: SupabaseIntegration = Depends(get_database)
):
    """Get allergen statistics across all menu items"""
    try:
        # This would need to be implemented with proper database queries
        # For now, return a placeholder response
        return {
            "allergens": [
                {"name": "dairy", "item_count": 0, "restaurant_count": 0},
                {"name": "gluten", "item_count": 0, "restaurant_count": 0},
                {"name": "nuts", "item_count": 0, "restaurant_count": 0},
                {"name": "eggs", "item_count": 0, "restaurant_count": 0},
                {"name": "soy", "item_count": 0, "restaurant_count": 0}
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching allergen stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch allergen statistics")

# Scraping endpoints (for triggering new scrapes)
@app.post("/api/scrape/restaurant")
async def scrape_restaurant(
    scraping_request: ScrapingRequest,
    background_tasks: BackgroundTasks,
    db: SupabaseIntegration = Depends(get_database)
):
    """Trigger scraping of a new restaurant (background task)"""
    try:
        # This would integrate with your existing scrapers
        # For now, return a placeholder response
        
        task_id = f"scrape_{int(time.time())}"
        
        # Add background task (you would implement the actual scraping logic)
        # background_tasks.add_task(run_scraper, scraping_request.restaurant_url, scraping_request.scraper_type)
        
        return {
            "task_id": task_id,
            "status": "queued",
            "message": "Scraping task has been queued",
            "estimated_completion": "5-10 minutes"
        }
        
    except Exception as e:
        logger.error(f"Error queuing scraping task: {e}")
        raise HTTPException(status_code=500, detail="Failed to queue scraping task")

@app.get("/api/scrape/status/{task_id}")
async def get_scraping_status(
    task_id: str,
    db: SupabaseIntegration = Depends(get_database)
):
    """Get status of a scraping task"""
    try:
        # This would check the actual task status
        # For now, return a placeholder response
        return {
            "task_id": task_id,
            "status": "completed",
            "progress": 100,
            "items_found": 45,
            "items_processed": 45,
            "errors": [],
            "completed_at": datetime.now()
        }
    except Exception as e:
        logger.error(f"Error fetching scraping status: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch scraping status")

# Export endpoints
@app.get("/api/export/restaurant/{restaurant_id}")
async def export_restaurant_data(
    restaurant_id: str,
    format: str = Query("json", regex="^(json|csv)$"),
    db: SupabaseIntegration = Depends(get_database)
):
    """Export restaurant data in various formats"""
    try:
        # Get restaurant data
        restaurants = await db.get_restaurants()
        restaurant = next((r for r in restaurants if r['id'] == restaurant_id), None)
        
        if not restaurant:
            raise HTTPException(status_code=404, detail="Restaurant not found")
        
        # Get menu items
        menu_items = await db.get_menu_items(restaurant_id)
        
        export_data = {
            "restaurant": restaurant,
            "menu_items": menu_items,
            "exported_at": datetime.now(),
            "total_items": len(menu_items)
        }
        
        if format == "json":
            return JSONResponse(
                content=export_data,
                headers={"Content-Disposition": f"attachment; filename=restaurant_{restaurant_id}.json"}
            )
        elif format == "csv":
            # Implement CSV export logic here
            raise HTTPException(status_code=501, detail="CSV export not yet implemented")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting restaurant data: {e}")
        raise HTTPException(status_code=500, detail="Failed to export restaurant data")

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "success": False,
            "message": "Resource not found",
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "timestamp": datetime.now().isoformat()
        }
    )

if __name__ == "__main__":
    import uvicorn
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Run the server
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )