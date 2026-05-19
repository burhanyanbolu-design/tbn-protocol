import sys
sys.path.insert(0, '/opt/tbn-protocol')
from tbn.philosophy_core_complete import PhilosophyPromptInjector
injector = PhilosophyPromptInjector.from_file('data/santiago_bot_identity.json')
print('Loaded:', injector.bot_identity.bot_name)
r = injector.chat('what is the meaning of life')
print('Response:', r[:400])
