-- Sample Data for Hardin Data Network
-- This gives people something to see immediately

-- ============================================================================
-- Sample TBN Bots
-- ============================================================================

INSERT INTO tbn_bots (bot_id, bot_name, bot_type, certification_level, capabilities, status, last_active) VALUES
('tbn-bot-uk-companies-001', 'UK Companies Collector', 'DATA_COLLECTOR', 'COMMUNITY', '["companies_house", "financial_data", "officer_data"]', 'active', NOW()),
('tbn-bot-news-aggregator-001', 'Business News Aggregator', 'NEWS_COLLECTOR', 'COMMUNITY', '["news_scraping", "sentiment_analysis", "summarization"]', 'active', NOW()),
('tbn-bot-ai-tools-001', 'AI Tools Directory Bot', 'DATA_COLLECTOR', 'STANDARD', '["web_scraping", "api_integration", "data_validation"]', 'active', NOW());

-- ============================================================================
-- Sample UK Companies (Real examples)
-- ============================================================================

INSERT INTO uk_companies (company_number, company_name, company_status, company_type, registered_address, incorporation_date, industry_code, industry_description, collected_by_bot, tbn_verified) VALUES
('12345678', 'Hardin Enterprises Ltd', 'Active', 'Private Limited Company', '123 Tech Street, London, EC1A 1BB', '2024-01-15', '62020', 'Information technology consultancy activities', 'tbn-bot-uk-companies-001', TRUE),
('87654321', 'TechStart Innovation Ltd', 'Active', 'Private Limited Company', '456 Innovation Way, Manchester, M1 1AA', '2023-06-20', '62012', 'Business and domestic software development', 'tbn-bot-uk-companies-001', TRUE),
('11223344', 'London AI Solutions Ltd', 'Active', 'Private Limited Company', '789 AI Avenue, London, W1A 1AA', '2022-03-10', '62020', 'Artificial intelligence consultancy', 'tbn-bot-uk-companies-001', TRUE),
('44332211', 'DataFlow Analytics Ltd', 'Active', 'Private Limited Company', '321 Data Lane, Birmingham, B1 1BB', '2023-09-05', '62020', 'Data processing and analytics', 'tbn-bot-uk-companies-001', TRUE),
('55667788', 'CloudTech Services Ltd', 'Active', 'Private Limited Company', '654 Cloud Street, Edinburgh, EH1 1AA', '2024-02-28', '63110', 'Cloud computing services', 'tbn-bot-uk-companies-001', TRUE);

-- ============================================================================
-- Sample Business News
-- ============================================================================

INSERT INTO business_news (headline, summary, source, source_url, published_date, category, sentiment, collected_by_bot) VALUES
('UK Tech Sector Sees Record Investment in Q1 2026', 'British technology companies raised £3.2 billion in the first quarter of 2026, marking a 45% increase from the previous year. AI and fintech sectors led the growth.', 'Tech UK News', 'https://example.com/news/1', NOW() - INTERVAL '2 days', 'Investment', 'positive', 'tbn-bot-news-aggregator-001'),

('London Emerges as Leading AI Hub in Europe', 'London has overtaken Paris and Berlin to become Europe''s top destination for AI startups, with over 500 AI companies now based in the capital.', 'Business Weekly', 'https://example.com/news/2', NOW() - INTERVAL '1 day', 'Technology', 'positive', 'tbn-bot-news-aggregator-001'),

('New Regulations for AI Companies Announced', 'The UK government has introduced new guidelines for AI companies, focusing on transparency and ethical AI development. Companies have 6 months to comply.', 'Gov Tech Today', 'https://example.com/news/3', NOW() - INTERVAL '3 hours', 'Regulation', 'neutral', 'tbn-bot-news-aggregator-001'),

('Startup Funding Slows in Traditional Sectors', 'While tech sees growth, traditional retail and hospitality sectors experienced a 20% decline in startup funding during Q1 2026.', 'Financial Times UK', 'https://example.com/news/4', NOW() - INTERVAL '5 hours', 'Finance', 'negative', 'tbn-bot-news-aggregator-001'),

('Remote Work Trend Continues to Shape UK Business', 'Survey shows 65% of UK tech companies now offer fully remote or hybrid work options, reshaping office space demand in major cities.', 'Work Culture Magazine', 'https://example.com/news/5', NOW() - INTERVAL '1 day', 'Workplace', 'neutral', 'tbn-bot-news-aggregator-001');

-- ============================================================================
-- Sample AI Tools
-- ============================================================================

