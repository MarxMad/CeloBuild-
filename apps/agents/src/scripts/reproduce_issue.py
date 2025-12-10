import asyncio
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

# Add src to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

# Load env vars
load_dotenv("apps/agents/.env")

from apps.agents.src.config import settings
from apps.agents.src.tools.celo import CeloToolbox

async def main():
    print("🔄 Reproducing Agent Flow: Mint NFT -> Wait -> Grant XP")
    
    celo = CeloToolbox(
        rpc_url=settings.celo_rpc_url,
        private_key=settings.celo_private_key
    )
    
    # Use the agent's wallet as the recipient for testing
    recipient = celo.account.address
    campaign_id = "demo-campaign"
    
    print(f"👤 Testing with address: {recipient}")
    
    # 1. Mint NFT
    print("\n1️⃣ Attempting to Mint NFT...")
    try:
        # Create dummy metadata
        import json
        import base64
        meta = {"name": "Test NFT", "description": "Reproduction Test"}
        meta_b64 = base64.b64encode(json.dumps(meta).encode()).decode()
        token_uri = f"data:application/json;base64,{meta_b64}"
        
        tx_mint = celo.mint_nft(
            minter_address=settings.minter_address,
            campaign_id=campaign_id,
            recipient=recipient,
            metadata_uri=token_uri
        )
        print(f"✅ Mint TX sent: {tx_mint}")
    except Exception as e:
        print(f"❌ Mint Failed: {e}")
        return

    # 2. Wait (Simulating Agent)
    print("\n⏳ Waiting 5 seconds (as per agent logic)...")
    time.sleep(5)
    
    # 3. Grant XP
    print("\n2️⃣ Attempting to Grant XP...")
    try:
        tx_xp = celo.grant_xp(
            registry_address=settings.registry_address,
            campaign_id=campaign_id,
            participant=recipient,
            amount=10
        )
        print(f"✅ XP Grant TX sent: {tx_xp}")
    except Exception as e:
        print(f"❌ XP Grant Failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
