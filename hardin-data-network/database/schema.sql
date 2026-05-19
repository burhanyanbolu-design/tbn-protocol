-- Hardin Data Network Database Schema
-- A marketplace of data collected by TBN-certified bots

-- ============================================================================
-- TBN Integration Tables
-- ============================================================================

CREATE TABLE tbn_bots (
    bot_id VARCHAR(255) PRIMARY KEY,
    bot_name VARCHAR(255) NOT NULL,
    bot_type VARCHAR(100),
    certification_level VARCHAR(50),
    capabilities JSON,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP
);

CREATE TABLE tbn_verifications (
    verification_id SERIAL PRIMARY KEY,
    bot_id VARCHAR(255) REFERENCES tbn_bots(bot_id),
    verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    verification_status BOOLEAN,
    tbn_response JSON
);

-- ============================================================================
-- UK Business Data Tables
-- ============================================================================

CREATE TABLE uk_companies (
    company_id SERIAL PRIMARY KEY,
    company_number VARCHAR(50) UNIQUE,
    company_name VARCHAR(500),
    company_status VARCHAR(100),
    company_type VARCHAR(100),
    registered_address TEXT,
    incorporation_date DATE,
    industry_code VARCHAR(50),
    industry_description TEXT,
    
    -- TBN tracking
    collected_by_bot VARCHAR(255) REFERENCES tbn_bots(bot_id),
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP,
    tbn_verified BOOLEAN DEFAULT TRUE,
    
    -- Search optimization
    search_vector tsvector
);

