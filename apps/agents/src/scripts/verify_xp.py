import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from apps.agents.src.tools.celo import CeloToolbox

# Load env vars manually to ensure config loads correctly
from dotenv import load_dotenv
load_dotenv("apps/agents/.env")

from apps.agents.src.config import settings

async def main():
    print("Verifying XP Granting...")
    
    celo = CeloToolbox(
        rpc_url=settings.celo_rpc_url,
        private_key=settings.celo_private_key
    )
    
    # Use the agent's address as test subject if no other
    test_address = celo.account.address
    campaign_id = "demo-campaign"
    
    print(f"Testing with address: {test_address}")
    print(f"Campaign: {campaign_id}")
    print(f"Registry: {settings.registry_address}")
    
    # 1. Check initial balance
    initial_xp = celo.get_xp_balance(settings.registry_address, campaign_id, test_address)
    print(f"Initial XP: {initial_xp}")
    
    # 2. Grant XP
    amount = 10
    print(f"Granting {amount} XP...")
    try:
        tx_hash = celo.grant_xp(settings.registry_address, campaign_id, test_address, amount)
        print(f"Tx sent: {tx_hash}")
        
        # Wait for receipt
        print("Waiting for confirmation...")
        receipt = celo.web3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"Confirmed in block {receipt['blockNumber']}")
        
    except Exception as e:
        print(f"Error granting XP: {e}")
        return

    # 3. Check new balance
    new_xp = celo.get_xp_balance(settings.registry_address, campaign_id, test_address)
    print(f"New XP: {new_xp}")
    
    if new_xp == initial_xp + amount:
        print("✅ SUCCESS: XP updated correctly")
    else:
        print(f"❌ FAILURE: XP mismatch (Expected {initial_xp + amount}, got {new_xp})")

if __name__ == "__main__":
    asyncio.run(main())
