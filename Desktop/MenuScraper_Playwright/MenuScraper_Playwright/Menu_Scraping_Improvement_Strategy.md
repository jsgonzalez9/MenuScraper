# Menu Scraping Success Rate Improvement Strategy

## Current Performance Analysis

### Current State (15% Success Rate)
- **Total Restaurants**: 130
- **Successful Extractions**: 2-3 restaurants
- **Menu Items Collected**: 11-20 items
- **Primary Success Method**: CSS selector-based scraping
- **OCR Usage**: Minimal (not triggered in successful cases)
- **Main Limitation**: Relying only on Yelp restaurant pages

## Target: 50-75% Success Rate

### Strategy 1: Multi-Platform Menu Discovery (Expected +30-40% success)

#### 1.1 Direct Restaurant Website Integration
```python
# Add restaurant website discovery
def find_restaurant_website(restaurant_name, location):
    # Google search for official website
    # Extract menu links from official sites
    # Common patterns: /menu, /food, /our-menu
```

#### 1.2 Third-Party Menu Platforms
- **DoorDash/Uber Eats**: Often have complete menus
- **Grubhub**: Detailed menu with prices
- **MenuPix/Zomato**: Menu photo databases
- **OpenTable**: Restaurant menu integration

#### 1.3 Implementation Priority
1. Google search for restaurant websites
2. DoorDash/Uber Eats menu scraping
3. Grubhub integration
4. Social media menu discovery (Facebook, Instagram)

### Strategy 2: Enhanced OCR Implementation (Expected +15-20% success)

#### 2.1 Targeted Image Menu Detection
```python
# Improve image detection
image_selectors = [
    'img[src*="menu"]',
    'img[alt*="menu"]',
    'img[class*="menu"]',
    '.menu-image img',
    '[data-test*="menu"] img',
    'a[href*="menu"] img'
]
```

#### 2.2 OCR Quality Improvements
- **Image preprocessing**: Contrast enhancement, noise reduction
- **Multiple OCR engines**: EasyOCR + Tesseract + PaddleOCR
- **Confidence scoring**: Combine results from multiple engines
- **Menu-specific training**: Fine-tune OCR for menu text patterns

#### 2.3 Menu Image Sources
- Yelp photo galleries
- Google Images search
- Restaurant social media
- Review photos containing menus

### Strategy 3: Advanced Web Scraping Techniques (Expected +10-15% success)

#### 3.1 Dynamic Content Handling
```python
# Enhanced page interaction
def enhanced_menu_scraping(page, url):
    # Wait for dynamic content
    page.wait_for_function("document.readyState === 'complete'")
    
    # Trigger menu loading
    menu_triggers = ['button:has-text("Menu")', '.menu-toggle', '[data-menu]']
    for trigger in menu_triggers:
        try:
            page.click(trigger)
            page.wait_for_timeout(2000)
        except:
            continue
    
    # Scroll to load lazy content
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(1000)
```

#### 3.2 Enhanced Selectors
```python
# More comprehensive menu item detection
menu_selectors = [
    # Standard patterns
    '[class*="menu-item"]', '[data-test*="menu-item"]',
    # Food delivery patterns
    '[class*="dish"]', '[class*="food-item"]',
    # Restaurant-specific patterns
    '.item-card', '.product-card', '.menu-product',
    # Price-based detection
    '*:has-text("$") >> xpath=ancestor::*[1]',
    # Description-based detection
    '*:has-text("served with") >> xpath=ancestor::*[1]'
]
```

### Strategy 4: Menu Data Sources Diversification (Expected +20-25% success)

#### 4.1 API Integration
```python
# Restaurant data APIs
APIS_TO_INTEGRATE = {
    'foursquare': 'Menu photos and basic info',
    'google_places': 'Restaurant details and photos',
    'yelp_business': 'Enhanced business data',
    'tripadvisor': 'Menu photos from reviews'
}
```

