import requests

r = requests.post('http://127.0.0.1:5008/search',
    json={'query': 'Chelsea vs Man United who will win?'})
print("Status:", r.status_code)
d = r.json()
print(d.get('answer', d.get('error', 'No response'))[:500])
