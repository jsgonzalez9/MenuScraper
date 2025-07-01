-- MenuScraper Database Schema for Supabase
-- Comprehensive schema for restaurant data pipeline with API integration

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Restaurants table - Core restaurant information
CREATE TABLE restaurants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    url TEXT NOT NULL,
    website_url TEXT,
    phone VARCHAR(50),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(50),
    zip_code VARCHAR(20),
    country VARCHAR(50) DEFAULT 'USA',
    cuisine_type VARCHAR(100),
    price_range VARCHAR(20), -- $, $$, $$$, $$$$
    rating DECIMAL(3,2),
    review_count INTEGER,
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    business_hours JSONB,
    features JSONB, -- delivery, takeout, dine-in, etc.
    source_platform VARCHAR(50), -- yelp, google, doordash, etc.
    source_id VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    last_scraped_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Menu categories table
CREATE TABLE menu_categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    restaurant_id UUID REFERENCES restaurants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    display_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Menu items table - Core menu item data
CREATE TABLE menu_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    restaurant_id UUID REFERENCES restaurants(id) ON DELETE CASCADE,
    category_id UUID REFERENCES menu_categories(id) ON DELETE SET NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10,2),
    price_range VARCHAR(50), -- for items with price ranges
    currency VARCHAR(3) DEFAULT 'USD',
    calories INTEGER,
    serving_size VARCHAR(100),
    preparation_time INTEGER, -- in minutes
    spice_level INTEGER CHECK (spice_level >= 0 AND spice_level <= 5),
    is_available BOOLEAN DEFAULT true,
    is_featured BOOLEAN DEFAULT false,
    image_url TEXT,
    confidence_score DECIMAL(3,2), -- ML confidence score
    extraction_method VARCHAR(100),
    raw_text TEXT, -- original scraped text
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Allergens reference table
CREATE TABLE allergens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    severity_level VARCHAR(20) DEFAULT 'medium', -- low, medium, high, severe
    icon_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Menu item allergens junction table
CREATE TABLE menu_item_allergens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    menu_item_id UUID REFERENCES menu_items(id) ON DELETE CASCADE,
    allergen_id UUID REFERENCES allergens(id) ON DELETE CASCADE,
    risk_level VARCHAR(20) DEFAULT 'medium', -- low, medium, high
    confidence_score DECIMAL(3,2),
    detection_method VARCHAR(100), -- ml_pattern, manual, api
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(menu_item_id, allergen_id)
);

-- Dietary tags table
CREATE TABLE dietary_tags (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    icon_url TEXT,
    color_code VARCHAR(7), -- hex color
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Menu item dietary tags junction table
CREATE TABLE menu_item_dietary_tags (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    menu_item_id UUID REFERENCES menu_items(id) ON DELETE CASCADE,
    dietary_tag_id UUID REFERENCES dietary_tags(id) ON DELETE CASCADE,
    confidence_score DECIMAL(3,2),
    detection_method VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(menu_item_id, dietary_tag_id)
);

-- Scraping sessions table - Track scraping operations
CREATE TABLE scraping_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    restaurant_id UUID REFERENCES restaurants(id) ON DELETE CASCADE,
    scraper_version VARCHAR(100),
    scraper_type VARCHAR(100), -- practical_ml, enhanced_dynamic, etc.
    start_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    end_time TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) DEFAULT 'running', -- running, completed, failed, partial
    total_items_found INTEGER DEFAULT 0,
    items_processed INTEGER DEFAULT 0,
    items_with_prices INTEGER DEFAULT 0,
    items_with_allergens INTEGER DEFAULT 0,
    average_confidence DECIMAL(3,2),
    extraction_methods JSONB,
    error_log TEXT,
    performance_metrics JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- API usage tracking
CREATE TABLE api_usage_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    endpoint VARCHAR(255),
    method VARCHAR(10),
    user_agent TEXT,
    ip_address INET,
    request_params JSONB,
    response_status INTEGER,
    response_time_ms INTEGER,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User favorites (for future frontend integration)
CREATE TABLE user_favorites (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID, -- will reference users table when auth is implemented
    restaurant_id UUID REFERENCES restaurants(id) ON DELETE CASCADE,
    menu_item_id UUID REFERENCES menu_items(id) ON DELETE CASCADE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, restaurant_id, menu_item_id)
);

