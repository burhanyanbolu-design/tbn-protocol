#!/bin/bash
python3 -c "
import requests, json
bot_id = 'tbn-bot-ac8ef57c5c79ce02'
r = requests.post('http://localhost:5004/api/security-challenge/verify', json={'bot_id': bot_id, 'bot_endpoint': '', 'system_prompt': '', 'config': {}})
print(json.dumps(r.json(), indent=2))
"
