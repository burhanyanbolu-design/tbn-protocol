#!/bin/bash
# Setup Kamailio MySQL database and user

# Create MySQL user for Kamailio
sudo mysql -e "CREATE USER IF NOT EXISTS 'kamailio'@'localhost' IDENTIFIED BY 'hardinai2026';"
sudo mysql -e "CREATE DATABASE IF NOT EXISTS kamailio;"
sudo mysql -e "GRANT ALL PRIVILEGES ON kamailio.* TO 'kamailio'@'localhost';"
sudo mysql -e "FLUSH PRIVILEGES;"

# Configure kamdbctl for database creation
sudo sed -i 's/# DBENGINE=MYSQL/DBENGINE=MYSQL/' /etc/kamailio/kamctlrc
sudo sed -i 's/# DBRWUSER=.*/DBRWUSER="kamailio"/' /etc/kamailio/kamctlrc
sudo sed -i 's/# DBRWPW=.*/DBRWPW="hardinai2026"/' /etc/kamailio/kamctlrc
sudo sed -i 's/# DBROUSER=.*/DBROUSER="kamailio"/' /etc/kamailio/kamctlrc
sudo sed -i 's/# DBROPW=.*/DBROPW="hardinai2026"/' /etc/kamailio/kamctlrc
sudo sed -i 's/# DBROOTUSER=.*/DBROOTUSER="root"/' /etc/kamailio/kamctlrc

# Create Kamailio database tables
echo "y" | sudo kamdbctl create

# Create dispatcher table for Asterisk routing
sudo mysql kamailio -e "
CREATE TABLE IF NOT EXISTS dispatcher (
  id INT(10) UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  setid INT DEFAULT 0 NOT NULL,
  destination VARCHAR(192) DEFAULT '' NOT NULL,
  flags INT DEFAULT 0 NOT NULL,
  priority INT DEFAULT 0 NOT NULL,
  attrs VARCHAR(128) DEFAULT '' NOT NULL,
  description VARCHAR(64) DEFAULT '' NOT NULL
);
INSERT IGNORE INTO dispatcher (setid, destination, flags, priority, description)
VALUES (1, 'sip:127.0.0.1:5080', 0, 0, 'Local Asterisk');
"

echo "=== Kamailio DB Setup Complete ==="
echo "Database: kamailio"
echo "User: kamailio"
echo "Asterisk dispatcher: 127.0.0.1:5080"