INSERT INTO ai_tools (tool_name, tool_description, tool_url, category, pricing_model, price_range, features, integrations, collected_by_bot) VALUES
('ChatGPT', 'Advanced conversational AI by OpenAI for natural language processing and generation', 'https://chat.openai.com', 'Conversational AI', 'Freemium', '$0-$20/month', '["text_generation", "code_assistance", "translation", "summarization"]', '["api", "plugins", "mobile_app"]', 'tbn-bot-ai-tools-001'),

('Midjourney', 'AI-powered image generation tool for creating artwork and designs', 'https://midjourney.com', 'Image Generation', 'Subscription', '$10-$60/month', '["image_generation", "style_transfer", "upscaling"]', '["discord", "api"]', 'tbn-bot-ai-tools-001'),

('GitHub Copilot', 'AI pair programmer that helps write code faster', 'https://github.com/features/copilot', 'Code Assistant', 'Subscription', '$10-$19/month', '["code_completion", "code_generation", "documentation"]', '["vscode", "jetbrains", "neovim"]', 'tbn-bot-ai-tools-001'),

('Jasper AI', 'AI writing assistant for marketing and content creation', 'https://jasper.ai', 'Content Writing', 'Subscription', '$39-$125/month', '["content_generation", "seo_optimization", "templates"]', '["chrome_extension", "api", "wordpress"]', 'tbn-bot-ai-tools-001'),

('Notion AI', 'AI-powered workspace for notes, docs, and project management', 'https://notion.so/product/ai', 'Productivity', 'Add-on', '$10/month', '["writing_assistance", "summarization", "translation"]', '["notion_workspace", "api"]', 'tbn-bot-ai-tools-001');

-- ============================================================================
-- Sample Market Trends
-- ============================================================================

INSERT INTO market_trends (industry, trend_name, trend_description, trend_score, time_period, collected_by_bot) VALUES
('Technology', 'AI Adoption Acceleration', 'Rapid increase in AI tool adoption across UK businesses, particularly in automation and customer service', 85.5, 'Q1 2026', 'tbn-bot-news-aggregator-001'),
('Finance', 'Fintech Innovation', 'Growth in digital banking and payment solutions, driven by consumer demand for seamless transactions', 78.2, 'Q1 2026', 'tbn-bot-news-aggregator-001'),
('Healthcare', 'Telemedicine Expansion', 'Continued growth in remote healthcare services and AI-assisted diagnostics', 72.8, 'Q1 2026', 'tbn-bot-news-aggregator-001'),
('Retail', 'E-commerce Consolidation', 'Major retailers strengthening online presence while smaller players face challenges', 65.3, 'Q1 2026', 'tbn-bot-news-aggregator-001'),
('Energy', 'Green Tech Investment', 'Significant increase in renewable energy and sustainability technology funding', 81.7, 'Q1 2026', 'tbn-bot-news-aggregator-001');

-- ============================================================================
-- Sample Subscribers
-- ============================================================================

INSERT INTO subscribers (company_name, contact_email, subscription_tier, api_key, monthly_api_calls, api_call_limit, status) VALUES
('Demo Company Ltd', 'demo@example.com', 'free', 'demo_key_12345', 150, 1000, 'active'),
('TechCorp Solutions', 'api@techcorp.com', 'pro', 'pro_key_67890', 5200, 10000, 'active'),
('Enterprise Analytics Inc', 'data@enterprise.com', 'enterprise', 'ent_key_11111', 45000, 100000, 'active');

-- ============================================================================
-- Sample Data Quality Checks
-- ============================================================================

INSERT INTO data_quality_checks (table_name, record_id, check_type, check_result, check_details, checked_by_bot) VALUES
('uk_companies', 1, 'completeness', 'pass', '{"fields_checked": 10, "fields_complete": 10, "completeness_score": 100}', 'tbn-bot-uk-companies-001'),
('uk_companies', 2, 'accuracy', 'pass', '{"verified_against": "companies_house_api", "match_score": 98}', 'tbn-bot-uk-companies-001'),
('business_news', 1, 'freshness', 'pass', '{"published_date": "2026-05-05", "collected_date": "2026-05-05", "freshness_hours": 2}', 'tbn-bot-news-aggregator-001'),
('ai_tools', 1, 'accuracy', 'pass', '{"verified_against": "official_website", "last_verified": "2026-05-06"}', 'tbn-bot-ai-tools-001');

-- ============================================================================
-- Update search vectors for full-text search
-- ============================================================================

UPDATE uk_companies SET search_vector = 
    to_tsvector('english', coalesce(company_name,'') || ' ' || coalesce(industry_description,''));

UPDATE business_news SET search_vector = 
    to_tsvector('english', coalesce(headline,'') || ' ' || coalesce(summary,''));

UPDATE ai_tools SET search_vector = 
    to_tsvector('english', coalesce(tool_name,'') || ' ' || coalesce(tool_description,''));
