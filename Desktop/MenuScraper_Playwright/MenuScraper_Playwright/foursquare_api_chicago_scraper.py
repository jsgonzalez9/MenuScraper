import requests
import json
import time
from datetime import datetime
import os
from typing import Dict, List, Any, Optional

# Foursquare API Configuration
FOURSQUARE_CLIENT_ID = "LIS3WLAIIZ4FWXQG3JYOCM1LQDVB0JTGNGEGO1LXV2J3TMWZ"
FOURSQUARE_CLIENT_SECRET = "U0WHX3KTI442OEGLSETUILR4JKD4ADIKEN2KZQZEHULBVVT5"
FOURSQUARE_API_VERSION = "20231010"  # Use a recent version date

def extract_allergen_info(text: str) -> Dict[str, Any]:
    """
    Extract potential allergen information from text
    """
    if not text:
        return {"potential_allergens": [], "dietary_info": []}
    
    text_lower = text.lower()
    
    # Common allergens
    allergens = {
        "dairy": ["milk", "cheese", "butter", "cream", "yogurt", "dairy"],
        "eggs": ["egg", "eggs", "mayonnaise", "mayo"],
        "fish": ["fish", "salmon", "tuna", "cod", "halibut", "anchovy"],
        "shellfish": ["shrimp", "crab", "lobster", "oyster", "mussel", "clam", "scallop"],
        "tree_nuts": ["almond", "walnut", "pecan", "cashew", "pistachio", "hazelnut", "macadamia"],
        "peanuts": ["peanut", "peanuts"],
        "wheat": ["wheat", "flour", "bread", "pasta", "noodle", "gluten"],
        "soy": ["soy", "tofu", "soybean", "edamame", "miso"]
    }
    
    # Dietary information
    dietary_options = {
        "vegetarian": ["vegetarian", "veggie"],
        "vegan": ["vegan", "plant-based"],
        "gluten_free": ["gluten-free", "gluten free", "gf"],
        "dairy_free": ["dairy-free", "dairy free", "lactose-free"],
        "nut_free": ["nut-free", "nut free"],
        "keto": ["keto", "ketogenic", "low-carb"],
        "paleo": ["paleo", "paleolithic"]
    }
    
    found_allergens = []
    found_dietary = []
    
    # Check for allergens
    for allergen, keywords in allergens.items():
        if any(keyword in text_lower for keyword in keywords):
            found_allergens.append(allergen)
    
    # Check for dietary options
    for diet, keywords in dietary_options.items():
        if any(keyword in text_lower for keyword in keywords):
            found_dietary.append(diet)
    
    return {
        "potential_allergens": found_allergens,
        "dietary_info": found_dietary
    }