CREATE TABLE company_officers (
    officer_id SERIAL PRIMARY KEY,
    company_id INT REFERENCES uk_companies(company_id),
    officer_name VARCHAR(500),
    officer_role VARCHAR(100),
    appointed_date DATE,
    resigned_date DATE,
    
    -- TBN tracking
    collected_by_bot VARCHAR(255) REFERENCES tbn_bots(bot_id),
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE company_financials (
    financial_id SERIAL PRIMARY KEY,
    company_id INT REFERENCES uk_companies(company_id),
    financial_year INT,
    turnover DECIMAL(15,2),
    profit_loss DECIMAL(15,2),
    assets DECIMAL(15,2),
    liabilities DECIMAL(15,2),
    
    -- TBN tracking
    collected_by_bot VARCHAR(255) REFERENCES tbn_bots(bot_id),
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- News & Market Intelligence
-- ============================================================================

CREATE TABLE business_news (
    news_id SERIAL PRIMARY KEY,
    headline VARCHAR(1000),
    summary TEXT,
    full_content TEXT,
    source VARCHAR(255),
    source_url VARCHAR(1000),
    published_date TIMESTAMP,
    category VARCHAR(100),
    sentiment VARCHAR(50), -- positive, negative, neutral
    
    -- TBN tracking
    collected_by_bot VARCHAR(255) REFERENCES tbn_bots(bot_id),
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Search optimization
    search_vector tsvector
);

CREATE TABLE market_trends (
    trend_id SERIAL PRIMARY KEY,
    industry VARCHAR(255),
    trend_name VARCHAR(500),
    trend_description TEXT,
    trend_score DECIMAL(5,2), -- 0-100
    time_period VARCHAR(50),
    
    -- TBN tracking
    collected_by_bot VARCHAR(255) REFERENCES tbn_bots(bot_id),
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- AI Tools Directory (Alternative dataset)
-- ============================================================================

CREATE TABLE ai_tools (
    tool_id SERIAL PRIMARY KEY,
    tool_name VARCHAR(255),
    tool_description TEXT,
    tool_url VARCHAR(1000),
    category VARCHAR(100),
    pricing_model VARCHAR(100),
    price_range VARCHAR(100),
    features JSON,
    integrations JSON,
    
    -- TBN tracking
    collected_by_bot VARCHAR(255) REFERENCES tbn_bots(bot_id),
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP,
    
    -- Search optimization
    search_vector tsvector
);

CREATE TABLE tool_reviews (
    review_id SERIAL PRIMARY KEY,
    tool_id INT REFERENCES ai_tools(tool_id),
    rating DECIMAL(3,2),
    review_text TEXT,
    reviewer_name VARCHAR(255),
    review_date DATE,
    
    -- TBN tracking
    collected_by_bot VARCHAR(255) REFERENCES tbn_bots(bot_id),
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- Subscribers & Access Control
-- ============================================================================

CREATE TABLE subscribers (
    subscriber_id SERIAL PRIMARY KEY,
    company_name VARCHAR(255),
    contact_email VARCHAR(255) UNIQUE,
    subscription_tier VARCHAR(50), -- free, pro, enterprise
    api_key VARCHAR(255) UNIQUE,
    tbn_bot_id VARCHAR(255), -- if they have a TBN-certified bot
    
    -- Limits
    monthly_api_calls INT DEFAULT 0,
    api_call_limit INT DEFAULT 1000,
    
    -- Status
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

CREATE TABLE api_access_logs (
    log_id SERIAL PRIMARY KEY,
    subscriber_id INT REFERENCES subscribers(subscriber_id),
    endpoint VARCHAR(255),
    query_params JSON,
    response_status INT,
    tbn_verified BOOLEAN,
    accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- Data Quality & Verification
-- ============================================================================

CREATE TABLE data_quality_checks (
    check_id SERIAL PRIMARY KEY,
    table_name VARCHAR(100),
    record_id INT,
    check_type VARCHAR(100), -- accuracy, completeness, freshness
    check_result VARCHAR(50), -- pass, fail, warning
    check_details JSON,
    checked_by_bot VARCHAR(255) REFERENCES tbn_bots(bot_id),
    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- Indexes for Performance
-- ============================================================================

CREATE INDEX idx_companies_name ON uk_companies(company_name);
CREATE INDEX idx_companies_number ON uk_companies(company_number);
CREATE INDEX idx_companies_bot ON uk_companies(collected_by_bot);
CREATE INDEX idx_news_date ON business_news(published_date DESC);
CREATE INDEX idx_news_category ON business_news(category);
CREATE INDEX idx_tools_category ON ai_tools(category);
CREATE INDEX idx_subscribers_email ON subscribers(contact_email);
CREATE INDEX idx_access_logs_subscriber ON api_access_logs(subscriber_id);

-- Full-text search indexes
CREATE INDEX idx_companies_search ON uk_companies USING gin(search_vector);
CREATE INDEX idx_news_search ON business_news USING gin(search_vector);
CREATE INDEX idx_tools_search ON ai_tools USING gin(search_vector);

-- ============================================================================
-- Views for Easy Querying
-- ============================================================================

-- View: Recent data with TBN verification
CREATE VIEW recent_verified_data AS
SELECT 
    'company' as data_type,
    company_id as record_id,
    company_name as name,
    collected_by_bot,
    collected_at,
    tbn_verified
FROM uk_companies
WHERE collected_at > NOW() - INTERVAL '7 days'
UNION ALL
SELECT 
    'news' as data_type,
    news_id as record_id,
    headline as name,
    collected_by_bot,
    collected_at,
    TRUE as tbn_verified
FROM business_news
WHERE collected_at > NOW() - INTERVAL '7 days'
ORDER BY collected_at DESC;

-- View: Bot activity summary
CREATE VIEW bot_activity_summary AS
SELECT 
    b.bot_id,
    b.bot_name,
    b.certification_level,
    COUNT(DISTINCT c.company_id) as companies_collected,
    COUNT(DISTINCT n.news_id) as news_collected,
    MAX(b.last_active) as last_active
FROM tbn_bots b
LEFT JOIN uk_companies c ON b.bot_id = c.collected_by_bot
LEFT JOIN business_news n ON b.bot_id = n.collected_by_bot
GROUP BY b.bot_id, b.bot_name, b.certification_level;

-- View: Subscriber usage
CREATE VIEW subscriber_usage AS
SELECT 
    s.subscriber_id,
    s.company_name,
    s.subscription_tier,
    s.monthly_api_calls,
    s.api_call_limit,
    ROUND((s.monthly_api_calls::DECIMAL / s.api_call_limit) * 100, 2) as usage_percentage,
    COUNT(l.log_id) as total_calls
FROM subscribers s
LEFT JOIN api_access_logs l ON s.subscriber_id = l.subscriber_id
GROUP BY s.subscriber_id, s.company_name, s.subscription_tier, s.monthly_api_calls, s.api_call_limit;
