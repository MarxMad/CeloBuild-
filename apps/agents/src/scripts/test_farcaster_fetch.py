import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the project root to the python path
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../.."))

from apps.agents.src.tools.farcaster import FarcasterToolbox

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), "../../.env"))

async def main():
    api_key = os.getenv("NEYNAR_API_KEY")
    if not api_key:
        print("❌ NEYNAR_API_KEY not found in env")
        return

    print(f"🔑 API Key: {api_key[:5]}...")
    
    toolbox = FarcasterToolbox(
        base_url="https://hub.farcaster.xyz:2281",
        api_token="",
        neynar_key=api_key
    )
    
    target_fid = 744296
    print(f"\n🔍 Testing fetch_user_latest_cast for FID: {target_fid}")
    
    try:
        latest_cast = await toolbox.fetch_user_latest_cast(target_fid)
        
        if latest_cast:
            print("\n✅ Success! Cast found:")
            print(f"Text: {latest_cast.get('text')}")
            print(f"Hash: {latest_cast.get('hash')}")
            print(f"Timestamp: {latest_cast.get('timestamp')}")
        else:
            print("\n⚠️ No cast found (Returned None)")
            
    except Exception as e:
        print(f"\n❌ Exception occurred: {e}")

    # Test fallback mechanism (Recent Casts)
    print(f"\n🔍 Testing fetch_user_recent_casts directly for FID: {target_fid}")
    try:
        recent = await toolbox.fetch_user_recent_casts(target_fid, limit=5)
        print(f"Found {len(recent)} recent casts.")
        for c in recent:
            print(f"- {c.get('timestamp')}: {c.get('text')[:30]}...")
    except Exception as e:
        print(f"❌ Error in recent casts: {e}")

if __name__ == "__main__":
    asyncio.run(main())
