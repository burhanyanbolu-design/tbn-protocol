#!/bin/bash
# Updated stats script with all new tables

sudo -u postgres psql -d hardin_data_network << 'EOF'

-- Display all data counts by type
SELECT 
    'Retail' as type,
    COUNT(*) as count
FROM retail_shops
UNION ALL
SELECT 
    'Restaurants',
    COUNT(*)
FROM restaurants
UNION ALL
SELECT 
    'Recipes',
    COUNT(*)
FROM recipes
UNION ALL
SELECT 
    'Lottery',
    COUNT(*)
FROM lottery_draws
UNION ALL
SELECT 
    'Football',
    COUNT(*)
FROM football_matches
UNION ALL
SELECT 
    'Horse Racing',
    COUNT(*)
FROM horse_racing
UNION ALL
SELECT 
    'Cricket',
    COUNT(*)
FROM cricket_matches
UNION ALL
SELECT 
    'Rugby',
    COUNT(*)
FROM rugby_matches
UNION ALL
SELECT 
    'Tennis',
    COUNT(*)
FROM tennis_matches
UNION ALL
SELECT 
    'Golf',
    COUNT(*)
FROM golf_tournaments
UNION ALL
SELECT 
    'F1',
    COUNT(*)
FROM f1_races
UNION ALL
SELECT 
    'Boxing',
    COUNT(*)
FROM boxing_matches
UNION ALL
SELECT 
    'Darts',
    COUNT(*)
FROM darts_tournaments
UNION ALL
SELECT 
    'Snooker',
    COUNT(*)
FROM snooker_tournaments
UNION ALL
SELECT 
    'Companies',
    COUNT(*)
FROM companies
UNION ALL
SELECT 
    'Weather',
    COUNT(*)
FROM weather_data
UNION ALL
SELECT 
    'News',
    COUNT(*)
FROM news_articles
UNION ALL
SELECT 
    'Car Manufacturing',
    COUNT(*)
FROM uk_car_manufacturing
UNION ALL
SELECT 
    'Car Sales',
    COUNT(*)
FROM uk_car_sales
UNION ALL
SELECT 
    'Car Imports',
    COUNT(*)
FROM uk_car_imports
UNION ALL
SELECT 
    'Car Exports',
    COUNT(*)
FROM uk_car_exports
UNION ALL
SELECT 
    'Gov Statistics',
    COUNT(*)
FROM uk_government_stats
UNION ALL
SELECT 
    'Currency Rates',
    COUNT(*)
FROM currency_rates
UNION ALL
SELECT 
    'Commodities',
    COUNT(*)
FROM commodities
UNION ALL
SELECT 
    'Trade Data',
    COUNT(*)
FROM uk_trade
UNION ALL
SELECT 
    'Books',
    COUNT(*)
FROM books
UNION ALL
SELECT 
    'Geography',
    COUNT(*)
FROM uk_geography
ORDER BY type;

-- Total count
SELECT 
    '===================' as separator;

SELECT 
    'TOTAL DATA POINTS' as metric,
    (
        (SELECT COUNT(*) FROM retail_shops) +
        (SELECT COUNT(*) FROM restaurants) +
        (SELECT COUNT(*) FROM recipes) +
        (SELECT COUNT(*) FROM lottery_draws) +
        (SELECT COUNT(*) FROM football_matches) +
        (SELECT COUNT(*) FROM horse_racing) +
        (SELECT COUNT(*) FROM cricket_matches) +
        (SELECT COUNT(*) FROM rugby_matches) +
        (SELECT COUNT(*) FROM tennis_matches) +
        (SELECT COUNT(*) FROM golf_tournaments) +
        (SELECT COUNT(*) FROM f1_races) +
        (SELECT COUNT(*) FROM boxing_matches) +
        (SELECT COUNT(*) FROM darts_tournaments) +
        (SELECT COUNT(*) FROM snooker_tournaments) +
        (SELECT COUNT(*) FROM companies) +
        (SELECT COUNT(*) FROM weather_data) +
        (SELECT COUNT(*) FROM news_articles) +
        (SELECT COUNT(*) FROM uk_car_manufacturing) +
        (SELECT COUNT(*) FROM uk_car_sales) +
        (SELECT COUNT(*) FROM uk_car_imports) +
        (SELECT COUNT(*) FROM uk_car_exports) +
        (SELECT COUNT(*) FROM uk_government_stats) +
        (SELECT COUNT(*) FROM currency_rates) +
        (SELECT COUNT(*) FROM commodities) +
        (SELECT COUNT(*) FROM uk_trade) +
        (SELECT COUNT(*) FROM books) +
        (SELECT COUNT(*) FROM uk_geography)
    ) as count;

-- Progress toward goals
SELECT 
    '===================' as separator;

SELECT 
    'Week 1 Goal: 1,000 (ACHIEVED!)' as progress;
SELECT 
    'Month 1 Goal: 50,000' as progress;
SELECT 
    'Current Progress: ' || 
    ROUND(
        (
            (SELECT COUNT(*) FROM retail_shops) +
            (SELECT COUNT(*) FROM restaurants) +
            (SELECT COUNT(*) FROM recipes) +
            (SELECT COUNT(*) FROM lottery_draws) +
            (SELECT COUNT(*) FROM football_matches) +
            (SELECT COUNT(*) FROM horse_racing) +
            (SELECT COUNT(*) FROM cricket_matches) +
            (SELECT COUNT(*) FROM rugby_matches) +
            (SELECT COUNT(*) FROM tennis_matches) +
            (SELECT COUNT(*) FROM golf_tournaments) +
            (SELECT COUNT(*) FROM f1_races) +
            (SELECT COUNT(*) FROM boxing_matches) +
            (SELECT COUNT(*) FROM darts_tournaments) +
            (SELECT COUNT(*) FROM snooker_tournaments) +
            (SELECT COUNT(*) FROM companies) +
            (SELECT COUNT(*) FROM weather_data) +
            (SELECT COUNT(*) FROM news_articles) +
            (SELECT COUNT(*) FROM uk_car_manufacturing) +
            (SELECT COUNT(*) FROM uk_car_sales) +
            (SELECT COUNT(*) FROM uk_car_imports) +
            (SELECT COUNT(*) FROM uk_car_exports) +
            (SELECT COUNT(*) FROM uk_government_stats) +
            (SELECT COUNT(*) FROM currency_rates) +
            (SELECT COUNT(*) FROM commodities) +
            (SELECT COUNT(*) FROM uk_trade) +
            (SELECT COUNT(*) FROM books) +
            (SELECT COUNT(*) FROM uk_geography)
        )::DECIMAL / 50000 * 100, 1
    ) || '%' as progress;

EOF
