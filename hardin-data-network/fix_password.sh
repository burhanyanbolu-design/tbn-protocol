#!/bin/bash
cd /tmp
sudo -u postgres psql -d hardin_data_network -c "ALTER USER hardin_admin WITH PASSWORD 'hardin2026';"
echo "Password updated"
