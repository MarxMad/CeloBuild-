import asyncio
import os
import httpx
from pathlib import Path
from dotenv import load_dotenv

# Load env
env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(env_path)

NEYNAR_API_KEY = os.getenv("NEYNAR_API_KEY")

async def test_neynar_bulk():
    print(f"🔑 Testing API Key with bulk-by-address...")
    
    headers = {
        "accept": "application/json",
        "api_key": NEYNAR_API_KEY
    }
    
    async with httpx.AsyncClient() as client:
        # Test bulk-by-address with Vitalik's address
        test_address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045" 
        print(f"\nTesting /v2/farcaster/user/bulk-by-address?addresses={test_address}...")
        
        try:
            resp = await client.get(f"https://api.neynar.com/v2/farcaster/user/bulk-by-address?addresses={test_address}", headers=headers)
            print(f"Status: {resp.status_code}")
            if resp.status_code == 200:
                print("✅ Success! Response:")
                print(resp.text[:500])
            else:
                print(f"❌ Failed: {resp.text}")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_neynar_bulk())