-- Indexes for performance optimization
CREATE INDEX idx_restaurants_city_state ON restaurants(city, state);
CREATE INDEX idx_restaurants_cuisine_type ON restaurants(cuisine_type);
CREATE INDEX idx_restaurants_source_platform ON restaurants(source_platform);
CREATE INDEX idx_restaurants_last_scraped ON restaurants(last_scraped_at);
CREATE INDEX idx_restaurants_location ON restaurants(latitude, longitude);

CREATE INDEX idx_menu_items_restaurant_id ON menu_items(restaurant_id);
CREATE INDEX idx_menu_items_category_id ON menu_items(category_id);
CREATE INDEX idx_menu_items_price ON menu_items(price);
CREATE INDEX idx_menu_items_name_search ON menu_items USING gin(to_tsvector('english', name));
CREATE INDEX idx_menu_items_description_search ON menu_items USING gin(to_tsvector('english', description));

CREATE INDEX idx_menu_item_allergens_menu_item ON menu_item_allergens(menu_item_id);
CREATE INDEX idx_menu_item_allergens_allergen ON menu_item_allergens(allergen_id);

CREATE INDEX idx_scraping_sessions_restaurant ON scraping_sessions(restaurant_id);
CREATE INDEX idx_scraping_sessions_status ON scraping_sessions(status);
CREATE INDEX idx_scraping_sessions_start_time ON scraping_sessions(start_time);

CREATE INDEX idx_api_usage_endpoint ON api_usage_logs(endpoint);
CREATE INDEX idx_api_usage_created_at ON api_usage_logs(created_at);

-- Insert default allergens
INSERT INTO allergens (name, description, severity_level) VALUES
('gluten', 'Contains gluten from wheat, barley, rye, or oats', 'medium'),
('dairy', 'Contains milk, cheese, cream, butter, or other dairy products', 'medium'),
('nuts', 'Contains tree nuts such as almonds, walnuts, pecans, cashews', 'high'),
('peanuts', 'Contains peanuts or peanut-derived ingredients', 'high'),
('eggs', 'Contains eggs or egg-derived ingredients', 'medium'),
('soy', 'Contains soy or soy-derived ingredients', 'medium'),
('fish', 'Contains fish or fish-derived ingredients', 'medium'),
('shellfish', 'Contains shellfish such as shrimp, crab, lobster, oysters', 'high'),
('sesame', 'Contains sesame seeds or sesame-derived ingredients', 'medium');

-- Insert default dietary tags
INSERT INTO dietary_tags (name, description, color_code) VALUES
('vegetarian', 'Suitable for vegetarians', '#4CAF50'),
('vegan', 'Suitable for vegans - no animal products', '#2E7D32'),
('gluten-free', 'Does not contain gluten', '#FF9800'),
('keto', 'Suitable for ketogenic diet', '#9C27B0'),
('paleo', 'Suitable for paleo diet', '#795548'),
('organic', 'Made with organic ingredients', '#8BC34A'),
('spicy', 'Contains spicy ingredients', '#F44336'),
('low-carb', 'Low in carbohydrates', '#3F51B5'),
('high-protein', 'High in protein content', '#E91E63'),
('dairy-free', 'Does not contain dairy products', '#00BCD4');

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at triggers
CREATE TRIGGER update_restaurants_updated_at BEFORE UPDATE ON restaurants FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_menu_categories_updated_at BEFORE UPDATE ON menu_categories FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_menu_items_updated_at BEFORE UPDATE ON menu_items FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security (RLS) policies for API access
ALTER TABLE restaurants ENABLE ROW LEVEL SECURITY;
ALTER TABLE menu_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE menu_categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE scraping_sessions ENABLE ROW LEVEL SECURITY;

-- Public read access policies (adjust based on your security requirements)
CREATE POLICY "Public restaurants read" ON restaurants FOR SELECT USING (true);
CREATE POLICY "Public menu items read" ON menu_items FOR SELECT USING (true);
CREATE POLICY "Public menu categories read" ON menu_categories FOR SELECT USING (true);
CREATE POLICY "Public allergens read" ON allergens FOR SELECT USING (true);
CREATE POLICY "Public dietary tags read" ON dietary_tags FOR SELECT USING (true);

