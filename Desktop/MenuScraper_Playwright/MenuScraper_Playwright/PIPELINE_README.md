# 🍽️ Complete Restaurant Data Pipeline

A comprehensive, production-ready restaurant data collection and processing system featuring multi-source integration, ML-enhanced menu extraction, and real-time updates.

## 🌟 System Overview

This pipeline represents a complete solution for restaurant data collection, processing, and maintenance at scale. It combines multiple data sources, advanced extraction techniques, and intelligent processing to create a comprehensive restaurant database with detailed menu information and allergen detection.

### 🎯 Key Features

- **Multi-Source Data Integration**: OpenStreetMap + Yelp API
- **ML-Enhanced Menu Extraction**: Advanced content analysis with allergen detection
- **Intelligent Data Merging**: Smart deduplication and quality assessment
- **National Scaling**: Architecture for multi-city expansion
- **Real-Time Updates**: Continuous monitoring and data refresh
- **Production Ready**: Comprehensive error handling and logging

## 🏗️ Architecture Components

### 1. Data Collection Layer

#### OpenStreetMap Integration (`openstreetmap_chicago_scraper.py`)
- Collects comprehensive restaurant data from OpenStreetMap
- Provides geographic coordinates, addresses, and basic amenity information
- Handles large-scale data extraction with rate limiting

#### Yelp API Integration (`yelp_optimized_chicago_scraper.py`)
- Enriches data with business details, ratings, and reviews
- Provides pricing information and business hours
- Includes photo URLs and category classifications

### 2. Data Processing Layer

#### Comprehensive Data Merger (`comprehensive_data_merger.py`)
- Intelligently merges OSM and Yelp data sources
- Implements fuzzy matching for restaurant identification
- Calculates data quality scores and confidence metrics
- Handles address normalization and phone number formatting

#### ML-Enhanced Menu Scraper (`ml_enhanced_menu_scraper.py`)
- Advanced menu extraction using multiple strategies
- ML-inspired allergen detection and dietary tag classification
- Confidence scoring for extracted menu items
- Comprehensive error handling and retry logic

### 3. Scaling Layer

#### National Scaling Pipeline (`national_scaling_pipeline.py`)
- Extends data collection to major US cities
- Priority-based processing for efficient resource utilization
- Concurrent processing with rate limiting
- Comprehensive progress tracking and reporting

#### Real-Time Update System (`realtime_update_system.py`)
- Continuous monitoring of restaurant data changes
- Automated menu updates and quality checks
- Change detection and notification system
- Performance metrics and alerting

### 4. Demonstration Layer

#### Complete Pipeline Demo (`complete_pipeline_demo.py`)
- Interactive demonstration of all pipeline components
- Performance benchmarking and quality assessment
- Comprehensive reporting and statistics
- User-friendly interface for testing and validation

## 🚀 Quick Start

### Prerequisites

```bash
# Install required dependencies
pip install -r requirements.txt
pip install -r requirements_ml.txt

# Ensure you have the following API keys (if using Yelp integration):
# - Yelp API Key (optional, for enhanced data)
```

### Running the Complete Demo

```bash
# Run the interactive pipeline demonstration
python complete_pipeline_demo.py

# Choose from:
# 1. Full Interactive Demo (all components)
# 2. Quick Demo (core components only)
```

### Running Individual Components

```bash
# 1. Collect OpenStreetMap data
python openstreetmap_chicago_scraper.py

# 2. Collect Yelp data (optional)
python yelp_optimized_chicago_scraper.py

# 3. Merge data sources
python comprehensive_data_merger.py

# 4. Extract menus with ML enhancement
python ml_enhanced_menu_scraper.py

# 5. Scale to national coverage
python national_scaling_pipeline.py

# 6. Start real-time monitoring
python realtime_update_system.py
```

## 📊 Data Pipeline Flow

