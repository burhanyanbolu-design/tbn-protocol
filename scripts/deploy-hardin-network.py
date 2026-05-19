#!/usr/bin/env python3
"""Deploy Hardin Data Network to server"""
import os
import subprocess

SERVER = "ubuntu@3.11.229.68"
KEY = "aws-lightsail.pem"

print("=" * 60)
print("  Deploying Hardin Data Network")
print("=" * 60)

# Copy files to server
print("\n[1/3] Copying files to server...")
subprocess.run([
    "scp", "-i", KEY, "-r",
    "hardin-data-network/",
    f"{SERVER}:/opt/tbn-protocol/"
])

# Make script executable
print("\n[2/3] Making setup script executable...")
subprocess.run([
    "ssh", "-i", KEY, SERVER,
    "chmod +x /opt/tbn-protocol/hardin-data-network/setup/quick-setup.sh"
])

# Run setup
print("\n[3/3] Running database setup...")
subprocess.run([
    "ssh", "-i", KEY, SERVER,
    "bash /opt/tbn-protocol/hardin-data-network/setup/quick-setup.sh"
])

print("\n" + "=" * 60)
print("  ✅ Deployment Complete!")
print("=" * 60)
