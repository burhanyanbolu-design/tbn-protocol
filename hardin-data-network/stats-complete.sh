#!/bin/bash

sudo -u postgres psql -d hardin_data_network -c "
-- Original Categories
SELECT 'Retail:' as type, COUNT(*) FROM retail_businesses
UNION ALL SELECT 'Restaurants:', COUNT(*) FROM restaurants
UNION ALL SELECT 'Recipes:', COUNT(*) FROM food_recipes
UNION ALL SELECT 'Lottery:', COUNT(*) FROM lottery_draws
UNION ALL SELECT 'Football:', COUNT(*) FROM football_matches
UNION ALL SELECT 'Horse Racing:', COUNT(*) FROM horse_races
UNION ALL SELECT 'Cricket:', COUNT(*) FROM cricket_matches
UNION ALL SELECT 'Rugby:', COUNT(*) FROM rugby_matches
UNION ALL SELECT 'Tennis:', COUNT(*) FROM tennis_matches
UNION ALL SELECT 'Golf:', COUNT(*) FROM golf_tournaments
UNION ALL SELECT 'F1:', COUNT(*) FROM f1_races
UNION ALL SELECT 'Boxing:', COUNT(*) FROM boxing_matches
UNION ALL SELECT 'Darts:', COUNT(*) FROM darts_tournaments
UNION ALL SELECT 'Snooker:', COUNT(*) FROM snooker_tournaments
UNION ALL SELECT 'Companies:', COUNT(*) FROM uk_companies
UNION ALL SELECT 'Weather:', COUNT(*) FROM weather_data
UNION ALL SELECT 'News:', COUNT(*) FROM news_articles

-- Master Plan Additions
UNION ALL SELECT 'Government Stats:', COUNT(*) FROM government_statistics
UNION ALL SELECT 'Currency Rates:', COUNT(*) FROM currency_rates
UNION ALL SELECT 'Commodities:', COUNT(*) FROM commodities
UNION ALL SELECT 'Trade Data:', COUNT(*) FROM trade_data
UNION ALL SELECT 'Books:', COUNT(*) FROM books
UNION ALL SELECT 'Geography:', COUNT(*) FROM geographic_data

-- Automotive Data
UNION ALL SELECT 'Car Sales:', COUNT(*) FROM uk_car_sales
UNION ALL SELECT 'Car Manufacturing:', COUNT(*) FROM uk_car_manufacturing
UNION ALL SELECT 'Car Imports:', COUNT(*) FROM uk_car_imports
UNION ALL SELECT 'Car Exports:', COUNT(*) FROM uk_car_exports

-- Grand Total
UNION ALL SELECT '==================', 0
UNION ALL SELECT 'TOTAL DATA POINTS:',
  (SELECT COUNT(*) FROM retail_businesses) +
  (SELECT COUNT(*) FROM restaurants) +
  (SELECT COUNT(*) FROM food_recipes) +
  (SELECT COUNT(*) FROM lottery_draws) +
  (SELECT COUNT(*) FROM football_matches) +
  (SELECT COUNT(*) FROM horse_races) +
  (SELECT COUNT(*) FROM cricket_matches) +
  (SELECT COUNT(*) FROM rugby_matches) +
  (SELECT COUNT(*) FROM tennis_matches) +
  (SELECT COUNT(*) FROM golf_tournaments) +
  (SELECT COUNT(*) FROM f1_races) +
  (SELECT COUNT(*) FROM boxing_matches) +
  (SELECT COUNT(*) FROM darts_tournaments) +
  (SELECT COUNT(*) FROM snooker_tournaments) +
  (SELECT COUNT(*) FROM uk_companies) +
  (SELECT COUNT(*) FROM weather_data) +
  (SELECT COUNT(*) FROM news_articles) +
  (SELECT COUNT(*) FROM government_statistics) +
  (SELECT COUNT(*) FROM currency_rates) +
  (SELECT COUNT(*) FROM commodities) +
  (SELECT COUNT(*) FROM trade_data) +
  (SELECT COUNT(*) FROM books) +
  (SELECT COUNT(*) FROM geographic_data) +
  (SELECT COUNT(*) FROM uk_car_sales) +
  (SELECT COUNT(*) FROM uk_car_manufacturing) +
  (SELECT COUNT(*) FROM uk_car_imports) +
  (SELECT COUNT(*) FROM uk_car_exports);
"
