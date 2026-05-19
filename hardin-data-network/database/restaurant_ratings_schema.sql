-- UK Restaurant & Takeaway Ratings Database
-- Collected by TBN-certified bots with verified reviews

-- ============================================================================
-- RESTAURANTS & TAKEAWAYS
-- ============================================================================

CREATE TABLE restaurants (
    restaurant_id SERIAL PRIMARY KEY,
    restaurant_name VARCHAR(255),
    cuisine_type VARCHAR(100), -- kebab, turkish, indian, chinese, pizza, etc.
    business_type VARCHAR(50), -- restaurant, takeaway, both
    
    -- Location
    address TEXT,
    postcode VARCHAR(20),
    city VARCHAR(100),
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    
    -- Contact
    phone VARCHAR(50),
    email VARCHAR(255),
    website VARCHAR(500),
    
    -- Business info
    company_number VARCHAR(50), -- Companies House number
    food_hygiene_rating INT, -- 0-5 (FSA rating)
    halal_certified BOOLEAN,
    vegetarian_options BOOLEAN,
    vegan_options BOOLEAN,
    
    -- Opening hours
    opening_hours JSON, -- {"monday": "11:00-23:00", ...}
    delivery_available BOOLEAN,
    collection_available BOOLEAN,
    dine_in_available BOOLEAN,
    
    -- Pricing
    average_price_range VARCHAR(20), -- £, ££, £££, ££££
    delivery_fee DECIMAL(5,2),
    minimum_order DECIMAL(5,2),
    
    -- Ratings (calculated from reviews)
    overall_rating DECIMAL(3,2), -- 0.00-5.00
    food_quality_rating DECIMAL(3,2),
    service_rating DECIMAL(3,2),
    value_rating DECIMAL(3,2),
    hygiene_rating DECIMAL(3,2),
    total_reviews INT DEFAULT 0,
    
    -- TBN tracking
    collected_by_bot VARCHAR(255) REFERENCES tbn_bots(bot_id),
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP,
    verified_by_tbn BOOLEAN DEFAULT TRUE,
    
    -- Search optimization
    search_vector tsvector
);

-- ============================================================================
-- MENU ITEMS
-- ============================================================================

