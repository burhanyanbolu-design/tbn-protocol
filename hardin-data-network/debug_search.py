import requests
r = requests.post('http://127.0.0.1:5008/search',
    json={'query': 'Arsenal'},
    headers={'Content-Type': 'application/json'})
print("Status:", r.status_code)
print("Response:", r.text[:500])
