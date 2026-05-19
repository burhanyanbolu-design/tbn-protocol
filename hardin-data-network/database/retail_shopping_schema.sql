-- UK Retail & Shopping Database
-- Ladies Clothing, Confectionery, Bakeries, and more
-- Collected by TBN-certified bots

-- ============================================================================
-- RETAIL BUSINESSES (All Types)
-- ============================================================================

CREATE TABLE retail_businesses (
    business_id SERIAL PRIMARY KEY,
    business_name VARCHAR(255),
    business_type VARCHAR(100), -- clothing, confectionery, bakery, etc.
    business_category VARCHAR(100), -- ladies_fashion, mens_fashion, sweets, chocolate, artisan_bakery, etc.
    
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
    social_media JSON, -- {"instagram": "@shop", "facebook": "page", ...}
    
    -- Business info
    company_number VARCHAR(50),
    established_year INT,
    independent_business BOOLEAN, -- vs chain store
    
    -- Opening hours
    opening_hours JSON,
    online_shopping BOOLEAN,
    click_and_collect BOOLEAN,
    home_delivery BOOLEAN,
    
    -- Pricing
    price_range VARCHAR(20), -- £, ££, £££, ££££
    accepts_cards BOOLEAN,
    accepts_cash BOOLEAN,
    
    -- Ratings
    overall_rating DECIMAL(3,2),
    quality_rating DECIMAL(3,2),
    service_rating DECIMAL(3,2),
    value_rating DECIMAL(3,2),
    atmosphere_rating DECIMAL(3,2),
    total_reviews INT DEFAULT 0,
    
    -- Special features
    features JSON, -- ["wheelchair_accessible", "parking", "fitting_rooms", ...]
    
    -- TBN tracking
    collected_by_bot VARCHAR(255) REFERENCES tbn_bots(bot_id),
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP,
    verified_by_tbn BOOLEAN DEFAULT TRUE,
    
    -- Search
    search_vector tsvector
);

-- ============================================================================
-- LADIES CLOTHING SHOPS
-- ============================================================================

