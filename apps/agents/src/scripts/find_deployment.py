import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware

# Load env
env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(env_path)

# Add src to path
sys.path.append(str(Path(__file__).resolve().parents[2]))

from src.config import settings

async def find_deployment_block():
    rpc_url = "https://forno.celo.org"
    registry_address = settings.registry_address
    
    if not registry_address:
        print("❌ No REGISTRY_ADDRESS in .env")
        return

    print(f"🔍 Finding deployment block for {registry_address}...")
    
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    
    if not w3.is_connected():
        print("❌ Failed to connect to RPC")
        return

    current_block = w3.eth.block_number
    print(f"Current block: {current_block}")
    
    # Binary search
    low = 0
    high = current_block
    deployment_block = None
    
    while low <= high:
        mid = (low + high) // 2
        code = w3.eth.get_code(w3.to_checksum_address(registry_address), block_identifier=mid)
        
        if len(code) > 0: # Code exists
            deployment_block = mid
            high = mid - 1 # Try earlier
        else: # No code
            low = mid + 1 # Try later
            
        print(f"Checking block {mid}: {'Code found' if len(code) > 0 else 'No code'}")
        
    if deployment_block:
        print(f"\n✅ Contract deployed at (or around) block: {deployment_block}")
        print(f"   Approx age: {(current_block - deployment_block) * 5 / 86400:.1f} days")
    else:
        print("\n❌ Could not find deployment block")

if __name__ == "__main__":
    asyncio.run(find_deployment_block())