```
┌─────────────────┐    ┌─────────────────┐
│   OpenStreetMap │    │    Yelp API     │
│   Data Source   │    │   Data Source   │
└─────────┬───────┘    └─────────┬───────┘
          │                      │
          └──────────┬───────────┘
                     │
          ┌──────────▼───────────┐
          │  Data Merger &      │
          │  Quality Assessment │
          └──────────┬───────────┘
                     │
          ┌──────────▼───────────┐
          │  ML-Enhanced Menu   │
          │  Extraction System  │
          └──────────┬───────────┘
                     │
          ┌──────────▼───────────┐
          │  National Scaling   │
          │  & Distribution     │
          └──────────┬───────────┘
                     │
          ┌──────────▼───────────┐
          │  Real-Time Updates  │
          │  & Monitoring       │
          └─────────────────────┘
```

## 🔧 Configuration

### Environment Variables

```bash
# Optional: Yelp API integration
export YELP_API_KEY="your_yelp_api_key_here"

# Optional: Custom output directory
export PIPELINE_OUTPUT_DIR="/path/to/output"

# Optional: Logging level
export LOG_LEVEL="INFO"
```

### Configuration Files

Each component supports configuration through:
- Command-line arguments
- Environment variables
- Configuration dictionaries in code

## 📈 Performance Metrics

### Typical Performance (Chicago Dataset)

| Component | Execution Time | Data Points | Success Rate |
|-----------|----------------|-------------|-------------|
| OSM Collection | 2-5 minutes | 8,000+ restaurants | 95%+ |
| Yelp Integration | 3-8 minutes | 5,000+ businesses | 90%+ |
| Data Merging | 30-60 seconds | 10,000+ records | 98%+ |
| Menu Extraction | 10-30 minutes | 1,000+ menus | 75%+ |
| Quality Assessment | 10-20 seconds | All records | 100% |

### Scaling Metrics

- **National Coverage**: 10+ major US cities
- **Concurrent Processing**: Up to 10 simultaneous requests
- **Data Freshness**: 6-24 hour update cycles
- **Storage Efficiency**: JSON format with compression

## 🧠 ML Features

### Allergen Detection

The system uses advanced pattern matching and ML-inspired techniques to detect:

- **Primary Allergens**: Gluten, Dairy, Nuts, Eggs, Soy, Fish, Shellfish, Sesame
- **Dietary Tags**: Vegetarian, Vegan, Gluten-Free, Keto, Paleo, Organic
- **Risk Assessment**: High/Medium/Low risk classification
- **Confidence Scoring**: 0.0-1.0 confidence for each detection

### Menu Extraction Strategies

1. **Structured Data Extraction**: JSON-LD, microdata parsing
2. **CSS Selector Targeting**: Advanced DOM element selection
3. **Text Pattern Analysis**: ML-inspired content classification
4. **Price-Based Detection**: Currency pattern recognition
5. **Contextual Analysis**: Surrounding content evaluation

## 📁 Output Structure

```
output/
├── chicago_restaurants_osm_YYYYMMDD_HHMMSS.json
├── chicago_restaurants_yelp_YYYYMMDD_HHMMSS.json
├── chicago_restaurants_merged_YYYYMMDD_HHMMSS.json
├── chicago_comprehensive_menus_YYYYMMDD_HHMMSS.json
├── national_summary_YYYYMMDD_HHMMSS.json
├── realtime_updated_restaurants_YYYYMMDD_HHMMSS.json
└── pipeline_demo_report_YYYYMMDD_HHMMSS.json
```

### Data Schema

#### Restaurant Record
```json
{
  "id": "unique_identifier",
  "name": "Restaurant Name",
  "cuisine": "cuisine_type",
  "coordinates": {"latitude": 41.8781, "longitude": -87.6298},
  "address": {
    "street": "123 Main St",
    "city": "Chicago",
    "state": "IL",
    "postcode": "60601"
  },
  "contact": {
    "phone": "+1-555-123-4567",
    "website": "https://example.com",
    "email": "info@restaurant.com"
  },
  "menu_items": [
    {
      "name": "Menu Item Name",
      "price": "$15.99",
      "description": "Item description",
      "allergens": ["gluten", "dairy"],
      "dietary_tags": ["vegetarian"],
      "confidence_score": 0.85
    }
  ],
  "data_quality": {
    "completeness_score": 0.92,
    "confidence_score": 0.88,
    "last_updated": "2024-01-01T12:00:00Z"
  }
}
```

