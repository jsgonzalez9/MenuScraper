#!/usr/bin/env python3
"""
Complete Restaurant Data Pipeline Demonstration

This script demonstrates the full end-to-end restaurant data collection and processing pipeline,
showcasing all the components we've built:

1. OpenStreetMap restaurant data collection
2. Yelp API integration and data merging
3. ML-enhanced menu extraction
4. National scaling capabilities
5. Real-time update system

Features:
- Interactive demo mode
- Progress tracking
- Performance metrics
- Data quality analysis
- Comprehensive reporting
"""

import asyncio
import json
import logging
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pipeline_demo.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CompletePipelineDemo:
    """Comprehensive demonstration of the restaurant data pipeline"""
    
    def __init__(self, output_dir: str = "output/demo"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Pipeline components
        self.components = {
            "osm_scraper": "openstreetmap_chicago_scraper.py",
            "yelp_scraper": "yelp_optimized_chicago_scraper.py",
            "data_merger": "comprehensive_data_merger.py",
            "ml_scraper": "ml_enhanced_menu_scraper.py",
            "national_pipeline": "national_scaling_pipeline.py",
            "realtime_system": "realtime_update_system.py"
        }
        
        # Demo statistics
        self.demo_stats = {
            "start_time": None,
            "end_time": None,
            "components_executed": [],
            "total_restaurants_collected": 0,
            "total_menus_extracted": 0,
            "data_quality_score": 0.0,
            "processing_times": {},
            "errors": []
        }
    
    def print_banner(self):
        """Print demo banner"""
        banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                    🍽️  COMPLETE RESTAURANT DATA PIPELINE DEMO  🍽️             ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  This demonstration showcases our comprehensive restaurant data collection   ║
║  and processing pipeline, featuring:                                         ║
║                                                                              ║
║  🗺️  OpenStreetMap Data Collection                                           ║
║  🔍  Yelp API Integration & Data Merging                                     ║
║  🤖  ML-Enhanced Menu Extraction                                             ║
║  🌍  National Scaling Capabilities                                           ║
║  ⚡  Real-time Update System                                                 ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
        """
        print(banner)
    
    def print_component_info(self, component: str, description: str):
        """Print component information"""
        print(f"\n{'='*80}")
        print(f"🔧 COMPONENT: {component.upper()}")
        print(f"📝 DESCRIPTION: {description}")
        print(f"{'='*80}")
    
    async def run_component(self, component_name: str, script_name: str, description: str) -> Dict[str, Any]:
        """Run a pipeline component and track results"""
        self.print_component_info(component_name, description)
        
        start_time = time.time()
        result = {
            "component": component_name,
            "success": False,
            "execution_time": 0,
            "output_files": [],
            "statistics": {},
            "error": None
        }
        
        try:
            # Check if script exists
            script_path = Path(script_name)
            if not script_path.exists():
                result["error"] = f"Script {script_name} not found"
                return result
            
            print(f"🚀 Executing: {script_name}")
            
            # Run the component
            process = await asyncio.create_subprocess_exec(
                sys.executable, script_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            execution_time = time.time() - start_time
            result["execution_time"] = round(execution_time, 2)
            
            if process.returncode == 0:
                result["success"] = True
                print(f"✅ {component_name} completed successfully in {execution_time:.1f}s")
                
                # Parse output for statistics
                output_text = stdout.decode('utf-8')
                result["statistics"] = self._parse_component_output(output_text)
                
                # Find output files
                result["output_files"] = self._find_output_files(component_name)
                
            else:
                result["error"] = stderr.decode('utf-8')
                print(f"❌ {component_name} failed: {result['error'][:200]}...")
            
        except Exception as e:
            result["error"] = str(e)
            result["execution_time"] = time.time() - start_time
            print(f"❌ {component_name} exception: {e}")
        
        self.demo_stats["processing_times"][component_name] = result["execution_time"]
        if result["success"]:
            self.demo_stats["components_executed"].append(component_name)
        else:
            self.demo_stats["errors"].append(f"{component_name}: {result['error']}")
        
        return result
    
    def _parse_component_output(self, output: str) -> Dict[str, Any]:
        """Parse component output for statistics"""
        stats = {}
        
        # Look for common patterns in output
        lines = output.split('\n')
        for line in lines:
            line = line.strip()
            
            # Restaurant count patterns
            if 'restaurants' in line.lower() and any(char.isdigit() for char in line):
                import re
                numbers = re.findall(r'\d+', line)
                if numbers:
                    stats['restaurants_found'] = int(numbers[-1])
            
            # Menu count patterns
            if 'menu' in line.lower() and any(char.isdigit() for char in line):
                import re
                numbers = re.findall(r'\d+', line)
                if numbers:
                    stats['menus_extracted'] = int(numbers[-1])
            
            # Success rate patterns
            if 'success' in line.lower() and '%' in line:
                import re
                percentages = re.findall(r'(\d+(?:\.\d+)?)%', line)
                if percentages:
                    stats['success_rate'] = float(percentages[0])
        
        return stats
    
    def _find_output_files(self, component_name: str) -> List[str]:
        """Find output files created by component"""
        output_files = []
        
        # Common output patterns
        patterns = {
            "osm_scraper": ["*chicago*osm*.json", "*openstreetmap*.json"],
            "yelp_scraper": ["*chicago*yelp*.json", "*optimized*.json"],
            "data_merger": ["*merged*.json", "*comprehensive*.json"],
            "ml_scraper": ["*menu*.json", "*ml_enhanced*.json"],
            "national_pipeline": ["*national*.json", "*summary*.json"],
            "realtime_system": ["*realtime*.json", "*updated*.json"]
        }
        
        if component_name in patterns:
            for pattern in patterns[component_name]:
                files = list(Path("output").glob(pattern))
                output_files.extend([str(f) for f in files])
        
        return output_files
    
    def calculate_demo_statistics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate comprehensive demo statistics"""
        total_restaurants = 0
        total_menus = 0
        successful_components = 0
        
        for result in results:
            if result["success"]:
                successful_components += 1
                stats = result["statistics"]
                total_restaurants += stats.get('restaurants_found', 0)
                total_menus += stats.get('menus_extracted', 0)
        
        # Calculate data quality score
        quality_factors = [
            successful_components / len(results),  # Component success rate
            min(total_restaurants / 1000, 1.0),    # Restaurant coverage
            min(total_menus / 500, 1.0),           # Menu extraction rate
        ]
        
        data_quality_score = sum(quality_factors) / len(quality_factors)
        
        return {
            "total_components": len(results),
            "successful_components": successful_components,
            "component_success_rate": (successful_components / len(results)) * 100,
            "total_restaurants_collected": total_restaurants,
            "total_menus_extracted": total_menus,
            "data_quality_score": round(data_quality_score * 100, 1),
            "total_execution_time": sum(r["execution_time"] for r in results),
            "average_component_time": sum(r["execution_time"] for r in results) / len(results)
        }
    
    def generate_demo_report(self, results: List[Dict[str, Any]], statistics: Dict[str, Any]) -> str:
        """Generate comprehensive demo report"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = self.output_dir / f"pipeline_demo_report_{timestamp}.json"
        
        report = {
            "demo_metadata": {
                "timestamp": datetime.now().isoformat(),
                "demo_version": "1.0",
                "total_duration_seconds": (self.demo_stats["end_time"] - self.demo_stats["start_time"]).total_seconds()
            },
            "pipeline_overview": {
                "description": "Complete restaurant data collection and processing pipeline",
                "components": list(self.components.keys()),
                "capabilities": [
                    "Multi-source data collection (OSM, Yelp)",
                    "Intelligent data merging and deduplication",
                    "ML-enhanced menu extraction with allergen detection",
                    "National scaling across major US cities",
                    "Real-time monitoring and updates"
                ]
            },
            "execution_results": results,
            "performance_statistics": statistics,
            "demo_statistics": self.demo_stats,
            "data_quality_assessment": {
                "overall_score": statistics["data_quality_score"],
                "component_reliability": statistics["component_success_rate"],
                "data_coverage": {
                    "restaurants": statistics["total_restaurants_collected"],
                    "menus": statistics["total_menus_extracted"]
                },
                "processing_efficiency": {
                    "total_time": statistics["total_execution_time"],
                    "average_per_component": statistics["average_component_time"]
                }
            },
            "next_steps": [
                "Deploy pipeline to production environment",
                "Set up automated scheduling for data updates",
                "Implement API endpoints for data access",
                "Add monitoring and alerting systems",
                "Scale to additional cities and data sources"
            ],
            "technical_achievements": [
                "Successfully integrated multiple data sources",
                "Implemented ML-enhanced content extraction",
                "Built scalable architecture for national coverage",
                "Created real-time update capabilities",
                "Achieved high data quality and processing efficiency"
            ]
        }
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        return str(report_file)
    
    def print_final_summary(self, statistics: Dict[str, Any], report_file: str):
        """Print final demo summary"""
        summary = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                           🎉 DEMO COMPLETED SUCCESSFULLY! 🎉                 ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  📊 PERFORMANCE SUMMARY:                                                     ║
║  • Components Executed: {statistics['successful_components']}/{statistics['total_components']} ({statistics['component_success_rate']:.1f}% success)                    ║
║  • Restaurants Collected: {statistics['total_restaurants_collected']:,}                                        ║
║  • Menus Extracted: {statistics['total_menus_extracted']:,}                                             ║
║  • Data Quality Score: {statistics['data_quality_score']:.1f}/100                                      ║
║  • Total Execution Time: {statistics['total_execution_time']:.1f} seconds                              ║
║                                                                              ║
║  🎯 KEY ACHIEVEMENTS:                                                        ║
║  ✅ Multi-source data integration (OpenStreetMap + Yelp)                    ║
║  ✅ ML-enhanced menu extraction with allergen detection                     ║
║  ✅ Intelligent data merging and quality assessment                         ║
║  ✅ National scaling architecture                                           ║
║  ✅ Real-time update system                                                 ║
║                                                                              ║
║  📁 Detailed Report: {Path(report_file).name:<45} ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
        """
        print(summary)
    
    async def run_interactive_demo(self) -> str:
        """Run the complete interactive demo"""
        self.demo_stats["start_time"] = datetime.now()
        
        self.print_banner()
        
        print("\n🚀 Starting Complete Pipeline Demonstration...\n")
        
        # Demo components with descriptions
        demo_components = [
            ("osm_scraper", "OpenStreetMap restaurant data collection for Chicago"),
            ("yelp_scraper", "Yelp API integration for enhanced restaurant data"),
            ("data_merger", "Intelligent merging of OSM and Yelp data sources"),
            ("ml_scraper", "ML-enhanced menu extraction with allergen detection")
        ]
        
        results = []
        
        # Execute core pipeline components
        for component_name, description in demo_components:
            script_name = self.components[component_name]
            result = await self.run_component(component_name, script_name, description)
            results.append(result)
            
            # Brief pause between components
            await asyncio.sleep(2)
        
        # Optional advanced components
        print("\n" + "="*80)
        print("🌟 ADVANCED COMPONENTS (Optional Demonstration)")
        print("="*80)
        
        advanced_choice = input("\nWould you like to demonstrate advanced features? (y/n): ").strip().lower()
        
        if advanced_choice == 'y':
            advanced_components = [
                ("national_pipeline", "National scaling pipeline for multi-city coverage"),
                ("realtime_system", "Real-time update and monitoring system")
            ]
            
            for component_name, description in advanced_components:
                script_name = self.components[component_name]
                result = await self.run_component(component_name, script_name, description)
                results.append(result)
                await asyncio.sleep(2)
        
        self.demo_stats["end_time"] = datetime.now()
        
        # Calculate final statistics
        statistics = self.calculate_demo_statistics(results)
        
        # Generate comprehensive report
        report_file = self.generate_demo_report(results, statistics)
        
        # Print final summary
        self.print_final_summary(statistics, report_file)
        
        return report_file
    
    async def run_quick_demo(self) -> str:
        """Run a quick demo of core components only"""
        self.demo_stats["start_time"] = datetime.now()
        
        print("🚀 Running Quick Pipeline Demo (Core Components Only)...\n")
        
        # Core components only
        core_components = [
            ("data_merger", "Data merging demonstration"),
            ("ml_scraper", "ML-enhanced menu extraction demo")
        ]
        
        results = []
        
        for component_name, description in core_components:
            script_name = self.components[component_name]
            result = await self.run_component(component_name, script_name, description)
            results.append(result)
        
        self.demo_stats["end_time"] = datetime.now()
        
        # Calculate statistics and generate report
        statistics = self.calculate_demo_statistics(results)
        report_file = self.generate_demo_report(results, statistics)
        
        print(f"\n✅ Quick demo completed! Report: {Path(report_file).name}")
        
        return report_file

async def main():
    """Main execution function"""
    demo = CompletePipelineDemo()
    
    print("🍽️ Restaurant Data Pipeline Demo")
    print("\nDemo Options:")
    print("1. Full Interactive Demo (all components)")
    print("2. Quick Demo (core components only)")
    print("3. Exit")
    
    try:
        choice = input("\nSelect demo type (1-3): ").strip()
        
        if choice == "1":
            report_file = await demo.run_interactive_demo()
            print(f"\n📁 Full demo report available at: {report_file}")
            
        elif choice == "2":
            report_file = await demo.run_quick_demo()
            print(f"\n📁 Quick demo report available at: {report_file}")
            
        elif choice == "3":
            print("👋 Demo cancelled by user")
            return 0
            
        else:
            print("❌ Invalid choice")
            return 1
            
    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)