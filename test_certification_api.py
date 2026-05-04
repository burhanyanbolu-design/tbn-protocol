import requests
import json

BASE_URL = "https://tbn.hardinai.co.uk"

print("=" * 60)
print("TBN CERTIFICATION API TEST")
print("=" * 60)

# Test 1: Get all certifications (should show existing bots)
print("\n1. Testing GET /api/certifications")
print("-" * 60)
try:
    response = requests.get(f"{BASE_URL}/api/certifications")
    print(f"Status Code: {response.status_code}")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    
    if data.get('success'):
        print(f"✓ Total bots: {data['total']}")
        print(f"✓ Community: {len(data['certifications']['COMMUNITY'])}")
        print(f"✓ Standard: {len(data['certifications']['STANDARD'])}")
        print(f"✓ Restricted: {len(data['certifications']['RESTRICTED'])}")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 2: Apply for STANDARD certification
print("\n2. Testing POST /api/certify (STANDARD level)")
print("-" * 60)
try:
    # First register the bot
    reg_payload = {
        "name": "Test Bot Standard",
        "description": "A test bot for API validation",
        "capabilities": ["search", "read"]
    }
    reg_response = requests.post(f"{BASE_URL}/api/register", json=reg_payload)
    reg_data = reg_response.json()
    
    if reg_data.get('bot_id'):
        bot_id_standard = reg_data['bot_id']
        print(f"✓ Registered bot: {bot_id_standard}")
        
        # Now certify it
        payload = {
            "bot_id": bot_id_standard,
            "level": "STANDARD"
        }
        response = requests.post(f"{BASE_URL}/api/certify", json=payload)
        print(f"Status Code: {response.status_code}")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        
        if data.get('success'):
            print(f"✓ Bot certified: {data['bot_id']}")
            print(f"✓ Level: {data['cert_level']}")
        else:
            print(f"✗ Error: {data.get('error')}")
    else:
        print(f"✗ Registration failed: {reg_data}")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 3: Apply for COMMUNITY certification (requires purpose and ethical declaration)
print("\n3. Testing POST /api/certify (COMMUNITY level)")
print("-" * 60)
try:
    # First register the bot
    reg_payload = {
        "name": "Test Bot Community",
        "description": "A community test bot for API validation",
        "capabilities": ["search", "read", "write", "clone"]
    }
    reg_response = requests.post(f"{BASE_URL}/api/register", json=reg_payload)
    reg_data = reg_response.json()
    
    if reg_data.get('bot_id'):
        bot_id_community = reg_data['bot_id']
        print(f"✓ Registered bot: {bot_id_community}")
        
        # Now certify it
        payload = {
            "bot_id": bot_id_community,
            "level": "COMMUNITY",
            "purpose": "Testing bot for TBN Protocol certification system validation",
            "ethical_declaration": True
        }
        response = requests.post(f"{BASE_URL}/api/certify", json=payload)
        print(f"Status Code: {response.status_code}")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        
        if data.get('success'):
            print(f"✓ Bot certified: {data['bot_id']}")
            print(f"✓ Level: {data['cert_level']}")
        else:
            print(f"✗ Error: {data.get('error')}")
    else:
        print(f"✗ Registration failed: {reg_data}")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 4: Check certification status
print("\n4. Testing GET /api/certification/{bot_id}")
print("-" * 60)
try:
    response = requests.get(f"{BASE_URL}/api/certification/{bot_id_standard}")
    print(f"Status Code: {response.status_code}")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    
    if data.get('success'):
        print(f"✓ Found certification for: {data['certification']['bot_id']}")
        print(f"✓ Level: {data['certification']['cert_level']}")
    else:
        print(f"✗ Error: {data.get('error')}")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 5: Report a violation
print("\n5. Testing POST /api/violation")
print("-" * 60)
try:
    payload = {
        "bot_id": bot_id_standard,
        "violation": "Test violation report - bot is operating outside ethical guidelines",
        "reporter": "Test Reporter"
    }
    response = requests.post(f"{BASE_URL}/api/violation", json=payload)
    print(f"Status Code: {response.status_code}")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    
    if data.get('success') or data.get('message'):
        print(f"✓ Violation reported successfully")
        print(f"✓ Message: {data.get('message')}")
        print(f"✓ Violation count: {data.get('violation_count')}")
    else:
        print(f"✗ Error: {data.get('error')}")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 6: Try to certify without required fields (should fail)
print("\n6. Testing POST /api/certify (COMMUNITY without purpose - should fail)")
print("-" * 60)
try:
    payload = {
        "bot_id": "tbn-bot-test-003",
        "level": "COMMUNITY"
        # Missing purpose and ethical_declaration
    }
    response = requests.post(f"{BASE_URL}/api/certify", json=payload)
    print(f"Status Code: {response.status_code}")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    
    if not data.get('success'):
        print(f"✓ Correctly rejected: {data.get('error')}")
    else:
        print(f"✗ Should have failed but succeeded")
except Exception as e:
    print(f"✗ Error: {e}")

# Final summary
print("\n" + "=" * 60)
print("TEST SUMMARY")
print("=" * 60)
print("Check the certification portal to see if the test bots appear:")
print(f"{BASE_URL}/certification/portal")
print("=" * 60)
