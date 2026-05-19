#!/bin/bash
# Hardin Data Network - Database Setup Script
# Run this ON THE SERVER (not locally)
# 
# Usage: bash setup-database.sh

set -e

echo "=================================================="
echo "  Hardin Data Network - Database Setup"
echo "=================================================="

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo ""
    echo "[1/6] Installing PostgreSQL..."
    sudo apt update
    sudo apt install -y postgresql postgresql-contrib
    sudo systemctl start postgresql
    sudo systemctl enable postgresql
else
    echo ""
    echo "[1/6] PostgreSQL already installed ✓"
fi

# Create database
echo ""
echo "[2/6] Creating database..."
sudo -u postgres psql -c "DROP DATABASE IF EXISTS hardin_data_network;" || true
sudo -u postgres psql -c "CREATE DATABASE hardin_data_network;"

# Create user
echo ""
echo "[3/6] Creating database user..."
sudo -u postgres psql -c "DROP USER IF EXISTS hardin_admin;" || true
sudo -u postgres psql -c "CREATE USER hardin_admin WITH PASSWORD 'hardin2026secure';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE hardin_data_network TO hardin_admin;"

# Run schema files
echo ""
echo "[4/6] Creating tables..."

# Main schema
echo "  → Main schema (TBN bots, registry)..."
sudo -u postgres psql -d hardin_data_network -f /opt/tbn-protocol/hardin-data-network/database/schema.sql

# Sports & Lottery schema
echo "  → Sports & Lottery schema..."
sudo -u postgres psql -d hardin_data_network -f /opt/tbn-protocol/hardin-data-network/database/sports_public_data_schema.sql

# Restaurant schema
echo "  → Restaurant schema..."
sudo -u postgres psql -d hardin_data_network -f /opt/tbn-protocol/hardin-data-network/database/restaurant_ratings_schema.sql

# Retail schema
echo "  → Retail shopping schema..."
sudo -u postgres psql -d hardin_data_network -f /opt/tbn-protocol/hardin-data-network/database/retail_shopping_schema.sql

# Bot intelligence schema
echo "  → Bot intelligence schema..."
sudo -u postgres psql -d hardin_data_network -f /opt/tbn-protocol/hardin-data-network/database/bot_intelligence_schema.sql

# Grant permissions
echo ""
echo "[5/6] Setting permissions..."
sudo -u postgres psql -d hardin_data_network -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO hardin_admin;"
sudo -u postgres psql -d hardin_data_network -c "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO hardin_admin;"

# Verify
echo ""
echo "[6/6] Verifying setup..."
TABLE_COUNT=$(sudo -u postgres psql -d hardin_data_network -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")
echo "  → Tables created: $TABLE_COUNT"

echo ""
echo "=================================================="
echo "  ✅ Database Setup Complete!"
echo "=================================================="
echo ""
echo "Database: hardin_data_network"
echo "User: hardin_admin"
echo "Password: hardin2026secure"
echo "Tables: $TABLE_COUNT"
echo ""
echo "Connect with:"
echo "  psql -h localhost -U hardin_admin -d hardin_data_network"
echo ""
echo "=================================================="