#### 4.2 Social Media Menu Discovery
- **Facebook Pages**: Menu tabs and photo albums
- **Instagram**: Menu highlight stories and posts
- **Twitter**: Menu announcements and photos

#### 4.3 Review Mining
```python
# Extract menu items from reviews
def extract_menu_from_reviews(reviews):
    food_patterns = [
        r'I ordered the ([^.!?]+)',
        r'The ([^.!?]+) was delicious',
        r'Try the ([^.!?]+)',
        r'([A-Z][a-z]+ [A-Z][a-z]+) \$([0-9]+)'
    ]
```

### Strategy 5: Machine Learning Enhancement (Expected +5-10% success)

#### 5.1 Menu Item Classification
```python
# Train ML model to identify menu items
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier

# Features: text patterns, price presence, food keywords
# Labels: menu_item vs non_menu_item
```

#### 5.2 Price Extraction Improvement
```python
# Enhanced price patterns
price_patterns = [
    r'\$([0-9]+(?:\.[0-9]{2})?)',  # $12.99
    r'([0-9]+(?:\.[0-9]{2})?)\$',  # 12.99$
    r'\$ ([0-9]+(?:\.[0-9]{2})?)', # $ 12.99
    r'USD ([0-9]+(?:\.[0-9]{2})?)', # USD 12.99
    r'([0-9]+) dollars?',           # 12 dollars
]
```

## Implementation Roadmap

### Phase 1: Quick Wins (Week 1-2) - Target: 25-30% success
1. **Enhanced Yelp Menu Detection**
   - Improve CSS selectors
   - Add dynamic content handling
   - Better price extraction patterns

2. **Restaurant Website Discovery**
   - Google search integration
   - Direct website menu scraping

### Phase 2: Platform Integration (Week 3-4) - Target: 40-50% success
1. **DoorDash/Uber Eats Integration**
   - Menu scraping from delivery platforms
   - Price and description extraction

2. **Enhanced OCR Implementation**
   - Multiple OCR engines
   - Image preprocessing
   - Menu photo detection

### Phase 3: Advanced Features (Week 5-6) - Target: 60-75% success
1. **Social Media Integration**
   - Facebook menu discovery
   - Instagram menu extraction

2. **Review Mining**
   - Extract menu items from customer reviews
   - Sentiment-based menu recommendations

3. **Machine Learning Enhancement**
   - Menu item classification
   - Confidence scoring

## Expected Results

### Conservative Estimate (50% success rate)
- **Current**: 2-3 successful restaurants out of 130
- **Improved**: 65 successful restaurants out of 130
- **Menu Items**: 500-800 items (vs current 11-20)

### Optimistic Estimate (75% success rate)
- **Successful Restaurants**: 97 out of 130
- **Menu Items**: 1,200-2,000 items
- **Data Quality**: Higher accuracy with multiple source validation

## Technical Requirements

### Additional Dependencies
```txt
# Add to requirements_menu.txt
selenium>=4.15.0
requests-html>=0.10.0
paddleocr>=2.7.0
scikit-learn>=1.3.0
textblob>=0.17.1
facebook-sdk>=3.1.0
```

### Infrastructure Considerations
- **Rate Limiting**: Implement proper delays between requests
- **Proxy Rotation**: Avoid IP blocking
- **Caching**: Store successful menu data
- **Error Handling**: Robust fallback mechanisms

## Success Metrics

### Primary KPIs
1. **Menu Extraction Success Rate**: Target 50-75%
2. **Menu Items per Restaurant**: Target 8-15 items
3. **Price Accuracy**: Target 80%+ with valid prices
4. **Allergen Detection**: Target 60%+ coverage

### Quality Metrics
1. **Data Completeness**: Name, description, price
2. **Duplicate Detection**: Avoid duplicate menu items
3. **Relevance Score**: Filter out non-menu content
4. **Source Diversity**: Multiple data sources per restaurant

This comprehensive strategy addresses the current limitations and provides a clear path to achieving 50-75% success rate through multiple complementary approaches.