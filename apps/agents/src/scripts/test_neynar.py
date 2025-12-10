import asyncio
import os
import httpx
from pathlib import Path
from dotenv import load_dotenv

# Load env
env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(env_path)

NEYNAR_API_KEY = os.getenv("NEYNAR_API_KEY")

async def test_neynar():
    print(f"🔑 Testing API Key: {NEYNAR_API_KEY[:4]}...{NEYNAR_API_KEY[-4:] if NEYNAR_API_KEY else 'None'}")
    
    headers = {
        "accept": "application/json",
        "api_key": NEYNAR_API_KEY
    }
    
    async with httpx.AsyncClient() as client:
        # Test 1: Basic User Fetch (FID 3 - Vitalik)
        print("\n1️⃣  Testing Basic Endpoint (/v2/farcaster/user/bulk?fids=3)...")
        try:
            resp = await client.get("https://api.neynar.com/v2/farcaster/user/bulk?fids=3", headers=headers)
            print(f"Status: {resp.status_code}")
            if resp.status_code == 200:
                print("✅ Success! API Key is valid.")
            else:
                print(f"❌ Failed: {resp.text}")
        except Exception as e:
            print(f"❌ Error: {e}")

        # Test 2: Custody Address Fetch (The one that failed)
        print("\n2️⃣  Testing Custody Address Endpoint (/v2/farcaster/user/by_custody_address)...")
        test_address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045" # Vitalik's address
        try:
            resp = await client.get(f"https://api.neynar.com/v2/farcaster/user/by_custody_address?custody_address={test_address}", headers=headers)
            print(f"Status: {resp.status_code}")
            if resp.status_code == 200:
                print("✅ Success! Endpoint is accessible.")
            else:
                print(f"❌ Failed: {resp.text}")
                if resp.status_code == 402:
                    print("⚠️  402 Payment Required: This specific endpoint might require a higher tier plan.")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_neynar())