CREATE TABLE menu_items (
    item_id SERIAL PRIMARY KEY,
    restaurant_id INT REFERENCES restaurants(restaurant_id),
    item_name VARCHAR(255),
    description TEXT,
    category VARCHAR(100), -- starters, mains, sides, desserts, drinks
    
    -- Pricing
    price DECIMAL(6,2),
    special_offer VARCHAR(255),
    
    -- Dietary info
    vegetarian BOOLEAN,
    vegan BOOLEAN,
    gluten_free BOOLEAN,
    halal BOOLEAN,
    spicy_level INT, -- 0-5
    
    -- Popularity
    times_ordered INT DEFAULT 0,
    item_rating DECIMAL(3,2),
    
    -- TBN tracking
    collected_by_bot VARCHAR(255) REFERENCES tbn_bots(bot_id),
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- CUSTOMER REVIEWS (TBN-Verified)
-- ============================================================================

CREATE TABLE restaurant_reviews (
    review_id SERIAL PRIMARY KEY,
    restaurant_id INT REFERENCES restaurants(restaurant_id),
    
    -- Ratings (1-5 stars)
    overall_rating INT CHECK (overall_rating BETWEEN 1 AND 5),
    food_quality INT CHECK (food_quality BETWEEN 1 AND 5),
    service INT CHECK (service BETWEEN 1 AND 5),
    value_for_money INT CHECK (value_for_money BETWEEN 1 AND 5),
    hygiene INT CHECK (hygiene BETWEEN 1 AND 5),
    
    -- Review content
    review_title VARCHAR(255),
    review_text TEXT,
    order_type VARCHAR(50), -- delivery, collection, dine-in
    
    -- Reviewer info
    reviewer_name VARCHAR(255),
    reviewer_verified BOOLEAN, -- Verified by TBN bot
    verified_purchase BOOLEAN, -- Actually ordered from here
    
    -- Photos
    photo_urls JSON,
    
    -- Response
    restaurant_response TEXT,
    response_date TIMESTAMP,
    
    -- Helpful votes
    helpful_count INT DEFAULT 0,
    not_helpful_count INT DEFAULT 0,
    
    -- TBN verification
    collected_by_bot VARCHAR(255) REFERENCES tbn_bots(bot_id),
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    verified_by_tbn BOOLEAN DEFAULT TRUE,
    tbn_trust_score DECIMAL(3,2) -- 0-100 (how trustworthy is this review)
);

-- ============================================================================
-- FOOD HYGIENE RATINGS (FSA Data)
-- ============================================================================

CREATE TABLE food_hygiene_inspections (
    inspection_id SERIAL PRIMARY KEY,
    restaurant_id INT REFERENCES restaurants(restaurant_id),
    inspection_date DATE,
    rating INT CHECK (rating BETWEEN 0 AND 5),
    
    -- Inspection details
    hygiene_score INT,
    structural_score INT,
    confidence_in_management_score INT,
    
    -- Issues found
    issues_found TEXT,
    corrective_actions TEXT,
    
    -- TBN tracking
    collected_by_bot VARCHAR(255) REFERENCES tbn_bots(bot_id),
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- POPULAR DISHES
-- ============================================================================

CREATE TABLE popular_dishes (
    dish_id SERIAL PRIMARY KEY,
    cuisine_type VARCHAR(100),
    dish_name VARCHAR(255),
    description TEXT,
    typical_price_range VARCHAR(50),
    
    -- Popularity metrics
    search_volume INT,
    order_frequency INT,
    
    -- TBN tracking
    collected_by_bot VARCHAR(255) REFERENCES tbn_bots(bot_id),
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- DELIVERY AREAS
-- ============================================================================

CREATE TABLE delivery_areas (
    area_id SERIAL PRIMARY KEY,
    restaurant_id INT REFERENCES restaurants(restaurant_id),
    postcode_prefix VARCHAR(10),
    delivery_time_minutes INT,
    delivery_fee DECIMAL(5,2),
    minimum_order DECIMAL(5,2),
    
    -- TBN tracking
    collected_by_bot VARCHAR(255) REFERENCES tbn_bots(bot_id),
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- SPECIAL OFFERS
-- ============================================================================

CREATE TABLE special_offers (
    offer_id SERIAL PRIMARY KEY,
    restaurant_id INT REFERENCES restaurants(restaurant_id),
    offer_title VARCHAR(255),
    offer_description TEXT,
    discount_type VARCHAR(50), -- percentage, fixed_amount, free_item
    discount_value DECIMAL(6,2),
    
    -- Validity
    valid_from DATE,
    valid_until DATE,
    days_valid JSON, -- ["monday", "tuesday", ...]
    minimum_order DECIMAL(6,2),
    
    -- Usage
    times_used INT DEFAULT 0,
    
    -- TBN tracking
    collected_by_bot VARCHAR(255) REFERENCES tbn_bots(bot_id),
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- Indexes for Performance
-- ============================================================================

CREATE INDEX idx_restaurants_cuisine ON restaurants(cuisine_type);
CREATE INDEX idx_restaurants_city ON restaurants(city);
CREATE INDEX idx_restaurants_postcode ON restaurants(postcode);
CREATE INDEX idx_restaurants_rating ON restaurants(overall_rating DESC);
CREATE INDEX idx_restaurants_hygiene ON restaurants(food_hygiene_rating DESC);
CREATE INDEX idx_reviews_restaurant ON restaurant_reviews(restaurant_id);
CREATE INDEX idx_reviews_rating ON restaurant_reviews(overall_rating DESC);
CREATE INDEX idx_menu_restaurant ON menu_items(restaurant_id);
CREATE INDEX idx_menu_category ON menu_items(category);

-- Full-text search
CREATE INDEX idx_restaurants_search ON restaurants USING gin(search_vector);

-- ============================================================================
-- Views for Easy Querying
-- ============================================================================

-- View: Top-rated kebab shops
CREATE VIEW top_kebab_shops AS
SELECT 
    restaurant_name,
    address,
    city,
    postcode,
    overall_rating,
    food_hygiene_rating,
    total_reviews,
    average_price_range,
    phone
FROM restaurants
WHERE cuisine_type = 'kebab' OR cuisine_type = 'turkish'
AND overall_rating >= 4.0
ORDER BY overall_rating DESC, total_reviews DESC
LIMIT 50;

-- View: Top-rated Indian restaurants
CREATE VIEW top_indian_restaurants AS
SELECT 
    restaurant_name,
    address,
    city,
    postcode,
    overall_rating,
    food_hygiene_rating,
    total_reviews,
    average_price_range,
    phone
FROM restaurants
WHERE cuisine_type = 'indian'
AND overall_rating >= 4.0
ORDER BY overall_rating DESC, total_reviews DESC
LIMIT 50;

-- View: Top-rated Chinese takeaways
CREATE VIEW top_chinese_takeaways AS
SELECT 
    restaurant_name,
    address,
    city,
    postcode,
    overall_rating,
    food_hygiene_rating,
    total_reviews,
    average_price_range,
    phone
FROM restaurants
WHERE cuisine_type = 'chinese'
AND overall_rating >= 4.0
ORDER BY overall_rating DESC, total_reviews DESC
LIMIT 50;

-- View: Top-rated pizza places
CREATE VIEW top_pizza_places AS
SELECT 
    restaurant_name,
    address,
    city,
    postcode,
    overall_rating,
    food_hygiene_rating,
    total_reviews,
    average_price_range,
    phone
FROM restaurants
WHERE cuisine_type = 'pizza' OR cuisine_type = 'italian'
AND overall_rating >= 4.0
ORDER BY overall_rating DESC, total_reviews DESC
LIMIT 50;

-- View: Restaurants by city with ratings
CREATE VIEW restaurants_by_city AS
SELECT 
    city,
    cuisine_type,
    COUNT(*) as restaurant_count,
    ROUND(AVG(overall_rating), 2) as avg_rating,
    ROUND(AVG(food_hygiene_rating), 1) as avg_hygiene_rating
FROM restaurants
GROUP BY city, cuisine_type
ORDER BY city, restaurant_count DESC;

-- View: Best value restaurants
CREATE VIEW best_value_restaurants AS
SELECT 
    restaurant_name,
    cuisine_type,
    city,
    overall_rating,
    value_rating,
    average_price_range,
    total_reviews
FROM restaurants
WHERE value_rating >= 4.5
AND overall_rating >= 4.0
ORDER BY value_rating DESC, overall_rating DESC
LIMIT 100;

-- View: Highest hygiene ratings
CREATE VIEW cleanest_restaurants AS
SELECT 
    restaurant_name,
    cuisine_type,
    address,
    city,
    food_hygiene_rating,
    overall_rating,
    total_reviews
FROM restaurants
WHERE food_hygiene_rating = 5
ORDER BY overall_rating DESC, total_reviews DESC;

-- View: TBN-verified reviews summary
CREATE VIEW verified_reviews_summary AS
SELECT 
    r.restaurant_name,
    r.cuisine_type,
    COUNT(rv.review_id) as total_verified_reviews,
    ROUND(AVG(rv.overall_rating), 2) as avg_verified_rating,
    ROUND(AVG(rv.tbn_trust_score), 2) as avg_trust_score
FROM restaurants r
JOIN restaurant_reviews rv ON r.restaurant_id = rv.restaurant_id
WHERE rv.verified_by_tbn = TRUE
GROUP BY r.restaurant_id, r.restaurant_name, r.cuisine_type
HAVING COUNT(rv.review_id) >= 5
ORDER BY avg_verified_rating DESC, total_verified_reviews DESC;

-- Update search vectors
CREATE OR REPLACE FUNCTION update_restaurant_search_vector() RETURNS trigger AS $$
BEGIN
    NEW.search_vector := 
        to_tsvector('english', coalesce(NEW.restaurant_name,'') || ' ' || 
                               coalesce(NEW.cuisine_type,'') || ' ' || 
                               coalesce(NEW.city,'') || ' ' ||
                               coalesce(NEW.postcode,''));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER restaurant_search_vector_update 
    BEFORE INSERT OR UPDATE ON restaurants
    FOR EACH ROW EXECUTE FUNCTION update_restaurant_search_vector();