## 🔍 Quality Assurance

### Data Quality Metrics

- **Completeness Score**: Percentage of filled required fields
- **Accuracy Score**: Validation against known data sources
- **Freshness Score**: Time since last update
- **Confidence Score**: ML model confidence in extracted data

### Error Handling

- **Retry Logic**: Automatic retry with exponential backoff
- **Graceful Degradation**: Partial success handling
- **Comprehensive Logging**: Detailed error tracking and reporting
- **Data Validation**: Schema validation and sanity checks

## 🚀 Production Deployment

### Recommended Infrastructure

```yaml
# Docker Compose Example
version: '3.8'
services:
  pipeline-scheduler:
    build: .
    environment:
      - YELP_API_KEY=${YELP_API_KEY}
      - LOG_LEVEL=INFO
    volumes:
      - ./output:/app/output
      - ./logs:/app/logs
    restart: unless-stopped
    
  pipeline-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - API_MODE=true
    volumes:
      - ./output:/app/output
    restart: unless-stopped
```

### Monitoring Setup

```bash
# Set up log monitoring
tail -f logs/pipeline.log | grep ERROR

# Monitor data freshness
find output/ -name "*.json" -mtime +1  # Files older than 1 day

# Check system resources
ps aux | grep python  # Monitor running processes
df -h output/         # Check disk usage
```

## 🔧 Troubleshooting

### Common Issues

#### 1. API Rate Limiting
```bash
# Symptoms: HTTP 429 errors, slow responses
# Solution: Increase delays between requests
# Edit: timeout and retry settings in scrapers
```

#### 2. Memory Issues
```bash
# Symptoms: Out of memory errors, slow processing
# Solution: Process data in smaller batches
# Edit: batch_size parameters in processing scripts
```

#### 3. Network Connectivity
```bash
# Symptoms: Connection timeouts, DNS errors
# Solution: Check network configuration
# Test: ping overpass-api.de
```

#### 4. Data Quality Issues
```bash
# Symptoms: Low confidence scores, missing data
# Solution: Review extraction patterns and selectors
# Debug: Enable verbose logging for detailed analysis
```

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with verbose output
python ml_enhanced_menu_scraper.py --verbose

# Test individual components
python -c "from comprehensive_data_merger import *; test_merger()"
```

## 📚 API Reference

### Core Classes

#### `ComprehensiveDataMerger`
```python
merger = ComprehensiveDataMerger()
result = merger.merge_restaurant_data(osm_file, yelp_file)
```

#### `MLEnhancedMenuScraper`
```python
scraper = MLEnhancedMenuScraper(headless=True)
menus = await scraper.scrape_restaurant_menus(restaurants)
```

#### `NationalScalingPipeline`
```python
pipeline = NationalScalingPipeline()
summary = await pipeline.run_national_pipeline()
```

#### `RealTimeUpdateSystem`
```python
updater = RealTimeUpdateSystem()
await updater.start_monitoring(update_interval_minutes=60)
```

## 🤝 Contributing

### Development Setup

```bash
# Clone and setup development environment
git clone <repository>
cd restaurant-pipeline
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements_ml.txt
```

### Code Style

- Follow PEP 8 guidelines
- Use type hints for function parameters
- Include comprehensive docstrings
- Add unit tests for new features

### Testing

```bash
# Run component tests
python test_comprehensive_merger.py
python test_ml_enhanced_scraper.py

# Run integration tests
python complete_pipeline_demo.py
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **OpenStreetMap**: For providing comprehensive geographic data
- **Yelp API**: For business information and reviews
- **Playwright**: For reliable web scraping capabilities
- **Python Community**: For excellent libraries and tools

## 📞 Support

For questions, issues, or contributions:

1. Check the troubleshooting section above
2. Review existing issues in the repository
3. Create a new issue with detailed information
4. Include logs and error messages when reporting bugs

---

**Built with ❤️ for the restaurant industry and data enthusiasts**

*Last updated: January 2024*