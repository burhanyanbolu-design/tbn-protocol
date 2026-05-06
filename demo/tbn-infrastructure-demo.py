#!/usr/bin/env python3
"""
TBN Infrastructure Demo
Shows TBN as the trust infrastructure layer between companies and bots

This demo has two parts:
1. Company Server (runs on AWS) - provides data, requires TBN certification
2. Bot Client (runs on your PC) - requests data using TBN certificate
"""

import json
import requests
from datetime import datetime
from tbn import TBNClient

# ============================================================================
# PART 1: COMPANY SERVER SIDE
# ============================================================================

class CompanyDataProvider:
    """
    A company that provides data to certified bots only.
    This represents ANY company that wants to use TBN infrastructure.
    """
    
    def __init__(self, company_name, tbn_server="https://tbn.hardinai.co.uk"):
        self.company_name = company_name
        self.tbn_server = tbn_server
        self.access_log = []
        
    def create_tbn_json(self):
        """
        Create the tbn.json file that companies publish on their website.
        This tells bots: "We accept TBN-certified bots only"
        """
        return {
            "tbn_version": "1.0",
            "company": self.company_name,
            "bot_policy": {
                "certified_bots_only": True,
                "require_tbn_certificate": True,
                "minimum_certification_level": "COMMUNITY",
                "log_all_access": True
            },
            "public_resources": [
                {
                    "endpoint": "/api/data",
                    "description": "Company data API",
                    "authentication": "tbn_certificate_required"
                }
            ],
            "contact": {
                "email": "api@company.com",
                "tbn_verification_endpoint": "/api/verify-bot"
            }
        }
    
    def verify_bot_certificate(self, bot_id):
        """
        Company verifies the bot's TBN certificate.
        This is the KEY function - company doesn't build verification,
        they just check with TBN!
        """
        print(f"\n🔍 [{self.company_name}] Verifying bot: {bot_id}")
        print(f"   Checking with TBN infrastructure...")
        
        try:
            # Company asks TBN: "Is this bot certified?"
            response = requests.post(
                f"{self.tbn_server}/api/verify",
                json={"bot_id": bot_id},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("verified"):
                    cert_level = result.get("certification_level", "STANDARD")
                    print(f"   ✅ Bot verified by TBN!")
                    print(f"   📜 Certification level: {cert_level}")
                    
                    # Log the access
                    self.access_log.append({
                        "bot_id": bot_id,
                        "timestamp": datetime.now().isoformat(),
                        "verified": True,
                        "certification_level": cert_level
                    })
                    
                    return True, cert_level
                else:
                    print(f"   ❌ Bot NOT verified by TBN")
                    return False, None
            else:
                print(f"   ❌ TBN verification failed")
                return False, None
                
        except Exception as e:
            print(f"   ❌ Error verifying with TBN: {e}")
            return False, None
    
    def provide_data(self, bot_id):
        """
        Provide data to the bot if they have valid TBN certificate.
        """
        verified, cert_level = self.verify_bot_certificate(bot_id)
        
        if verified:
            print(f"\n✅ [{self.company_name}] Access GRANTED to bot {bot_id}")
            print(f"   Providing data...")
            
            # Company's valuable data
            data = {
                "company": self.company_name,
                "data": {
                    "products": ["AI Tool A", "AI Tool B", "AI Tool C"],
                    "pricing": {"basic": "$99/mo", "pro": "$299/mo"},
                    "api_docs": "https://company.com/docs"
                },
                "message": "This data is provided because you have a valid TBN certificate",
                "accessed_at": datetime.now().isoformat()
            }
            
            return {"success": True, "data": data}
        else:
            print(f"\n❌ [{self.company_name}] Access DENIED to bot {bot_id}")
            print(f"   Reason: No valid TBN certificate")
            return {"success": False, "error": "TBN certification required"}
    
    def show_access_log(self):
        """Show all bot access attempts"""
        print(f"\n📊 [{self.company_name}] Access Log:")
        print("=" * 60)
        for entry in self.access_log:
            print(f"Bot: {entry['bot_id']}")
            print(f"Time: {entry['timestamp']}")
            print(f"Verified: {entry['verified']}")
            print(f"Level: {entry.get('certification_level', 'N/A')}")
            print("-" * 60)


# ============================================================================
# PART 2: BOT CLIENT SIDE
# ============================================================================

class TBNCertifiedBot:
    """
    A bot that uses TBN infrastructure to access company data.
    This represents ANY bot developer who wants to access multiple companies.
    """
    
    def __init__(self, bot_name, bot_type="SEARCH"):
        self.bot_name = bot_name
        self.bot_type = bot_type
        self.tbn_client = None
        self.bot_id = None
        
    def register_with_tbn(self):
        """
        Bot registers with TBN to get a certificate.
        This is the ONLY place bots can get certified!
        """
        print(f"\n🤖 [{self.bot_name}] Registering with TBN infrastructure...")
        
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
            
            return True
            
        except Exception as e:
            print(f"   ❌ Registration failed: {e}")
            return False
    
    def access_company_data(self, company_provider):
        """
        Bot tries to access company data using TBN certificate.
        """
        if not self.bot_id:
            print(f"\n❌ [{self.bot_name}] Cannot access - no TBN certificate!")
            return None
        
        print(f"\n🤖 [{self.bot_name}] Requesting data from {company_provider.company_name}")
        print(f"   Presenting TBN certificate: {self.bot_id}")
        
        # Request data from company
        result = company_provider.provide_data(self.bot_id)
        
        if result["success"]:
            print(f"\n✅ [{self.bot_name}] Data received!")
            print(f"   Data: {json.dumps(result['data'], indent=2)}")
            return result["data"]
        else:
            print(f"\n❌ [{self.bot_name}] Access denied: {result.get('error')}")
            return None


# ============================================================================
# DEMO SCENARIOS
# ============================================================================

def demo_scenario_1_certified_bot():
    """
    Scenario 1: Certified bot successfully accesses company data
    """
    print("\n" + "=" * 70)
    print("SCENARIO 1: TBN-Certified Bot Accessing Company Data")
    print("=" * 70)
    
    # Company sets up their data provider
    company = CompanyDataProvider("Acme Corp")
    
    # Show the tbn.json file
    print("\n📄 Company publishes tbn.json:")
    print(json.dumps(company.create_tbn_json(), indent=2))
    
    # Bot registers with TBN
    bot = TBNCertifiedBot("DataCollectorBot", "SEARCH")
    bot.register_with_tbn()
    
    # Bot tries to access company data
    data = bot.access_company_data(company)
    
    # Show company's access log
    company.show_access_log()
    
    return data is not None


def demo_scenario_2_uncertified_bot():
    """
    Scenario 2: Uncertified bot gets blocked
    """
    print("\n" + "=" * 70)
    print("SCENARIO 2: Uncertified Bot Blocked")
    print("=" * 70)
    
    company = CompanyDataProvider("Acme Corp")
    
    # Fake bot without TBN certificate
    fake_bot_id = "fake-bot-12345"
    
    print(f"\n🤖 [FakeBot] Trying to access {company.company_name}")
    print(f"   Using fake ID: {fake_bot_id}")
    
    # Try to access without TBN certificate
    result = company.provide_data(fake_bot_id)
    
    company.show_access_log()
    
    return result["success"] == False


def demo_scenario_3_multiple_companies():
    """
    Scenario 3: One TBN certificate works across multiple companies
    This shows the POWER of TBN infrastructure!
    """
    print("\n" + "=" * 70)
    print("SCENARIO 3: One Certificate, Multiple Companies")
    print("=" * 70)
    
    # Multiple companies using TBN
    companies = [
        CompanyDataProvider("Acme Corp"),
        CompanyDataProvider("TechStart Inc"),
        CompanyDataProvider("DataHub Ltd")
    ]
    
    # One bot with TBN certificate
    bot = TBNCertifiedBot("UniversalBot", "SEARCH")
    bot.register_with_tbn()
    
    print(f"\n🎯 Bot has ONE TBN certificate")
    print(f"   Now accessing {len(companies)} different companies...")
    
    # Access all companies with the same certificate!
    for company in companies:
        bot.access_company_data(company)
    
    # Show all access logs
    for company in companies:
        company.show_access_log()


# ============================================================================
# MAIN DEMO
# ============================================================================

def main():
    """
    Run the complete TBN infrastructure demo
    """
    print("\n" + "=" * 70)
    print("TBN INFRASTRUCTURE DEMO")
    print("Showing TBN as the trust layer for AI agents")
    print("=" * 70)
    
    print("\n📋 What this demo shows:")
    print("   1. Companies don't build their own bot verification")
    print("   2. They just check TBN certificates")
    print("   3. Bots get ONE certificate that works everywhere")
    print("   4. TBN is the ONLY authority that can certify bots")
    
    input("\nPress Enter to start demo...")
    
    # Run scenarios
    demo_scenario_1_certified_bot()
    input("\nPress Enter for next scenario...")
    
    demo_scenario_2_uncertified_bot()
    input("\nPress Enter for next scenario...")
    
    demo_scenario_3_multiple_companies()
    
    print("\n" + "=" * 70)
    print("DEMO COMPLETE")
    print("=" * 70)
    print("\n💡 Key Takeaway:")
    print("   TBN is the infrastructure layer that:")
    print("   ✅ Companies rely on for bot verification")
    print("   ✅ Bots need to access any company")
    print("   ✅ Creates a network effect (more companies → more bots → more value)")
    print("   ✅ Has monopoly position as the ONLY certification authority")


if __name__ == "__main__":
    main()
