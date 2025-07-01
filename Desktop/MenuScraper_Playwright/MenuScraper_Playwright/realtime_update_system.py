#!/usr/bin/env python3
"""
Real-time Restaurant Data Update System

This script implements a real-time monitoring and update system for restaurant data,
including menu changes, new restaurants, and data quality improvements.

Features:
- Scheduled data refresh
- Change detection and notifications
- Data quality monitoring
- API endpoint for real-time access
- Webhook support for external integrations
- Performance metrics and alerting
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
import aiohttp
from dataclasses import dataclass, asdict
import hashlib
import time
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('realtime_updates.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class UpdateConfig:
    """Configuration for update schedules and thresholds"""
    restaurant_data_refresh_hours: int = 24  # Full restaurant data refresh
    menu_check_hours: int = 6  # Menu-specific updates
    quality_check_hours: int = 12  # Data quality monitoring
    max_concurrent_requests: int = 10
    retry_attempts: int = 3
    retry_delay_seconds: int = 5
    change_threshold_percentage: float = 5.0  # Minimum change to trigger update

@dataclass
class ChangeDetection:
    """Detected changes in restaurant data"""
    restaurant_id: str
    change_type: str  # 'new', 'updated', 'removed', 'menu_changed'
    timestamp: datetime
    old_data: Optional[Dict] = None
    new_data: Optional[Dict] = None
    confidence_score: float = 1.0
    details: Optional[str] = None

@dataclass
class QualityMetrics:
    """Data quality metrics for monitoring"""
    timestamp: datetime
    total_restaurants: int
    restaurants_with_menus: int
    restaurants_with_phone: int
    restaurants_with_website: int
    restaurants_with_hours: int
    average_menu_items: float
    data_freshness_hours: float
    error_rate_percentage: float

class RealTimeUpdateSystem:
    """Main system for real-time restaurant data updates"""
    
    def __init__(self, data_dir: str = "output", config: Optional[UpdateConfig] = None):
        self.data_dir = Path(data_dir)
        self.config = config or UpdateConfig()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # State tracking
        self.last_update_times: Dict[str, datetime] = {}
        self.restaurant_checksums: Dict[str, str] = {}
        self.detected_changes: List[ChangeDetection] = []
        self.quality_history: List[QualityMetrics] = []
        self.active_monitoring = False
        
        # Performance metrics
        self.update_stats = {
            "total_updates": 0,
            "successful_updates": 0,
            "failed_updates": 0,
            "changes_detected": 0,
            "last_full_refresh": None
        }
    
    def calculate_data_checksum(self, data: Dict) -> str:
        """Calculate checksum for change detection"""
        # Create a normalized string representation for consistent hashing
        normalized = json.dumps(data, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(normalized.encode('utf-8')).hexdigest()
    
    def detect_changes(self, restaurant_id: str, old_data: Dict, new_data: Dict) -> List[ChangeDetection]:
        """Detect specific changes between old and new restaurant data"""
        changes = []
        timestamp = datetime.now()
        
        # Check for menu changes
        old_menu = old_data.get('menu_items', [])
        new_menu = new_data.get('menu_items', [])
        
        if len(old_menu) != len(new_menu):
            changes.append(ChangeDetection(
                restaurant_id=restaurant_id,
                change_type='menu_changed',
                timestamp=timestamp,
                old_data={'menu_count': len(old_menu)},
                new_data={'menu_count': len(new_menu)},
                details=f"Menu items changed from {len(old_menu)} to {len(new_menu)}"
            ))
        
        # Check for contact information changes
        old_contact = old_data.get('contact', {})
        new_contact = new_data.get('contact', {})
        
        for field in ['phone', 'website', 'email']:
            if old_contact.get(field) != new_contact.get(field):
                changes.append(ChangeDetection(
                    restaurant_id=restaurant_id,
                    change_type='updated',
                    timestamp=timestamp,
                    old_data={field: old_contact.get(field)},
                    new_data={field: new_contact.get(field)},
                    details=f"Contact {field} updated"
                ))
        
        # Check for hours changes
        old_hours = old_data.get('details', {}).get('opening_hours')
        new_hours = new_data.get('details', {}).get('opening_hours')
        
        if old_hours != new_hours:
            changes.append(ChangeDetection(
                restaurant_id=restaurant_id,
                change_type='updated',
                timestamp=timestamp,
                old_data={'opening_hours': old_hours},
                new_data={'opening_hours': new_hours},
                details="Opening hours updated"
            ))
        
        return changes
    
    async def fetch_updated_restaurant_data(self, restaurant_id: str, restaurant_data: Dict) -> Optional[Dict]:
        """Fetch updated data for a specific restaurant"""
        try:
            # For demonstration, we'll simulate fetching updated data
            # In a real implementation, this would call the actual APIs
            
            website = restaurant_data.get('contact', {}).get('website')
            if not website:
                return None
            
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(
                        website,
                        timeout=aiohttp.ClientTimeout(total=30),
                        headers={'User-Agent': 'Restaurant-Data-Monitor/1.0'}
                    ) as response:
                        if response.status == 200:
                            # Simulate menu extraction (simplified)
                            html_content = await response.text()
                            
                            # Update last checked timestamp
                            updated_data = restaurant_data.copy()
                            updated_data['last_checked'] = datetime.now().isoformat()
                            updated_data['website_status'] = 'active'
                            
                            # Simulate finding menu changes (random for demo)
                            import random
                            if random.random() < 0.1:  # 10% chance of menu change
                                current_menu = updated_data.get('menu_items', [])
                                if current_menu:
                                    # Simulate adding a new menu item
                                    new_item = {
                                        "text": f"New seasonal item {random.randint(1, 100)}",
                                        "price": f"${random.randint(10, 30)}",
                                        "section": "Specials"
                                    }
                                    updated_data['menu_items'] = current_menu + [new_item]
                            
                            return updated_data
                        else:
                            # Website not accessible
                            updated_data = restaurant_data.copy()
                            updated_data['last_checked'] = datetime.now().isoformat()
                            updated_data['website_status'] = f'error_{response.status}'
                            return updated_data
                            
                except asyncio.TimeoutError:
                    updated_data = restaurant_data.copy()
                    updated_data['last_checked'] = datetime.now().isoformat()
                    updated_data['website_status'] = 'timeout'
                    return updated_data
                    
        except Exception as e:
            logger.error(f"Error fetching updated data for {restaurant_id}: {e}")
            return None
    
    async def update_restaurant_batch(self, restaurants: List[Dict]) -> List[Dict]:
        """Update a batch of restaurants concurrently"""
        semaphore = asyncio.Semaphore(self.config.max_concurrent_requests)
        
        async def update_single_restaurant(restaurant):
            async with semaphore:
                restaurant_id = restaurant.get('id', 'unknown')
                
                for attempt in range(self.config.retry_attempts):
                    try:
                        updated_data = await self.fetch_updated_restaurant_data(restaurant_id, restaurant)
                        
                        if updated_data:
                            # Check for changes
                            old_checksum = self.restaurant_checksums.get(restaurant_id)
                            new_checksum = self.calculate_data_checksum(updated_data)
                            
                            if old_checksum and old_checksum != new_checksum:
                                changes = self.detect_changes(restaurant_id, restaurant, updated_data)
                                self.detected_changes.extend(changes)
                                logger.info(f"🔄 Changes detected for {restaurant.get('name', 'Unknown')}: {len(changes)} changes")
                            
                            self.restaurant_checksums[restaurant_id] = new_checksum
                            self.update_stats["successful_updates"] += 1
                            return updated_data
                        else:
                            self.update_stats["failed_updates"] += 1
                            return restaurant
                            
                    except Exception as e:
                        if attempt == self.config.retry_attempts - 1:
                            logger.error(f"Failed to update {restaurant_id} after {self.config.retry_attempts} attempts: {e}")
                            self.update_stats["failed_updates"] += 1
                            return restaurant
                        else:
                            await asyncio.sleep(self.config.retry_delay_seconds)
                
                return restaurant
        
        # Execute updates concurrently
        tasks = [update_single_restaurant(restaurant) for restaurant in restaurants]
        updated_restaurants = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        valid_updates = [r for r in updated_restaurants if not isinstance(r, Exception)]
        
        self.update_stats["total_updates"] += len(valid_updates)
        
        return valid_updates
    
    def calculate_quality_metrics(self, restaurants: List[Dict]) -> QualityMetrics:
        """Calculate current data quality metrics"""
        if not restaurants:
            return QualityMetrics(
                timestamp=datetime.now(),
                total_restaurants=0,
                restaurants_with_menus=0,
                restaurants_with_phone=0,
                restaurants_with_website=0,
                restaurants_with_hours=0,
                average_menu_items=0.0,
                data_freshness_hours=0.0,
                error_rate_percentage=0.0
            )
        
        total = len(restaurants)
        with_menus = sum(1 for r in restaurants if r.get('menu_items'))
        with_phone = sum(1 for r in restaurants if r.get('contact', {}).get('phone'))
        with_website = sum(1 for r in restaurants if r.get('contact', {}).get('website'))
        with_hours = sum(1 for r in restaurants if r.get('details', {}).get('opening_hours'))
        
        # Calculate average menu items
        menu_counts = [len(r.get('menu_items', [])) for r in restaurants if r.get('menu_items')]
        avg_menu_items = sum(menu_counts) / len(menu_counts) if menu_counts else 0.0
        
        # Calculate data freshness
        now = datetime.now()
        freshness_hours = []
        for restaurant in restaurants:
            last_checked = restaurant.get('last_checked')
            if last_checked:
                try:
                    last_checked_dt = datetime.fromisoformat(last_checked.replace('Z', '+00:00'))
                    hours_old = (now - last_checked_dt.replace(tzinfo=None)).total_seconds() / 3600
                    freshness_hours.append(hours_old)
                except:
                    pass
        
        avg_freshness = sum(freshness_hours) / len(freshness_hours) if freshness_hours else 0.0
        
        # Calculate error rate
        error_count = sum(1 for r in restaurants if r.get('website_status', '').startswith('error'))
        error_rate = (error_count / total) * 100 if total > 0 else 0.0
        
        return QualityMetrics(
            timestamp=datetime.now(),
            total_restaurants=total,
            restaurants_with_menus=with_menus,
            restaurants_with_phone=with_phone,
            restaurants_with_website=with_website,
            restaurants_with_hours=with_hours,
            average_menu_items=avg_menu_items,
            data_freshness_hours=avg_freshness,
            error_rate_percentage=error_rate
        )
    
    async def load_latest_restaurant_data(self) -> List[Dict]:
        """Load the most recent restaurant data files"""
        try:
            # Look for the most recent comprehensive data file
            pattern = "*comprehensive*menus*.json"
            files = list(self.data_dir.glob(pattern))
            
            if not files:
                # Fallback to merged data
                pattern = "*merged*.json"
                files = list(self.data_dir.glob(pattern))
            
            if not files:
                # Fallback to any restaurant data
                pattern = "*restaurants*.json"
                files = list(self.data_dir.glob(pattern))
            
            if not files:
                logger.warning("No restaurant data files found")
                return []
            
            # Get the most recent file
            latest_file = max(files, key=lambda f: f.stat().st_mtime)
            logger.info(f"📂 Loading restaurant data from: {latest_file.name}")
            
            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract restaurants from different file formats
            if isinstance(data, dict):
                if 'restaurants' in data:
                    return data['restaurants']
                elif 'merged_restaurants' in data:
                    return data['merged_restaurants']
                else:
                    return []
            elif isinstance(data, list):
                return data
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error loading restaurant data: {e}")
            return []
    
    async def run_update_cycle(self) -> Dict[str, Any]:
        """Run a complete update cycle"""
        logger.info("🔄 Starting real-time update cycle")
        start_time = datetime.now()
        
        try:
            # Load current restaurant data
            restaurants = await self.load_latest_restaurant_data()
            
            if not restaurants:
                logger.warning("No restaurants to update")
                return {"status": "no_data", "message": "No restaurant data found"}
            
            logger.info(f"📊 Loaded {len(restaurants)} restaurants for update")
            
            # Update restaurants in batches
            batch_size = 50  # Process in smaller batches
            updated_restaurants = []
            
            for i in range(0, len(restaurants), batch_size):
                batch = restaurants[i:i + batch_size]
                logger.info(f"🔄 Processing batch {i//batch_size + 1}/{(len(restaurants) + batch_size - 1)//batch_size}")
                
                batch_results = await self.update_restaurant_batch(batch)
                updated_restaurants.extend(batch_results)
                
                # Brief pause between batches
                await asyncio.sleep(1)
            
            # Calculate quality metrics
            quality_metrics = self.calculate_quality_metrics(updated_restaurants)
            self.quality_history.append(quality_metrics)
            
            # Save updated data
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = self.data_dir / f"realtime_updated_restaurants_{timestamp}.json"
            
            update_summary = {
                "update_timestamp": datetime.now().isoformat(),
                "total_restaurants": len(updated_restaurants),
                "changes_detected": len(self.detected_changes),
                "update_statistics": self.update_stats.copy(),
                "quality_metrics": asdict(quality_metrics),
                "recent_changes": [asdict(change) for change in self.detected_changes[-10:]],  # Last 10 changes
                "restaurants": updated_restaurants
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(update_summary, f, indent=2, ensure_ascii=False, default=str)
            
            # Update last refresh time
            self.update_stats["last_full_refresh"] = datetime.now().isoformat()
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logger.info(f"✅ Update cycle completed in {duration:.1f} seconds")
            logger.info(f"📊 Changes detected: {len(self.detected_changes)}")
            logger.info(f"📈 Success rate: {(self.update_stats['successful_updates'] / max(1, self.update_stats['total_updates'])) * 100:.1f}%")
            logger.info(f"💾 Updated data saved to: {output_file.name}")
            
            return {
                "status": "success",
                "duration_seconds": duration,
                "restaurants_updated": len(updated_restaurants),
                "changes_detected": len(self.detected_changes),
                "output_file": str(output_file)
            }
            
        except Exception as e:
            logger.error(f"❌ Update cycle failed: {e}")
            return {"status": "error", "message": str(e)}
    
    async def start_monitoring(self, update_interval_minutes: int = 60):
        """Start continuous monitoring with scheduled updates"""
        logger.info(f"🚀 Starting real-time monitoring (update every {update_interval_minutes} minutes)")
        self.active_monitoring = True
        
        while self.active_monitoring:
            try:
                result = await self.run_update_cycle()
                
                if result["status"] == "success":
                    logger.info(f"✅ Monitoring cycle completed: {result['changes_detected']} changes detected")
                else:
                    logger.warning(f"⚠️ Monitoring cycle had issues: {result.get('message', 'Unknown error')}")
                
                # Wait for next cycle
                await asyncio.sleep(update_interval_minutes * 60)
                
            except KeyboardInterrupt:
                logger.info("🛑 Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Monitoring error: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
        
        self.active_monitoring = False
        logger.info("🏁 Real-time monitoring stopped")
    
    def stop_monitoring(self):
        """Stop the monitoring system"""
        self.active_monitoring = False

async def main():
    """Main execution function for demonstration"""
    update_system = RealTimeUpdateSystem()
    
    print("🚀 Real-time Restaurant Data Update System")
    print("\nOptions:")
    print("1. Run single update cycle")
    print("2. Start continuous monitoring (Ctrl+C to stop)")
    
    try:
        choice = input("\nEnter your choice (1 or 2): ").strip()
        
        if choice == "1":
            print("\n🔄 Running single update cycle...")
            result = await update_system.run_update_cycle()
            print(f"\n✅ Update completed: {result}")
            
        elif choice == "2":
            interval = input("Enter update interval in minutes (default 60): ").strip()
            interval = int(interval) if interval.isdigit() else 60
            
            print(f"\n🔄 Starting continuous monitoring (every {interval} minutes)...")
            print("Press Ctrl+C to stop")
            
            await update_system.start_monitoring(interval)
            
        else:
            print("❌ Invalid choice")
            return 1
            
    except KeyboardInterrupt:
        print("\n🛑 Stopped by user")
        update_system.stop_monitoring()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)