# MenuScraper Playwright 🍽️

A comprehensive web scraping solution for extracting restaurant menu data using Playwright. This project includes multiple scraper implementations with advanced features like OCR integration, machine learning enhancement, and optimized content detection.

## 🆕 Phase 1 Improvements (Latest)

**Enhanced Yelp Detection & Official Website Fallback**

- **🔍 Enhanced Yelp Menu Detection**: Comprehensive price extraction patterns and improved dynamic content handling with Yelp-specific scrolling strategies
- **🌐 Restaurant Website Discovery**: Google search integration to automatically find official restaurant websites
- **🔄 Intelligent Fallback Logic**: When primary URL (e.g., Yelp) yields insufficient results, automatically falls back to scraping the discovered official website
- **📈 Improved Content Handling**: Enhanced dynamic content waiting and better navigation for modern restaurant websites
- **🎯 Better Extraction Coverage**: Combines results from multiple sources for comprehensive menu data

### Quick Demo of Phase 1 Features

```python
from enhanced_dynamic_scraper import EnhancedDynamicScraper
import asyncio

async def demo_phase1():
    scraper = EnhancedDynamicScraper(headless=True)
    await scraper.setup_browser()
    
    # New extract_menu_items method with fallback logic
    result = await scraper.extract_menu_items(
        url="https://www.yelp.com/biz/restaurant-name",
        restaurant_name="Restaurant Name"
    )
    
    print(f"Primary extraction: {result['total_items']} items")
    if result.get('fallback_url'):
        print(f"Fallback used: {result['fallback_url']}")
    
    await scraper.cleanup()

# Run Phase 1 demo
python demo_phase1.py
```

## 🚀 Core Features

- **Multiple Scraper Implementations**: From basic to advanced ML-enhanced scrapers
- **Smart Content Detection**: Intelligent menu content identification and extraction
- **Price Pattern Recognition**: Advanced regex patterns for various price formats
- **Dynamic Content Handling**: Supports JavaScript-heavy websites and lazy loading
- **OCR Integration**: Extract menu data from images
- **Machine Learning Enhancement**: AI-powered content classification and filtering
- **Multi-Platform Support**: Yelp, OpenTable, TripAdvisor, and more
- **Comprehensive Testing**: Extensive test suites with performance metrics

## 📊 Performance Results

| Scraper Version | Success Rate | Items Extracted | Price Coverage | Description Coverage |
|----------------|--------------|-----------------|----------------|---------------------|
| Enhanced Dynamic | 35.0% | 84 items | 0.0% | 0.0% |
| Priority1 Optimized | 30.0% | 102 items | 0.0% | 11.8% |
| ML Enhanced | 25.0% | 95 items | 5.3% | 15.8% |
| Production Ready | 40.0% | 120 items | 8.3% | 20.0% |

## 🛠️ Installation

### Prerequisites

- Python 3.8+
- Node.js (for Playwright)

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/MenuScraper_Playwright.git
   cd MenuScraper_Playwright
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Playwright browsers**
   ```bash
   playwright install
   ```

## 🎯 Quick Start

### Basic Menu Scraping

```python
from enhanced_dynamic_scraper import EnhancedDynamicScraper
import asyncio

async def scrape_menu():
    scraper = EnhancedDynamicScraper(headless=True)
    await scraper.setup_browser()
    
    restaurant_data = {
        'name': 'Restaurant Name',
        'url': 'https://example-restaurant-url.com'
    }
    
    result = await scraper.scrape_restaurant_enhanced(restaurant_data)
    print(f"Success: {result['scraping_success']}")
    print(f"Items found: {len(result['items'])}")
    
    await scraper.close()

# Run the scraper
asyncio.run(scrape_menu())
```

### Advanced ML-Enhanced Scraping

```python
from ml_enhanced_menu_scraper import MLEnhancedMenuScraper

async def advanced_scrape():
    scraper = MLEnhancedMenuScraper(headless=True)
    await scraper.setup_browser()
    
    # Scrape with ML classification
    result = await scraper.scrape_restaurant(restaurant_data)
    
    # Access enhanced features
    for item in result['items']:
        print(f"Item: {item['name']}")
        print(f"Price: ${item['price']}")
        print(f"Category: {item['category']}")
        print(f"Confidence: {item['confidence_score']:.2f}")
    
    await scraper.close()

asyncio.run(advanced_scrape())
```

## 📁 Project Structure

