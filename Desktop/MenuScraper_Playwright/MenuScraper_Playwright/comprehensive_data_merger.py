#!/usr/bin/env python3
"""
Comprehensive Data Merger for Chicago Restaurant Data
Combines OpenStreetMap and Yelp data sources for maximum coverage
"""

import json
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import math
from dataclasses import dataclass
import asyncio
from pathlib import Path

@dataclass
class RestaurantMatch:
    """Data class for restaurant matching results"""
    osm_id: str
    yelp_id: str
    confidence: float
    match_type: str
    distance: float

class ComprehensiveDataMerger:
    """Merge and deduplicate restaurant data from multiple sources"""
    
    def __init__(self):
        self.osm_data = {}
        self.yelp_data = {}
        self.merged_data = {}
        self.matches = []
        self.statistics = {}
        
        # Matching thresholds
        self.name_similarity_threshold = 0.8
        self.distance_threshold_meters = 100  # 100 meters
        self.phone_match_weight = 0.4
        self.name_match_weight = 0.4
        self.location_match_weight = 0.2
    
    def load_osm_data(self, filename: str) -> bool:
        """Load OpenStreetMap restaurant data"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if 'restaurants' in data:
                for restaurant in data['restaurants']:
                    self.osm_data[restaurant['id']] = restaurant
                
                print(f"✅ Loaded {len(self.osm_data)} OpenStreetMap restaurants")
                return True
            else:
                print("❌ Invalid OpenStreetMap data format")
                return False
                
        except Exception as e:
            print(f"❌ Error loading OpenStreetMap data: {e}")
            return False
    
    def load_yelp_data(self, filename: str) -> bool:
        """Load Yelp restaurant data"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"🔍 Yelp data keys: {list(data.keys())}")
            
            # Handle both 'restaurants' and 'all_restaurants' keys
            restaurants_key = None
            if 'restaurants' in data:
                restaurants_key = 'restaurants'
            elif 'all_restaurants' in data:
                restaurants_key = 'all_restaurants'
            
            if restaurants_key:
                restaurants = data[restaurants_key]
                print(f"🔍 Found {len(restaurants)} restaurants in Yelp data (key: {restaurants_key})")
                
                for restaurant in restaurants:
                    if 'id' not in restaurant:
                        print(f"⚠️ Restaurant missing ID: {restaurant.get('name', 'Unknown')}")
                        continue
                    self.yelp_data[restaurant['id']] = restaurant
                
                print(f"✅ Loaded {len(self.yelp_data)} Yelp restaurants")
                return True
            else:
                print("❌ Invalid Yelp data format - no 'restaurants' or 'all_restaurants' key found")
                return False
                
        except Exception as e:
            print(f"❌ Error loading Yelp data: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two coordinates in meters using Haversine formula"""
        R = 6371000  # Earth's radius in meters
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def normalize_name(self, name: str) -> str:
        """Normalize restaurant name for comparison"""
        if not name:
            return ""
        
        # Convert to lowercase and remove common suffixes/prefixes
        normalized = name.lower().strip()
        
        # Remove common restaurant suffixes
        suffixes = ['restaurant', 'cafe', 'bar', 'grill', 'kitchen', 'house', 'place']
        for suffix in suffixes:
            if normalized.endswith(f' {suffix}'):
                normalized = normalized[:-len(suffix)-1].strip()
        
        # Remove special characters and extra spaces
        import re
        normalized = re.sub(r'[^a-z0-9\s]', '', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate name similarity using Levenshtein distance"""
        name1_norm = self.normalize_name(name1)
        name2_norm = self.normalize_name(name2)
        
        if not name1_norm or not name2_norm:
            return 0.0
        
        # Simple Levenshtein distance implementation
        def levenshtein_distance(s1: str, s2: str) -> int:
            if len(s1) < len(s2):
                return levenshtein_distance(s2, s1)
            
            if len(s2) == 0:
                return len(s1)
            
            previous_row = list(range(len(s2) + 1))
            for i, c1 in enumerate(s1):
                current_row = [i + 1]
                for j, c2 in enumerate(s2):
                    insertions = previous_row[j + 1] + 1
                    deletions = current_row[j] + 1
                    substitutions = previous_row[j] + (c1 != c2)
                    current_row.append(min(insertions, deletions, substitutions))
                previous_row = current_row
            
            return previous_row[-1]
        
        distance = levenshtein_distance(name1_norm, name2_norm)
        max_len = max(len(name1_norm), len(name2_norm))
        
        if max_len == 0:
            return 1.0
        
        return 1.0 - (distance / max_len)
    
    def normalize_phone(self, phone: str) -> str:
        """Normalize phone number for comparison"""
        if not phone:
            return ""
        
        # Remove all non-digit characters
        import re
        digits = re.sub(r'\D', '', phone)
        
        # Remove leading 1 if present (US country code)
        if digits.startswith('1') and len(digits) == 11:
            digits = digits[1:]
        
        return digits
    
    def find_potential_matches(self, osm_restaurant: Dict[str, Any]) -> List[Tuple[str, float]]:
        """Find potential Yelp matches for an OSM restaurant"""
        matches = []
        
        osm_lat = osm_restaurant.get('latitude')
        osm_lon = osm_restaurant.get('longitude')
        osm_name = osm_restaurant.get('name', '')
        osm_phone = self.normalize_phone(osm_restaurant.get('phone', ''))
        
        if not osm_lat or not osm_lon:
            return matches
        
        for yelp_id, yelp_restaurant in self.yelp_data.items():
            yelp_lat = yelp_restaurant.get('latitude')
            yelp_lon = yelp_restaurant.get('longitude')
            yelp_name = yelp_restaurant.get('name', '')
            yelp_phone = self.normalize_phone(yelp_restaurant.get('phone', ''))
            
            if not yelp_lat or not yelp_lon:
                continue
            
            # Calculate distance
            distance = self.calculate_distance(osm_lat, osm_lon, yelp_lat, yelp_lon)
            
            if distance > self.distance_threshold_meters:
                continue
            
            # Calculate name similarity
            name_similarity = self.calculate_name_similarity(osm_name, yelp_name)
            
            # Calculate phone match
            phone_match = 1.0 if osm_phone and yelp_phone and osm_phone == yelp_phone else 0.0
            
            # Calculate location score (closer = higher score)
            location_score = max(0, 1.0 - (distance / self.distance_threshold_meters))
            
            # Calculate overall confidence
            confidence = (
                name_similarity * self.name_match_weight +
                phone_match * self.phone_match_weight +
                location_score * self.location_match_weight
            )
            
            if confidence >= 0.5:  # Minimum confidence threshold
                matches.append((yelp_id, confidence, distance, name_similarity, phone_match))
        
        # Sort by confidence (highest first)
        matches.sort(key=lambda x: x[1], reverse=True)
        
        return matches
    
    def merge_restaurant_data(self, osm_restaurant: Dict[str, Any], yelp_restaurant: Dict[str, Any]) -> Dict[str, Any]:
        """Merge data from OSM and Yelp restaurants"""
        merged = {
            'id': f"merged_{osm_restaurant['id']}_{yelp_restaurant['id']}",
            'data_sources': ['OpenStreetMap', 'Yelp'],
            'osm_id': osm_restaurant['id'],
            'yelp_id': yelp_restaurant['id'],
            
            # Name (prefer Yelp if available, fallback to OSM)
            'name': yelp_restaurant.get('name') or osm_restaurant.get('name'),
            
            # Location (prefer OSM coordinates, fallback to Yelp)
            'latitude': osm_restaurant.get('latitude') or yelp_restaurant.get('latitude'),
            'longitude': osm_restaurant.get('longitude') or yelp_restaurant.get('longitude'),
            
            # Address (prefer Yelp formatted address)
            'address': yelp_restaurant.get('address') or osm_restaurant.get('address'),
            
            # Contact information (prefer Yelp)
            'phone': yelp_restaurant.get('phone') or osm_restaurant.get('phone'),
            'website': yelp_restaurant.get('url') or osm_restaurant.get('website'),
            
            # Business information
            'categories': yelp_restaurant.get('categories', []),
            'cuisine': osm_restaurant.get('cuisine', 'unknown'),
            'amenity': osm_restaurant.get('amenity', 'restaurant'),
            
            # Yelp-specific data
            'rating': yelp_restaurant.get('rating'),
            'review_count': yelp_restaurant.get('review_count'),
            'price': yelp_restaurant.get('price'),
            'is_closed': yelp_restaurant.get('is_closed'),
            
            # OSM-specific data
            'opening_hours': osm_restaurant.get('opening_hours'),
            'wheelchair': osm_restaurant.get('wheelchair'),
            'outdoor_seating': osm_restaurant.get('outdoor_seating'),
            'takeaway': osm_restaurant.get('takeaway'),
            'delivery': osm_restaurant.get('delivery'),
            'payment_methods': osm_restaurant.get('payment_methods', []),
            'dietary_options': osm_restaurant.get('dietary_options', []),
            
            # Metadata
            'last_updated': datetime.now().isoformat(),
            'data_quality_score': self.calculate_data_quality_score(osm_restaurant, yelp_restaurant)
        }
        
        return merged
    
    def calculate_data_quality_score(self, osm_restaurant: Dict[str, Any], yelp_restaurant: Dict[str, Any]) -> float:
        """Calculate data quality score for merged restaurant"""
        score = 0.0
        max_score = 10.0
        
        # Name (required)
        if osm_restaurant.get('name') or yelp_restaurant.get('name'):
            score += 1.0
        
        # Coordinates (required)
        if (osm_restaurant.get('latitude') and osm_restaurant.get('longitude')) or \
           (yelp_restaurant.get('latitude') and yelp_restaurant.get('longitude')):
            score += 1.0
        
        # Address
        if osm_restaurant.get('address') or yelp_restaurant.get('address'):
            score += 1.0
        
        # Phone
        if osm_restaurant.get('phone') or yelp_restaurant.get('phone'):
            score += 1.0
        
        # Website/URL
        if osm_restaurant.get('website') or yelp_restaurant.get('url'):
            score += 1.0
        
        # Rating (Yelp)
        if yelp_restaurant.get('rating'):
            score += 1.0
        
        # Categories/Cuisine
        if yelp_restaurant.get('categories') or osm_restaurant.get('cuisine'):
            score += 1.0
        
        # Opening hours
        if osm_restaurant.get('opening_hours'):
            score += 1.0
        
        # Accessibility info
        if osm_restaurant.get('wheelchair'):
            score += 1.0
        
        # Additional services
        if osm_restaurant.get('takeaway') or osm_restaurant.get('delivery'):
            score += 1.0
        
        return round(score / max_score, 2)
    
    def perform_matching(self) -> Dict[str, Any]:
        """Perform restaurant matching between OSM and Yelp data"""
        print("\n🔍 Starting restaurant matching process...")
        start_time = time.time()
        
        matched_yelp_ids = set()
        unmatched_osm = []
        unmatched_yelp = []
        
        # Find matches for each OSM restaurant
        for osm_id, osm_restaurant in self.osm_data.items():
            potential_matches = self.find_potential_matches(osm_restaurant)
            
            if potential_matches:
                # Take the best match
                best_match = potential_matches[0]
                yelp_id, confidence, distance, name_sim, phone_match = best_match
                
                if yelp_id not in matched_yelp_ids:
                    # Create match
                    match = RestaurantMatch(
                        osm_id=osm_id,
                        yelp_id=yelp_id,
                        confidence=confidence,
                        match_type='automatic',
                        distance=distance
                    )
                    self.matches.append(match)
                    matched_yelp_ids.add(yelp_id)
                    
                    # Merge the data
                    yelp_restaurant = self.yelp_data[yelp_id]
                    merged_restaurant = self.merge_restaurant_data(osm_restaurant, yelp_restaurant)
                    self.merged_data[merged_restaurant['id']] = merged_restaurant
                    
                    print(f"✅ Matched: {osm_restaurant.get('name', 'Unknown')} <-> {yelp_restaurant.get('name', 'Unknown')} (confidence: {confidence:.2f})")
                else:
                    unmatched_osm.append(osm_restaurant)
            else:
                unmatched_osm.append(osm_restaurant)
        
        # Add unmatched restaurants
        for restaurant in unmatched_osm:
            restaurant['data_sources'] = ['OpenStreetMap']
            restaurant['data_quality_score'] = self.calculate_data_quality_score(restaurant, {})
            self.merged_data[f"osm_only_{restaurant['id']}"] = restaurant
        
        for yelp_id, yelp_restaurant in self.yelp_data.items():
            if yelp_id not in matched_yelp_ids:
                yelp_restaurant['data_sources'] = ['Yelp']
                yelp_restaurant['data_quality_score'] = self.calculate_data_quality_score({}, yelp_restaurant)
                self.merged_data[f"yelp_only_{yelp_id}"] = yelp_restaurant
        
        processing_time = round(time.time() - start_time, 2)
        
        # Calculate statistics
        self.statistics = {
            'total_merged_restaurants': len(self.merged_data),
            'successful_matches': len(self.matches),
            'osm_only_restaurants': len(unmatched_osm),
            'yelp_only_restaurants': len(self.yelp_data) - len(matched_yelp_ids),
            'match_rate': round(len(self.matches) / min(len(self.osm_data), len(self.yelp_data)) * 100, 1),
            'processing_time': processing_time,
            'average_match_confidence': round(sum(match.confidence for match in self.matches) / len(self.matches), 2) if self.matches else 0
        }
        
        print(f"\n📊 Matching completed in {processing_time} seconds")
        print(f"✅ Total merged restaurants: {self.statistics['total_merged_restaurants']}")
        print(f"🔗 Successful matches: {self.statistics['successful_matches']}")
        print(f"📍 OSM-only restaurants: {self.statistics['osm_only_restaurants']}")
        print(f"⭐ Yelp-only restaurants: {self.statistics['yelp_only_restaurants']}")
        print(f"📈 Match rate: {self.statistics['match_rate']}%")
        
        return self.statistics
    
    def save_merged_data(self, filename: str = None) -> str:
        """Save merged restaurant data to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"output/chicago_restaurants_merged_{timestamp}.json"
        
        # Create output directory if it doesn't exist
        import os
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Prepare data for saving
        results = {
            'merging_info': {
                'timestamp': datetime.now().isoformat(),
                'data_sources': ['OpenStreetMap', 'Yelp'],
                'osm_restaurants_input': len(self.osm_data),
                'yelp_restaurants_input': len(self.yelp_data),
                'matching_algorithm': 'name_similarity + location_proximity + phone_matching'
            },
            'statistics': self.statistics,
            'matches': [
                {
                    'osm_id': match.osm_id,
                    'yelp_id': match.yelp_id,
                    'confidence': match.confidence,
                    'match_type': match.match_type,
                    'distance_meters': match.distance
                }
                for match in self.matches
            ],
            'restaurants': list(self.merged_data.values())
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Merged data saved to: {filename}")
        return filename

async def main():
    """Main execution function"""
    print("🔄 Starting Comprehensive Data Merger")
    
    merger = ComprehensiveDataMerger()
    
    # Load data files
    osm_file = "output/chicago_restaurants_openstreetmap_20250701_094203.json"
    yelp_file = "output/chicago_restaurants_optimized_yelp.json"
    
    print(f"📂 Loading OpenStreetMap data from: {osm_file}")
    if not merger.load_osm_data(osm_file):
        print("❌ Failed to load OpenStreetMap data")
        return
    
    print(f"📂 Loading Yelp data from: {yelp_file}")
    if not merger.load_yelp_data(yelp_file):
        print("❌ Failed to load Yelp data")
        return
    
    # Perform matching and merging
    stats = merger.perform_matching()
    
    # Save results
    filename = merger.save_merged_data()
    
    print(f"\n🎉 Data merging completed successfully!")
    print(f"📊 Final dataset: {stats['total_merged_restaurants']} unique Chicago restaurants")
    print(f"💾 Results saved to: {filename}")
    
    return stats

if __name__ == "__main__":
    asyncio.run(main())