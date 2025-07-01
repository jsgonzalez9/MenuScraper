# Proxy Usage Guide for Enhanced Menu Scraper

## Overview
The Enhanced Website Menu Scraper now supports proxy configuration for improved scraping capabilities, rate limit avoidance, and IP rotation.

## Features
✅ **Proxy Support Added**: Full proxy integration with Playwright browser
✅ **Easy Configuration**: Simple proxy parameter in constructor
✅ **Error Handling**: Graceful handling of proxy connection failures
✅ **Flexible Usage**: Works with HTTP/HTTPS/SOCKS proxies
✅ **Testing Ready**: Comprehensive test scripts included

## Basic Usage

### 1. Without Proxy (Direct Connection)
```python
from enhanced_website_menu_scraper import EnhancedWebsiteMenuScraper

# Initialize without proxy
scraper = EnhancedWebsiteMenuScraper(headless=True)

# Scrape a restaurant
result = await scraper.scrape_restaurant_menu(
    restaurant_name="Alinea Chicago",
    direct_url="https://www.alinearestaurant.com"
)
```

### 2. With Single Proxy
```python
# Initialize with proxy
scraper = EnhancedWebsiteMenuScraper(
    headless=True,
    proxy="http://username:password@proxy.example.com:8080"
)

# Scrape with proxy
result = await scraper.scrape_restaurant_menu(
    restaurant_name="Girl & the Goat Chicago",
    direct_url="https://www.girlandthegoat.com"
)
```

### 3. Proxy Rotation Pattern
```python
proxy_list = [
    "http://proxy1.example.com:8080",
    "http://proxy2.example.com:8080",
    "http://proxy3.example.com:8080"
]

restaurants = [
    {"name": "Restaurant 1", "url": "https://restaurant1.com"},
    {"name": "Restaurant 2", "url": "https://restaurant2.com"},
    {"name": "Restaurant 3", "url": "https://restaurant3.com"}
]

# Rotate proxies for each request
for i, restaurant in enumerate(restaurants):
    proxy = proxy_list[i % len(proxy_list)]  # Rotate through proxies
    
    scraper = EnhancedWebsiteMenuScraper(proxy=proxy)
    result = await scraper.scrape_restaurant_menu(
        restaurant_name=restaurant["name"],
        direct_url=restaurant["url"]
    )
    print(f"Used proxy: {proxy}, Success: {result['success']}")
```

## Proxy Formats Supported

### HTTP Proxy
```python
proxy = "http://proxy.example.com:8080"
```

### HTTP Proxy with Authentication
```python
proxy = "http://username:password@proxy.example.com:8080"
```

### HTTPS Proxy
```python
proxy = "https://proxy.example.com:8080"
```

### SOCKS Proxy
```python
proxy = "socks5://proxy.example.com:1080"
```

## Testing Scripts

### 1. Proxy Readiness Test
```bash
python test_proxy_readiness.py
```
Tests basic proxy functionality and parameter acceptance.

### 2. Comprehensive Proxy Test
```bash
python test_proxy_enhanced_scraper.py
```
Full proxy testing with multiple configurations.

### 3. Custom Proxy Test
Modify `test_proxy_enhanced_scraper.py` and add your proxy list:
```python
proxy_list = [
    "http://your-proxy1:port",
    "http://your-proxy2:port"
]
```

## Benefits of Using Proxies

### 🚀 **Performance Benefits**
- **Rate Limit Avoidance**: Distribute requests across multiple IPs
- **Higher Throughput**: Parallel scraping with different proxies
- **Reduced Blocking**: Lower chance of IP-based blocks

### 🛡️ **Reliability Benefits**
- **Geographic Distribution**: Access from different locations
- **Redundancy**: Fallback options if one proxy fails
- **Load Distribution**: Spread traffic across proxy network

### 🔒 **Privacy Benefits**
- **IP Masking**: Hide your actual IP address
- **Location Flexibility**: Appear to browse from different regions
- **Enhanced Anonymity**: Reduce tracking and fingerprinting

## Error Handling

The scraper includes comprehensive error handling for proxy issues:

```python
# Example error responses
{
    "success": false,
    "error": "Page.goto: net::ERR_PROXY_CONNECTION_FAILED",
    "processing_time": 2.45
}
```

Common proxy errors:
- `ERR_PROXY_CONNECTION_FAILED`: Proxy server unreachable
- `ERR_PROXY_AUTH_FAILED`: Invalid proxy credentials
- `ERR_TUNNEL_CONNECTION_FAILED`: HTTPS tunnel setup failed

## Best Practices

### 1. **Proxy Rotation**
- Rotate proxies between requests to avoid rate limits
- Use different proxies for different restaurant chains
- Implement random delays between proxy switches

### 2. **Error Recovery**
- Always have fallback proxies available
- Implement retry logic with different proxies
- Monitor proxy health and response times

### 3. **Performance Optimization**
- Test proxy speed before bulk operations
- Use geographically appropriate proxies
- Monitor success rates per proxy

### 4. **Security**
- Use authenticated proxies when possible
- Avoid free/public proxies for production
- Regularly rotate proxy credentials

## Configuration Examples

### Development Setup
```python
# For testing and development
scraper = EnhancedWebsiteMenuScraper(
    headless=True,
    timeout=30000,
    proxy=None  # Direct connection for development
)
```

### Production Setup
```python
# For production with proxy rotation
proxy_pool = [
    "http://user1:pass1@premium-proxy1.com:8080",
    "http://user2:pass2@premium-proxy2.com:8080",
    "http://user3:pass3@premium-proxy3.com:8080"
]

# Select proxy based on request or round-robin
current_proxy = proxy_pool[request_count % len(proxy_pool)]

scraper = EnhancedWebsiteMenuScraper(
    headless=True,
    timeout=45000,  # Longer timeout for proxy connections
    proxy=current_proxy
)
```

## Monitoring and Logging

The scraper provides detailed logging for proxy usage:

```
🌐 Using proxy: http://proxy.example.com:8080
🌐 Navigating to: https://www.restaurant.com
✅ Success: 25 items extracted
⏱️  Processing time: 8.45s
```

## Next Steps

1. **Test without proxies** to establish baseline performance
2. **Add your proxy list** to the test scripts
3. **Run comprehensive tests** with your proxies
4. **Implement proxy rotation** in your production code
5. **Monitor success rates** and adjust proxy usage accordingly

## Support

The enhanced scraper is now fully proxy-ready and tested. All existing functionality remains unchanged, with proxy support as an optional enhancement.

**Ready for your proxy list!** 🚀