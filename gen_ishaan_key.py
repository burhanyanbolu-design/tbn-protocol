"""Generate API key for Ishaan (Shango)."""
import sys
sys.path.insert(0, ".")
from api.access_control import generate_api_key

result = generate_api_key("Shango", "ishaan@shango.io", tier="PRO")
print(f"API Key: {result['api_key']}")
print(f"Tier: {result['tier']}")
print(f"Expires: {result['expires_at']}")
print("\nSend this key to Ishaan. It won't be shown again.")