```
MenuScraper_Playwright/
├── 📄 Core Scrapers
│   ├── enhanced_dynamic_scraper.py      # Main enhanced scraper
│   ├── ml_enhanced_menu_scraper.py      # ML-powered scraper
│   ├── production_menu_scraper.py       # Production-ready version
│   └── priority1_optimized_scraper.py   # Optimized implementation
│
├── 🧪 Testing & Analysis
│   ├── test_enhanced_dynamic_scraper.py
│   ├── test_ml_enhanced_scraper.py
│   └── test_production_scraper.py
│
├── 📊 Results & Documentation
│   ├── Enhanced_Scraper_Results.md
│   ├── ML_Integration_Analysis_Report.md
│   └── Menu_Scraping_Improvement_Strategy.md
│
├── 🔧 Utilities
│   ├── chicago_restaurant_scraper.py
│   ├── yelp_api_chicago_scraper.py
│   └── foursquare_api_chicago_scraper.py
│
└── 📋 Configuration
    ├── requirements.txt
    ├── requirements_ml.txt
    └── restaurant_data.json
```

## 🎛️ Available Scrapers

### 1. Enhanced Dynamic Scraper
**Best for**: General-purpose menu extraction
- Smart content detection
- Dynamic loading support
- Menu link navigation

### 2. ML Enhanced Scraper
**Best for**: High-accuracy content classification
- Machine learning content filtering
- Advanced categorization
- Confidence scoring

### 3. Production Scraper
**Best for**: Production environments
- Robust error handling
- Performance optimization
- Comprehensive logging

### 4. Priority1 Optimized
**Best for**: Balanced performance
- Optimized extraction strategies
- Moderate filtering
- Good success rates

## 🔧 Configuration

### Scraper Settings

```python
scraper = EnhancedDynamicScraper(
    headless=True,          # Run in headless mode
    timeout=30000,          # Page timeout in ms
    max_retries=3,          # Retry attempts
    delay_between_requests=2 # Delay in seconds
)
```

### Content Detection Parameters

```python
# Customize food keywords
food_keywords = [
    'burger', 'pizza', 'pasta', 'salad', 'sandwich',
    'steak', 'chicken', 'fish', 'soup', 'appetizer'
]

# Price patterns
price_patterns = [
    r'\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # $12.99
    r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*\$',  # 12.99$
    r'USD\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'   # USD 12.99
]
```

## 📈 Testing & Evaluation

### Run Comprehensive Tests

```bash
# Test Phase 1 improvements (NEW)
python test_phase1_improvements.py

# Quick Phase 1 demo (NEW)
python demo_phase1.py

# Test enhanced scraper
python test_enhanced_dynamic_scraper.py

# Test ML scraper
python test_ml_enhanced_scraper.py

# Test production scraper
python test_production_scraper.py
```

### Phase 1 Testing Features

The new Phase 1 test suite (`test_phase1_improvements.py`) provides:
- **Fallback Logic Testing**: Validates automatic website discovery and fallback scraping
- **Enhanced Yelp Detection**: Tests improved price extraction and dynamic content handling
- **Performance Metrics**: Detailed analytics on extraction methods and success rates
- **Comprehensive Reporting**: JSON output with detailed results and performance data
- **Multi-Restaurant Testing**: Tests across various restaurant types and platforms

### Performance Metrics

The testing framework provides detailed metrics:
- **Success Rate**: Percentage of successful extractions
- **Content Quality**: Price and description coverage
- **Extraction Methods**: Which strategies work best
- **Error Analysis**: Common failure patterns
- **Performance Comparison**: Benchmarking across versions

## 🎨 Advanced Features

### OCR Integration

```python
from demo_ocr_menu_scraping import OCRMenuScraper

# Extract text from menu images
scraper = OCRMenuScraper()
text_data = await scraper.extract_text_from_images(image_urls)
```

### Health-Focused Extraction

```python
from health_menu_scraper import HealthMenuScraper

# Focus on nutritional information
scraper = HealthMenuScraper()
health_data = await scraper.extract_health_info(restaurant_url)
```

### API Integration

```python
# Yelp API integration
from yelp_api_chicago_scraper import YelpAPIScraper

# Foursquare API integration
from foursquare_api_chicago_scraper import FoursquareAPIScraper
```

## 🚨 Common Issues & Solutions

### Issue: Low Success Rate
**Solution**: Use Priority1OptimizedScraper with balanced filtering

### Issue: No Price Detection
**Solution**: Implement price-focused extraction strategy

### Issue: Navigation Failures
**Solution**: Enable smart menu link detection

### Issue: Dynamic Content Not Loading
**Solution**: Increase timeout and enable content waiting

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Playwright Team** for the excellent browser automation framework
- **scikit-learn** for machine learning capabilities
- **OpenCV & Tesseract** for OCR functionality
- **Restaurant data providers** for testing datasets

## 📞 Support

For support, please open an issue on GitHub or contact the development team.

---

**Built with ❤️ for the restaurant industry and data enthusiasts**
