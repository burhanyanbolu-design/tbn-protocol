import requests, json

r = requests.post('http://localhost:5004/api/register',
    headers={
        'X-Admin-Secret': 'hardin-admin-2026-secret',
        'Content-Type': 'application/json'
    },
    json={
        'name': 'CLARIXO-Test-Agent',
        'type': 'VALIDATOR'
    }
)
print(f"Status: {r.status_code}")
data = r.json()
print(f"Bot ID: {data.get('bot_id')}")
print(f"Cert: {data.get('cert_level')}")