CREATE TABLE ladies_clothing_shops (
    shop_id SERIAL PRIMARY KEY,
    business_id INT REFERENCES retail_businesses(business_id),
    
    -- Shop specialization
    style_focus VARCHAR(100), -- casual, formal, evening_wear, modest, plus_size, etc.
    age_range VARCHAR(50), -- teens, 20s-30s, 40s+, all_ages
    
    -- Brands stocked
    brands_available JSON, -- ["Zara", "H&M", "Next", ...]
    designer_brands BOOLEAN,
    own_brand BOOLEAN,
    
    -- Size range
    size_range_start VARCHAR(10), -- UK 6, 8, 10...
    size_range_end VARCHAR(10), -- UK 24, 26...
    plus_size_available BOOLEAN,
    petite_range BOOLEAN,
    tall_range BOOLEAN,
    
    -- Services
    personal_styling BOOLEAN,
    alterations_service BOOLEAN,
    bridal_wear BOOLEAN,
    occasion_wear BOOLEAN,
    
    -- Popular items
    popular_categories JSON, -- ["dresses", "tops", "jeans", ...]
    
    -- TBN tracking
    collected_by_bot VARCHAR(255) REFERENCES tbn_bots(bot_id),
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- CONFECTIONERY SHOPS (Sweets & Chocolate)
-- ============================================================================

CREATE TABLE confectionery_shops (
    shop_id SERIAL PRIMARY KEY,
    business_id INT REFERENCES retail_businesses(business_id),
    
    -- Shop type
    shop_specialization VARCHAR(100), -- traditional_sweets, luxury_chocolate, pick_n_mix, etc.
    
    -- Products
    handmade_chocolates BOOLEAN,
    imported_sweets BOOLEAN,
    sugar_free_options BOOLEAN,
    vegan_options BOOLEAN,
    halal_certified BOOLEAN,
    
    -- Popular items
    signature_products JSON, -- ["Turkish Delight", "Handmade Truffles", ...]
    gift_boxes_available BOOLEAN,
    custom_orders BOOLEAN,
    
    -- Services
    gift_wrapping BOOLEAN,
    corporate_gifts BOOLEAN,
    wedding_favours BOOLEAN,
    
    -- TBN tracking
    collected_by_bot VARCHAR(255) REFERENCES tbn_bots(bot_id),
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- BAKERIES (Artisan & Traditional)
-- ============================================================================

CREATE TABLE bakeries (
    bakery_id SERIAL PRIMARY KEY,
    business_id INT REFERENCES retail_businesses(business_id),
    
    -- Bakery type
    bakery_type VARCHAR(100), -- artisan, traditional, french, turkish, etc.
    
    -- Products
    fresh_bread BOOLEAN,
    pastries BOOLEAN,
    cakes BOOLEAN,
    turkish_pastries BOOLEAN, -- baklava, borek, etc.
    french_pastries BOOLEAN, -- croissants, pain au chocolat, etc.
    
    -- Dietary options
    gluten_free BOOLEAN,
    vegan_options BOOLEAN,
    sugar_free_options BOOLEAN,
    
    -- Services
    custom_cakes BOOLEAN,
    wedding_cakes BOOLEAN,
    birthday_cakes BOOLEAN,
    wholesale_available BOOLEAN,
    
    -- Baking schedule
    baking_times JSON, -- {"bread": "6am", "pastries": "7am", ...}
    fresh_daily BOOLEAN,
    
    -- Popular items
    signature_items JSON, -- ["Sourdough", "Croissants", "Baklava", ...]
    
    -- TBN tracking
    collected_by_bot VARCHAR(255) REFERENCES tbn_bots(bot_id),
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- PRODUCTS (For all retail types)
-- ============================================================================

CREATE TABLE retail_products (
    product_id SERIAL PRIMARY KEY,
    business_id INT REFERENCES retail_businesses(business_id),
    
    -- Product info
    product_name VARCHAR(255),
    product_description TEXT,
    category VARCHAR(100),
    subcategory VARCHAR(100),
    
    -- Pricing
    price DECIMAL(8,2),
    sale_price DECIMAL(8,2),
    on_sale BOOLEAN,
    
    -- Availability
    in_stock BOOLEAN,
    stock_level VARCHAR(50), -- low, medium, high
    
    -- Product details (varies by type)
    product_details JSON, -- sizes, colors, ingredients, etc.
    
    -- Images
    image_urls JSON,
    
    -- Ratings
    product_rating DECIMAL(3,2),
    times_purchased INT DEFAULT 0,
    
    -- TBN tracking
    collected_by_bot VARCHAR(255) REFERENCES tbn_bots(bot_id),
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP
);

-- ============================================================================
-- CUSTOMER REVIEWS (TBN-Verified)
-- ============================================================================

CREATE TABLE retail_reviews (
    review_id SERIAL PRIMARY KEY,
    business_id INT REFERENCES retail_businesses(business_id),
    product_id INT REFERENCES retail_products(product_id),
    
    -- Ratings
    overall_rating INT CHECK (overall_rating BETWEEN 1 AND 5),
    quality_rating INT CHECK (quality_rating BETWEEN 1 AND 5),
    service_rating INT CHECK (service_rating BETWEEN 1 AND 5),
    value_rating INT CHECK (value_rating BETWEEN 1 AND 5),
    
    -- Review content
    review_title VARCHAR(255),
    review_text TEXT,
    purchase_type VARCHAR(50), -- in_store, online, click_and_collect
    
    -- Reviewer
    reviewer_name VARCHAR(255),
    reviewer_verified BOOLEAN,
    verified_purchase BOOLEAN,
    
    -- Photos
    photo_urls JSON,
    
    -- Response
    business_response TEXT,
    response_date TIMESTAMP,
    
    -- Helpful votes
    helpful_count INT DEFAULT 0,
    
    -- TBN verification
    collected_by_bot VARCHAR(255) REFERENCES tbn_bots(bot_id),
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    verified_by_tbn BOOLEAN DEFAULT TRUE,
    tbn_trust_score DECIMAL(3,2)
);

-- ============================================================================
-- SPECIAL OFFERS & SALES
-- ============================================================================

CREATE TABLE retail_offers (
    offer_id SERIAL PRIMARY KEY,
    business_id INT REFERENCES retail_businesses(business_id),
    
    -- Offer details
    offer_title VARCHAR(255),
    offer_description TEXT,
    discount_type VARCHAR(50),
    discount_value DECIMAL(6,2),
    
    -- Validity
    valid_from DATE,
    valid_until DATE,
    
    -- Conditions
    minimum_spend DECIMAL(6,2),
    applies_to JSON, -- categories or products
    
    -- TBN tracking
    collected_by_bot VARCHAR(255) REFERENCES tbn_bots(bot_id),
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- Indexes
-- ============================================================================

CREATE INDEX idx_retail_type ON retail_businesses(business_type);
CREATE INDEX idx_retail_category ON retail_businesses(business_category);
CREATE INDEX idx_retail_city ON retail_businesses(city);
CREATE INDEX idx_retail_postcode ON retail_businesses(postcode);
CREATE INDEX idx_retail_rating ON retail_businesses(overall_rating DESC);
CREATE INDEX idx_products_business ON retail_products(business_id);
CREATE INDEX idx_products_category ON retail_products(category);
CREATE INDEX idx_reviews_business ON retail_reviews(business_id);

-- Full-text search
CREATE INDEX idx_retail_search ON retail_businesses USING gin(search_vector);

-- ============================================================================
-- Views
-- ============================================================================

-- Top ladies clothing shops
CREATE VIEW top_ladies_clothing_shops AS
SELECT 
    rb.business_name,
    rb.address,
    rb.city,
    rb.postcode,
    rb.overall_rating,
    rb.price_range,
    lcs.style_focus,
    lcs.brands_available,
    rb.phone,
    rb.website
FROM retail_businesses rb
JOIN ladies_clothing_shops lcs ON rb.business_id = lcs.business_id
WHERE rb.overall_rating >= 4.0
ORDER BY rb.overall_rating DESC, rb.total_reviews DESC
LIMIT 50;

-- Top confectionery shops
CREATE VIEW top_confectionery_shops AS
SELECT 
    rb.business_name,
    rb.address,
    rb.city,
    rb.postcode,
    rb.overall_rating,
    cs.shop_specialization,
    cs.handmade_chocolates,
    cs.signature_products,
    rb.phone,
    rb.website
FROM retail_businesses rb
JOIN confectionery_shops cs ON rb.business_id = cs.business_id
WHERE rb.overall_rating >= 4.0
ORDER BY rb.overall_rating DESC, rb.total_reviews DESC
LIMIT 50;

-- Top bakeries
CREATE VIEW top_bakeries AS
SELECT 
    rb.business_name,
    rb.address,
    rb.city,
    rb.postcode,
    rb.overall_rating,
    b.bakery_type,
    b.signature_items,
    b.fresh_daily,
    rb.phone,
    rb.website
FROM retail_businesses rb
JOIN bakeries b ON rb.business_id = b.bakery_id
WHERE rb.overall_rating >= 4.0
ORDER BY rb.overall_rating DESC, rb.total_reviews DESC
LIMIT 50;

-- Best value shops
CREATE VIEW best_value_shops AS
SELECT 
    business_name,
    business_type,
    business_category,
    city,
    overall_rating,
    value_rating,
    price_range,
    total_reviews
FROM retail_businesses
WHERE value_rating >= 4.5
AND overall_rating >= 4.0
ORDER BY value_rating DESC, overall_rating DESC
LIMIT 100;

-- Independent businesses
CREATE VIEW independent_businesses AS
SELECT 
    business_name,
    business_type,
    business_category,
    city,
    overall_rating,
    established_year,
    total_reviews
FROM retail_businesses
WHERE independent_business = TRUE
AND overall_rating >= 4.0
ORDER BY overall_rating DESC, total_reviews DESC;

-- Current offers
CREATE VIEW current_retail_offers AS
SELECT 
    rb.business_name,
    rb.business_type,
    rb.city,
    ro.offer_title,
    ro.offer_description,
    ro.discount_value,
    ro.valid_until
FROM retail_businesses rb
JOIN retail_offers ro ON rb.business_id = ro.business_id
WHERE ro.valid_from <= CURRENT_DATE
AND ro.valid_until >= CURRENT_DATE
ORDER BY ro.discount_value DESC;

-- Update search vectors
CREATE OR REPLACE FUNCTION update_retail_search_vector() RETURNS trigger AS $$
BEGIN
    NEW.search_vector := 
        to_tsvector('english', coalesce(NEW.business_name,'') || ' ' || 
                               coalesce(NEW.business_type,'') || ' ' || 
                               coalesce(NEW.business_category,'') || ' ' ||
                               coalesce(NEW.city,'') || ' ' ||
                               coalesce(NEW.postcode,''));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER retail_search_vector_update 
    BEFORE INSERT OR UPDATE ON retail_businesses
    FOR EACH ROW EXECUTE FUNCTION update_retail_search_vector();