-- API service role policies (for scraper access)
-- Note: Replace 'service_role' with your actual service role
-- CREATE POLICY "Service role full access" ON restaurants FOR ALL USING (auth.role() = 'service_role');
-- CREATE POLICY "Service role menu items" ON menu_items FOR ALL USING (auth.role() = 'service_role');

-- Views for API endpoints
CREATE VIEW restaurant_summary AS
SELECT 
    r.id,
    r.name,
    r.cuisine_type,
    r.city,
    r.state,
    r.price_range,
    r.rating,
    COUNT(mi.id) as menu_item_count,
    MAX(r.last_scraped_at) as last_scraped_at,
    r.created_at
FROM restaurants r
LEFT JOIN menu_items mi ON r.id = mi.restaurant_id
WHERE r.is_active = true
GROUP BY r.id, r.name, r.cuisine_type, r.city, r.state, r.price_range, r.rating, r.created_at;

CREATE VIEW menu_items_with_details AS
SELECT 
    mi.id,
    mi.restaurant_id,
    r.name as restaurant_name,
    mc.name as category_name,
    mi.name,
    mi.description,
    mi.price,
    mi.calories,
    mi.spice_level,
    mi.confidence_score,
    ARRAY_AGG(DISTINCT a.name) FILTER (WHERE a.name IS NOT NULL) as allergens,
    ARRAY_AGG(DISTINCT dt.name) FILTER (WHERE dt.name IS NOT NULL) as dietary_tags,
    mi.created_at,
    mi.updated_at
FROM menu_items mi
JOIN restaurants r ON mi.restaurant_id = r.id
LEFT JOIN menu_categories mc ON mi.category_id = mc.id
LEFT JOIN menu_item_allergens mia ON mi.id = mia.menu_item_id
LEFT JOIN allergens a ON mia.allergen_id = a.id
LEFT JOIN menu_item_dietary_tags midt ON mi.id = midt.menu_item_id
LEFT JOIN dietary_tags dt ON midt.dietary_tag_id = dt.id
WHERE mi.is_available = true
GROUP BY mi.id, r.name, mc.name, mi.name, mi.description, mi.price, mi.calories, mi.spice_level, mi.confidence_score, mi.created_at, mi.updated_at;

-- Function to get restaurant statistics
CREATE OR REPLACE FUNCTION get_restaurant_stats(restaurant_uuid UUID)
RETURNS JSON AS $$
DECLARE
    result JSON;
BEGIN
    SELECT json_build_object(
        'total_menu_items', COUNT(mi.id),
        'items_with_prices', COUNT(mi.id) FILTER (WHERE mi.price IS NOT NULL),
        'items_with_allergens', COUNT(DISTINCT mia.menu_item_id),
        'average_price', ROUND(AVG(mi.price), 2),
        'price_range', json_build_object(
            'min', MIN(mi.price),
            'max', MAX(mi.price)
        ),
        'allergen_breakdown', (
            SELECT json_object_agg(a.name, COUNT(mia.menu_item_id))
            FROM allergens a
            LEFT JOIN menu_item_allergens mia ON a.id = mia.allergen_id
            LEFT JOIN menu_items mi2 ON mia.menu_item_id = mi2.id
            WHERE mi2.restaurant_id = restaurant_uuid
            GROUP BY a.name
        ),
        'last_updated', MAX(mi.updated_at)
    ) INTO result
    FROM menu_items mi
    LEFT JOIN menu_item_allergens mia ON mi.id = mia.menu_item_id
    WHERE mi.restaurant_id = restaurant_uuid AND mi.is_available = true;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

COMMENT ON TABLE restaurants IS 'Core restaurant information and metadata';
COMMENT ON TABLE menu_items IS 'Individual menu items with pricing and details';
COMMENT ON TABLE allergens IS 'Reference table for allergen types';
COMMENT ON TABLE menu_item_allergens IS 'Junction table linking menu items to allergens';
COMMENT ON TABLE scraping_sessions IS 'Tracking and analytics for scraping operations';
COMMENT ON TABLE api_usage_logs IS 'API usage monitoring and analytics';