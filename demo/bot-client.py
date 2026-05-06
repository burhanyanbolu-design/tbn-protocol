#!/usr/bin/env python3
"""
Bot Client - Computer 2 (Your PC)
Represents a bot that uses TBN infrastructure to access company data
"""

import requests
import json
import argparse
from datetime import datetime
from tbn import TBNClient

class TBNCertifiedBot:
    """
    A bot that uses TBN infrastructure to access company data
    """
    
    def __init__(self, bot_name="DataCollectorBot", bot_type="SEARCH"):
        self.bot_name = bot_name
        self.bot_type = bot_type
        self.tbn_client = None
        self.bot_id = None
        self.tbn_server = "https://tbn.hardinai.co.uk"
        
    def register_with_tbn(self):
        """
        Register with TBN to get a certificate.
        This is the ONLY way to get certified!
        """
        print(f"\n🤖 [{self.bot_name}] Registering with TBN infrastructure...")
        print(f"   TBN Server: {self.tbn_server}")
        
        try:
            # Create TBN client
            self.tbn_client = TBNClient(
                bot_name=self.bot_name,
                bot_type=self.bot_type
            )
            
            # Register and get certificate
            result = self.tbn_client.register()
            self.bot_id = result.get("bot_id")
            
            print(f"   ✅ Registered with TBN!")
            print(f"   🆔 Bot ID: {self.bot_id}")
            print(f"   📜 Certificate issued by TBN")
            print(f"   🔗 View certificate: {self.tbn_server}/api/bots")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Registration failed: {e}")
            print(f"   💡 Make sure TBN server is running at {self.tbn_server}")
            return False
    
    def read_company_tbn_json(self, company_url):
        """
        Read the company's tbn.json file to understand their policy
        """
        print(f"\n📄 [{self.bot_name}] Reading company's TBN policy...")
        
        try:
            response = requests.get(f"{company_url}/tbn.json", timeout=10)
            
            if response.status_code == 200:
                tbn_config = response.json()
                print(f"   ✅ TBN policy retrieved")
                print(f"   Company: {tbn_config.get('company')}")
                print(f"   Requires TBN certificate: {tbn_config.get('bot_policy', {}).get('require_tbn_certificate')}")
                print(f"   Minimum level: {tbn_config.get('bot_policy', {}).get('minimum_certification_level')}")
                return tbn_config
            else:
                print(f"   ❌ Could not read tbn.json: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"   ❌ Error reading tbn.json: {e}")
            return None
    
    def access_company_data(self, company_url):
        """
        Access company data using TBN certificate
        """
        if not self.bot_id:
            print(f"\n❌ [{self.bot_name}] Cannot access - no TBN certificate!")
            print(f"   💡 Run register_with_tbn() first")
            return None
        
        # First, read the company's TBN policy
        tbn_config = self.read_company_tbn_json(company_url)
        
        if not tbn_config:
            print(f"\n⚠️  [{self.bot_name}] Company doesn't have tbn.json")
            print(f"   Trying to access anyway...")
        
        print(f"\n🤖 [{self.bot_name}] Requesting data from company")
        print(f"   Company URL: {company_url}")
        print(f"   Presenting TBN certificate: {self.bot_id}")
        
        try:
            # Request data with TBN certificate
            response = requests.post(
                f"{company_url}/api/data",
                json={"bot_id": self.bot_id},
                headers={"X-TBN-Bot-ID": self.bot_id},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("success"):
                    print(f"\n✅ [{self.bot_name}] Data received!")
                    print(f"   Message: {result.get('message')}")
                    print(f"\n📊 Company Data:")
                    print(json.dumps(result.get('data'), indent=2))
                    return result.get('data')
                else:
                    print(f"\n❌ [{self.bot_name}] Access denied")
                    print(f"   Error: {result.get('error')}")
                    return None
            else:
                error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
                print(f"\n❌ [{self.bot_name}] Access denied: {response.status_code}")
                print(f"   Error: {error_data.get('error', 'Unknown error')}")
                return None
                
        except Exception as e:
            print(f"\n❌ [{self.bot_name}] Error accessing company: {e}")
            return None
    
    def view_company_access_log(self, company_url):
        """
        View the company's access log to see all bot attempts
        """
        print(f"\n📊 [{self.bot_name}] Viewing company access log...")
        
        try:
            response = requests.get(f"{company_url}/api/access-log", timeout=10)
            
            if response.status_code == 200:
                log_data = response.json()
                print(f"\n📋 Access Log for {log_data.get('company')}:")
                print(f"   Total requests: {log_data.get('total_requests')}")
                print("\n   Recent access attempts:")
                
                for entry in log_data.get('log', [])[-5:]:  # Show last 5
                    print(f"\n   Bot: {entry.get('bot_id')}")
                    print(f"   Name: {entry.get('bot_name', 'N/A')}")
                    print(f"   Time: {entry.get('timestamp')}")
                    print(f"   Action: {entry.get('action')}")
                    print(f"   Verified: {'✅' if entry.get('verified') else '❌'}")
                    if entry.get('certification_level'):
                        print(f"   Level: {entry.get('certification_level')}")
                
                return log_data
            else:
                print(f"   ❌ Could not retrieve access log: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"   ❌ Error retrieving access log: {e}")
            return None


def main():
    """
    Run the bot client demo
    """
    parser = argparse.ArgumentParser(description='TBN Bot Client Demo')
    parser.add_argument('--company-url', default='http://localhost:5010',
                       help='Company server URL (default: http://localhost:5010)')
    parser.add_argument('--bot-name', default='DataCollectorBot',
                       help='Bot name (default: DataCollectorBot)')
    args = parser.parse_args()
    
    print("\n" + "=" * 70)
    print("🤖 TBN BOT CLIENT DEMO")
    print("=" * 70)
    print(f"\nBot Name: {args.bot_name}")
    print(f"Company URL: {args.company_url}")
    
    # Create bot
    bot = TBNCertifiedBot(bot_name=args.bot_name)
    
    # Step 1: Register with TBN
    print("\n" + "=" * 70)
    print("STEP 1: Register with TBN Infrastructure")
    print("=" * 70)
    
    if not bot.register_with_tbn():
        print("\n❌ Failed to register with TBN. Exiting.")
        return
    
    input("\nPress Enter to continue...")
    
    # Step 2: Access company data
    print("\n" + "=" * 70)
    print("STEP 2: Access Company Data")
    print("=" * 70)
    
    data = bot.access_company_data(args.company_url)
    
    if data:
        print(f"\n✅ Successfully accessed company data!")
    else:
        print(f"\n❌ Failed to access company data")
    
    input("\nPress Enter to continue...")
    
    # Step 3: View access log
    print("\n" + "=" * 70)
    print("STEP 3: View Company Access Log")
    print("=" * 70)
    
    bot.view_company_access_log(args.company_url)
    
    # Summary
    print("\n" + "=" * 70)
    print("DEMO COMPLETE")
    print("=" * 70)
    print("\n💡 What just happened:")
    print("   1. Bot registered with TBN (the ONLY certification authority)")
    print("   2. Bot presented TBN certificate to company")
    print("   3. Company verified certificate with TBN infrastructure")
    print("   4. Access granted because bot is TBN-certified")
    print("\n🎯 Key Insight:")
    print("   Company didn't build verification - they used TBN infrastructure")
    print("   Bot got ONE certificate that works with ALL TBN-enabled companies")
    print("   TBN is the infrastructure layer everyone depends on")


if __name__ == "__main__":
    main()
