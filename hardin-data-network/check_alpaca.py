import sys
sys.path.insert(0, '/opt/vc3')
from dotenv import load_dotenv
import os

load_dotenv('/opt/vc3/.env')

api_key = os.getenv('ALPACA_API_KEY', '')
secret  = os.getenv('ALPACA_SECRET_KEY', '')
base    = os.getenv('ALPACA_BASE_URL', '')

print("API Key:    ", api_key[:8] + "..." if api_key else "MISSING")
print("Secret Key: ", secret[:8] + "..." if secret else "MISSING")
print("Base URL:   ", base)
print()

# Test the connection
try:
    from alpaca.trading.client import TradingClient
    client = TradingClient(api_key, secret, paper=True)
    account = client.get_account()
    print("CONNECTION: OK")
    print("Account status:", account.status)
    print("Cash:", account.cash)
except Exception as e:
    print("CONNECTION FAILED:", str(e))
    print()
    print(">>> This means the API keys are wrong/expired!")
    print(">>> Update /opt/vc3/.env with new keys from Alpaca dashboard")
