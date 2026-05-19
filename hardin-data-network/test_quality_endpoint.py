import requests
r = requests.get('http://127.0.0.1:5008/quality-check')
d = r.json()
print(d['result'][-500:])