def search_foursquare_venues(query: str = "restaurant", location: str = "Chicago, IL", 
                           limit: int = 50, offset: int = 0) -> Dict[str, Any]:
    """
    Search for venues using Foursquare API
    """
    url = "https://api.foursquare.com/v2/venues/search"
    
    params = {
        "client_id": FOURSQUARE_CLIENT_ID,
        "client_secret": FOURSQUARE_CLIENT_SECRET,
        "v": FOURSQUARE_API_VERSION,
        "query": query,
        "near": location,
        "limit": limit,
        "offset": offset,
        "categoryId": "4d4b7105d754a06374d81259"  # Food category
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error searching venues: {e}")
        return {"response": {"venues": []}}

def get_venue_details(venue_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific venue
    """
    url = f"https://api.foursquare.com/v2/venues/{venue_id}"
    
    params = {
        "client_id": FOURSQUARE_CLIENT_ID,
        "client_secret": FOURSQUARE_CLIENT_SECRET,
        "v": FOURSQUARE_API_VERSION
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting venue details for {venue_id}: {e}")
        return {"response": {"venue": {}}}

def get_venue_menu(venue_id: str) -> Dict[str, Any]:
    """
    Get menu information for a venue (if available)
    """
    url = f"https://api.foursquare.com/v2/venues/{venue_id}/menu"
    
    params = {
        "client_id": FOURSQUARE_CLIENT_ID,
        "client_secret": FOURSQUARE_CLIENT_SECRET,
        "v": FOURSQUARE_API_VERSION
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting menu for {venue_id}: {e}")
        return {"response": {"menu": {}}}

def process_venue_data(venue: Dict[str, Any], detailed_info: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Process and structure venue data
    """
    processed = {
        "id": venue.get("id", ""),
        "name": venue.get("name", ""),
        "categories": [cat.get("name", "") for cat in venue.get("categories", [])],
        "location": {
            "address": venue.get("location", {}).get("formattedAddress", []),
            "lat": venue.get("location", {}).get("lat"),
            "lng": venue.get("location", {}).get("lng"),
            "neighborhood": venue.get("location", {}).get("neighborhood", ""),
            "city": venue.get("location", {}).get("city", ""),
            "state": venue.get("location", {}).get("state", ""),
            "postalCode": venue.get("location", {}).get("postalCode", "")
        },
        "contact": {
            "phone": venue.get("contact", {}).get("phone", ""),
            "formattedPhone": venue.get("contact", {}).get("formattedPhone", ""),
            "website": venue.get("url", "")
        },
        "stats": {
            "checkinsCount": venue.get("stats", {}).get("checkinsCount", 0),
            "usersCount": venue.get("stats", {}).get("usersCount", 0),
            "tipCount": venue.get("stats", {}).get("tipCount", 0)
        },
        "rating": venue.get("rating", 0),
        "price": venue.get("price", {}).get("tier", 0) if venue.get("price") else 0,
        "hours": venue.get("hours", {}),
        "menu_items": [],
        "allergen_analysis": {"potential_allergens": [], "dietary_info": []}
    }
    
    # Add detailed information if available
    if detailed_info and "response" in detailed_info and "venue" in detailed_info["response"]:
        detail_venue = detailed_info["response"]["venue"]
        processed["description"] = detail_venue.get("description", "")
        processed["tags"] = detail_venue.get("tags", [])
        processed["attributes"] = detail_venue.get("attributes", {})
        
        # Extract allergen info from description and tags
        description_text = detail_venue.get("description", "")
        tags_text = " ".join(detail_venue.get("tags", []))
        combined_text = f"{description_text} {tags_text}"
        
        if combined_text.strip():
            allergen_info = extract_allergen_info(combined_text)
            processed["allergen_analysis"] = allergen_info
    
    return processed

def scrape_all_chicago_restaurants_foursquare() -> Dict[str, Any]:
    """
    Scrape all restaurants in Chicago using Foursquare API
    """
    print("Starting Chicago restaurant scraping with Foursquare API...")
    
    all_restaurants = []
    total_api_calls = 0
    offset = 0
    limit = 50  # Foursquare limit per request
    
    # Different search queries to get comprehensive coverage
    search_queries = [
        "restaurant",
        "food",
        "cafe",
        "bar",
        "pizza",
        "burger",
        "sushi",
        "mexican",
        "italian",
        "chinese",
        "thai",
        "indian",
        "steakhouse",
        "seafood",
        "bakery",
        "deli"
    ]
    
    seen_venues = set()
    
    for query in search_queries:
        print(f"\nSearching for: {query}")
        offset = 0
        
        while True:
            print(f"  Fetching venues {offset}-{offset+limit-1}...")
            
            # Search venues
            search_result = search_foursquare_venues(query=query, offset=offset, limit=limit)
            total_api_calls += 1
            
            venues = search_result.get("response", {}).get("venues", [])
            
            if not venues:
                print(f"  No more venues found for '{query}'")
                break
            
            for venue in venues:
                venue_id = venue.get("id")
                if venue_id and venue_id not in seen_venues:
                    seen_venues.add(venue_id)
                    
                    # Get detailed venue information
                    detailed_info = get_venue_details(venue_id)
                    total_api_calls += 1
                    
                    # Process venue data
                    processed_venue = process_venue_data(venue, detailed_info)
                    all_restaurants.append(processed_venue)
                    
                    print(f"    Added: {processed_venue['name']}")
                    
                    # Rate limiting
                    time.sleep(0.1)
            
            offset += limit
            
            # Foursquare has pagination limits, break if we've gone too far
            if offset >= 1000:  # Reasonable limit to avoid infinite loops
                break
        
        # Rate limiting between queries
        time.sleep(1)
    
    # Calculate statistics
    total_restaurants = len(all_restaurants)
    restaurants_with_allergens = sum(1 for r in all_restaurants 
                                   if r["allergen_analysis"]["potential_allergens"])
    restaurants_with_dietary = sum(1 for r in all_restaurants 
                                 if r["allergen_analysis"]["dietary_info"])
    
    # Category distribution
    all_categories = []
    for restaurant in all_restaurants:
        all_categories.extend(restaurant["categories"])
    
    category_counts = {}
    for category in all_categories:
        category_counts[category] = category_counts.get(category, 0) + 1
    
    top_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # Rating distribution
    ratings = [r["rating"] for r in all_restaurants if r["rating"] > 0]
    avg_rating = sum(ratings) / len(ratings) if ratings else 0
    
    # Price distribution
    prices = [r["price"] for r in all_restaurants if r["price"] > 0]
    price_distribution = {}
    for price in prices:
        price_distribution[price] = price_distribution.get(price, 0) + 1
    
    summary = {
        "scraping_info": {
            "timestamp": datetime.now().isoformat(),
            "source": "Foursquare API",
            "location": "Chicago, Illinois",
            "total_api_calls": total_api_calls,
            "search_queries_used": len(search_queries)
        },
        "statistics": {
            "total_restaurants": total_restaurants,
            "restaurants_with_allergen_info": restaurants_with_allergens,
            "restaurants_with_dietary_info": restaurants_with_dietary,
            "allergen_coverage_percentage": round((restaurants_with_allergens / total_restaurants * 100), 2) if total_restaurants > 0 else 0,
            "dietary_coverage_percentage": round((restaurants_with_dietary / total_restaurants * 100), 2) if total_restaurants > 0 else 0
        },
        "data_quality": {
            "average_rating": round(avg_rating, 2),
            "total_rated_restaurants": len(ratings),
            "price_distribution": price_distribution,
            "top_categories": top_categories
        },
        "scaling_estimates": {
            "current_coverage": f"{total_restaurants} restaurants",
            "estimated_full_chicago": "8,000-12,000 restaurants",
            "api_calls_for_full_coverage": "16,000-24,000 calls",
            "estimated_time_full_scrape": "2-3 hours with rate limiting",
            "daily_api_limit": "5,000 calls (free tier)",
            "days_needed_for_full_scrape": "3-5 days"
        },
        "restaurants": all_restaurants
    }
    
    return summary

def main():
    """
    Main function to demonstrate Foursquare API scraping
    """
    # Create output directory
    os.makedirs("output", exist_ok=True)
    
    # Scrape restaurants
    result = scrape_all_chicago_restaurants_foursquare()
    
    # Save results
    output_file = "output/chicago_restaurants_foursquare_api.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\n=== FOURSQUARE API SCRAPING COMPLETE ===")
    print(f"Total restaurants collected: {result['statistics']['total_restaurants']}")
    print(f"Total API calls used: {result['scraping_info']['total_api_calls']}")
    print(f"Allergen coverage: {result['statistics']['allergen_coverage_percentage']}%")
    print(f"Results saved to: {output_file}")
    
    # Display sample restaurants
    print("\n=== SAMPLE RESTAURANTS ===")
    for i, restaurant in enumerate(result['restaurants'][:3]):
        print(f"\n{i+1}. {restaurant['name']}")
        print(f"   Categories: {', '.join(restaurant['categories'])}")
        print(f"   Rating: {restaurant['rating']}")
        print(f"   Price: {'$' * restaurant['price'] if restaurant['price'] > 0 else 'N/A'}")
        print(f"   Location: {', '.join(restaurant['location']['address'])}")
        if restaurant['allergen_analysis']['potential_allergens']:
            print(f"   Potential Allergens: {', '.join(restaurant['allergen_analysis']['potential_allergens'])}")
        if restaurant['allergen_analysis']['dietary_info']:
            print(f"   Dietary Options: {', '.join(restaurant['allergen_analysis']['dietary_info'])}")
    
    print(f"\n=== TIME ESTIMATES ===")
    print(f"Current scrape time: ~30-45 minutes")
    print(f"Full Chicago scrape: {result['scaling_estimates']['estimated_time_full_scrape']}")
    print(f"API calls needed: {result['scaling_estimates']['api_calls_for_full_coverage']}")
    print(f"Days needed (free tier): {result['scaling_estimates']['days_needed_for_full_scrape']}")

if __name__ == "__main__":
    main()