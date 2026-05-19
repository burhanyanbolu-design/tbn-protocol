#!/bin/bash
# Quick setup for Hardin Data Network
set -e

echo "=================================================="
echo "  Hardin Data Network - Quick Setup"
echo "=================================================="

# Check PostgreSQL
if ! command -v psql &> /dev/null; then
    echo "Installing PostgreSQL..."
    sudo apt update
    sudo apt install -y postgresql postgresql-contrib
    sudo systemctl start postgresql
    sudo systemctl enable postgresql
fi

# Create database and user
echo "Creating database..."
sudo -u postgres psql << 'EOSQL'
DROP DATABASE IF EXISTS hardin_data_network;
CREATE DATABASE hardin_data_network;
DROP USER IF EXISTS hardin_admin;
CREATE USER hardin_admin WITH PASSWORD 'hardin2026';
ALTER DATABASE hardin_data_network OWNER TO hardin_admin;
\c hardin_data_network
GRANT ALL ON SCHEMA public TO hardin_admin;
EOSQL

# Create tables
echo "Creating tables..."
sudo -u postgres psql -d hardin_data_network << 'EOSQL'
-- TBN Bots table
CREATE TABLE IF NOT EXISTS tbn_bots (
    bot_id VARCHAR(255) PRIMARY KEY,
    bot_name VARCHAR(255),
    bot_type VARCHAR(100),
    owner_name VARCHAR(255),
    owner_email VARCHAR(255),
    capabilities JSON,
    star_rating INT CHECK (star_rating BETWEEN 1 AND 5),
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP,
    status VARCHAR(50) DEFAULT 'active'
);

-- Retail businesses
CREATE TABLE retail_businesses (
    business_id SERIAL PRIMARY KEY,
    business_name VARCHAR(255),
    business_type VARCHAR(100),
    business_category VARCHAR(100),
    address TEXT,
    city VARCHAR(100),
    postcode VARCHAR(20),
    phone VARCHAR(50),
    website VARCHAR(500),
    overall_rating DECIMAL(3,2),
    price_range VARCHAR(20),
    collected_by_bot VARCHAR(255),
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    verified_by_tbn BOOLEAN DEFAULT TRUE
);

-- Ladies clothing
CREATE TABLE ladies_clothing_shops (
    shop_id SERIAL PRIMARY KEY,
    business_id INT REFERENCES retail_businesses(business_id),
    style_focus VARCHAR(100),
    age_range VARCHAR(50),
    size_range_start VARCHAR(10),
    size_range_end VARCHAR(10),
    plus_size_available BOOLEAN,
    collected_by_bot VARCHAR(255),
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Confectionery
CREATE TABLE confectionery_shops (
    shop_id SERIAL PRIMARY KEY,
    business_id INT REFERENCES retail_businesses(business_id),
    shop_specialization VARCHAR(100),
    handmade_chocolates BOOLEAN,
    imported_sweets BOOLEAN,
    sugar_free_options BOOLEAN,
    vegan_options BOOLEAN,
    collected_by_bot VARCHAR(255),
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Bakeries
CREATE TABLE bakeries (
    bakery_id SERIAL PRIMARY KEY,
    business_id INT REFERENCES retail_businesses(business_id),
    bakery_type VARCHAR(100),
    fresh_bread BOOLEAN,
    pastries BOOLEAN,
    cakes BOOLEAN,
    turkish_pastries BOOLEAN,
    gluten_free BOOLEAN,
    vegan_options BOOLEAN,
    fresh_daily BOOLEAN,
    collected_by_bot VARCHAR(255),
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO hardin_admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO hardin_admin;
EOSQL

echo ""
echo "✅ Database setup complete!"
echo "Database: hardin_data_network"
echo "User: hardin_admin"
echo "Password: hardin2026"
