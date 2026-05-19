#!/bin/bash
# Create Kamailio database manually

# Set charset env var to avoid interactive prompt
export CHARSET="utf8"

# Update kamctlrc
sudo bash -c 'cat > /etc/kamailio/kamctlrc << EOF
DBENGINE=MYSQL
DBRWUSER="kamailio"
DBRWPW="hardinai2026"
DBROUSER="kamailio"
DBROPW="hardinai2026"
DBROOTUSER="root"
DBROOTPW=""
CHARSET="utf8"
INSTALL_EXTRA_TABLES=yes
INSTALL_PRESENCE_TABLES=no
INSTALL_DBUID_TABLES=no
EOF'

# Drop and recreate database
sudo mysql -e "DROP DATABASE IF EXISTS kamailio;"
sudo mysql -e "CREATE DATABASE kamailio CHARACTER SET utf8;"
sudo mysql -e "GRANT ALL PRIVILEGES ON kamailio.* TO 'kamailio'@'localhost';"
sudo mysql -e "FLUSH PRIVILEGES;"

# Import Kamailio schema files directly
SCHEMA_DIR="/usr/share/kamailio/mysql"
if [ -d "$SCHEMA_DIR" ]; then
    echo "Importing Kamailio schema from $SCHEMA_DIR..."
    for f in $SCHEMA_DIR/*.sql; do
        echo "  Importing: $(basename $f)"
        sudo mysql kamailio < "$f" 2>/dev/null
    done
else
    echo "Schema dir not found, trying kamdbctl..."
    echo "utf8" | sudo kamdbctl create
fi

# Create dispatcher entry for Asterisk
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

# Verify
echo ""
echo "=== Verification ==="
sudo mysql kamailio -e "SHOW TABLES;" | head -20
echo ""
echo "Dispatcher entries:"
sudo mysql kamailio -e "SELECT * FROM dispatcher;"
echo ""
echo "DONE - Kamailio DB ready"
