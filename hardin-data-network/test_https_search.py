import requests
r = requests.post('https://search.hardinai.co.uk/search',
    json={'query': 'Arsenal'},
    headers={'Content-Type': 'application/json'})
print("Status:", r.status_code)
print("Response:", r.text[:200])
