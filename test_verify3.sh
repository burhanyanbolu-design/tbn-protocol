#!/bin/bash
python3 -c "
import json
data = json.load(open('/opt/tbn-protocol/data/security_challenges.json'))
bot = 'tbn-bot-ac8ef57c5c79ce02'
evals = [r for r in data if r.get('type') == 'evaluation' and r.get('bot_id') == bot and r.get('result') == 'PASS']
print(f'PASS evaluations for {bot}: {len(evals)}')
if evals:
    print(json.dumps(evals[-1], indent=2))
else:
    print('NO PASSING EVALUATION FOUND')
    # Check all evaluations
    all_evals = [r for r in data if r.get('type') == 'evaluation']
    print(f'Total evaluations in file: {len(all_evals)}')
    for e in all_evals[-3:]:
        print(f'  {e.get(\"bot_id\")} -> {e.get(\"result\")}')
"
