#!/usr/bin/env python3
"""
Test script for Boomi integration endpoints.
Run this to verify the integration is working.
"""

import requests
import json
from datetime import datetime, timezone

# Configuration
BASE_URL = "https://tbn.hardinai.co.uk"
API_KEY = "tbn_live_YOUR_KEY_HERE"  # Replace with your actual key

def test_health_check():
    """Test the health check endpoint (no auth required)."""
    print("\n" + "="*60)
    print("TEST 1: Health Check (No Auth)")
    print("="*60)
    
    url = f"{BASE_URL}/api/boomi/health"
    print(f"GET {url}")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ PASS: Health check is working")
            return True
        else:
            print("❌ FAIL: Unexpected status code")
            return False
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False


def test_bot_registration(api_key):
    """Test bot registration endpoint."""
    print("\n" + "="*60)
    print("TEST 2: Bot Registration (With Auth)")
    print("="*60)
    
    url = f"{BASE_URL}/api/boomi/process"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "process_type": "bot_registration",
        "data": {
            "bot_name": "TestBot",
            "bot_type": "SEARCH",
            "company": "Test Corp",
            "email": "test@test.com",
            "description": "Test bot for Boomi integration"
        },
        "metadata": {
            "boomi_process_id": "test-001",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "boomi"
        }
    }
    
    print(f"POST {url}")
    print(f"Headers: {headers}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200 and response.json().get("success"):
            print("✅ PASS: Bot registration is working")
            return True
        else:
            print("❌ FAIL: Bot registration failed")
            return False
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False


def test_certification_check(api_key, bot_id):
    """Test certification check endpoint."""
    print("\n" + "="*60)
    print("TEST 3: Certification Check (With Auth)")
    print("="*60)
    
    url = f"{BASE_URL}/api/boomi/process"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "process_type": "certification_check",
        "data": {
            "bot_id": bot_id,
            "cert_level": "GOLD"
        },
        "metadata": {
            "boomi_process_id": "test-002",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "boomi"
        }
    }
    
    print(f"POST {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200 and response.json().get("success"):
            print("✅ PASS: Certification check is working")
            return True
        else:
            print("❌ FAIL: Certification check failed")
            return False
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False


def test_governance_query(api_key):
    """Test governance query endpoint."""
    print("\n" + "="*60)
    print("TEST 4: Governance Query (With Auth)")
    print("="*60)
    
    url = f"{BASE_URL}/api/boomi/process"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "process_type": "governance_query",
        "data": {
            "query_type": "bot_status",
            "limit": 5
        },
        "metadata": {
            "boomi_process_id": "test-003",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "boomi"
        }
    }
    
    print(f"POST {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200 and response.json().get("success"):
            print("✅ PASS: Governance query is working")
            return True
        else:
            print("❌ FAIL: Governance query failed")
            return False
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False


def main():
    print("\n" + "="*60)
    print("BOOMI INTEGRATION TEST SUITE")
    print("="*60)
    print(f"Base URL: {BASE_URL}")
    print(f"API Key: {API_KEY[:20]}..." if API_KEY != "tbn_live_YOUR_KEY_HERE" else "API Key: NOT SET")
    
    # Test 1: Health check
    health_ok = test_health_check()
    
    if not health_ok:
        print("\n❌ Health check failed. Stopping tests.")
        return
    
    # Test 2: Bot registration
    if API_KEY == "tbn_live_YOUR_KEY_HERE":
        print("\n⚠️  API key not set. Skipping authenticated tests.")
        print("To run full tests, set API_KEY in this script.")
        return
    
    reg_ok = test_bot_registration(API_KEY)
    
    # Test 3: Certification check (use a known bot ID)
    if reg_ok:
        cert_ok = test_certification_check(API_KEY, "tbn-bot-testbot-001")
    else:
        print("\n⚠️  Bot registration failed. Skipping certification check.")
        cert_ok = False
    
    # Test 4: Governance query
    gov_ok = test_governance_query(API_KEY)
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Health Check:        {'✅ PASS' if health_ok else '❌ FAIL'}")
    print(f"Bot Registration:    {'✅ PASS' if reg_ok else '❌ FAIL'}")
    print(f"Certification Check: {'✅ PASS' if cert_ok else '❌ FAIL'}")
    print(f"Governance Query:    {'✅ PASS' if gov_ok else '❌ FAIL'}")
    
    all_pass = health_ok and reg_ok and cert_ok and gov_ok
    print(f"\nOverall: {'✅ ALL TESTS PASSED' if all_pass else '❌ SOME TESTS FAILED'}")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
