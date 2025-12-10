import asyncio
import logging
import sys
import os
import json
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
from src.stores.leaderboard import default_store

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def rebuild_leaderboard():
    logger.info("🚀 Starting Leaderboard Rebuild from Blockchain Events...")
    
    # Fallback to public RPC if env var fails
    # Force HTTP for this script to avoid WSS issues with HTTPProvider
    rpc_url = "https://forno.celo.org" 
    registry_address = settings.registry_address
    
    if not registry_address:
        logger.error("Missing Registry Address")
        return

    # Initialize Web3
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    
    try:
        if not w3.is_connected():
            logger.error(f"Failed to connect to Celo RPC at {rpc_url}")
            # Try to get block number to force error
            logger.info(f"Block number: {w3.eth.block_number}")
            return
    except Exception as e:
        logger.error(f"Connection Exception: {e}")
        return

    # Event Signature: GrantXp(bytes32 indexed campaignId, address indexed participant, uint32 amount)
    # keccak256("GrantXp(bytes32,address,uint32)")
    event_signature_hash = w3.keccak(text="GrantXp(bytes32,address,uint32)").hex()
    if not event_signature_hash.startswith("0x"):
        event_signature_hash = "0x" + event_signature_hash
    
    logger.info(f"Scanning for GrantXp events on Registry: {registry_address}")
    logger.info(f"Event Topic: {event_signature_hash}")

    # Get current block
    current_block = w3.eth.block_number
    
    # Scan from deployment block (found via binary search)
    # Block: 53338074 (approx 9.2 days ago)
    from_block = 53338074
    
    participants = set()
    
    try:
        chunk_size = 2000
        found_events = 0
        
        logger.info(f"Scanning from block {from_block} to {current_block} for ANY log...")
        
        for start in range(from_block, current_block, chunk_size):
            end = min(start + chunk_size, current_block)
            
            filter_params = {
                "fromBlock": w3.to_hex(start),
                "toBlock": w3.to_hex(end),
                "address": w3.to_checksum_address(registry_address),
                # "topics": [event_signature_hash] # Remove topic filter to see all
            }
            
            logs = w3.eth.get_logs(filter_params)
            
            for log in logs:
                logger.info(f"Found log: {log['topics']}")
                # Try to match GrantXp signature manually
                if len(log["topics"]) > 0 and log["topics"][0].hex() == event_signature_hash.replace("0x", ""):
                     logger.info("MATCHED GrantXp signature!")
            
            for log in logs:
                # Extract participant address (indexed parameter 2)
                # topics[0] is signature
                # topics[1] is campaignId
                # topics[2] is participant
                if len(log["topics"]) >= 3:
                    # Decode address from bytes32 topic
                    participant_hex = "0x" + log["topics"][2].hex()[-40:]
                    participant = w3.to_checksum_address(participant_hex)
                    participants.add(participant)
                    found_events += 1
                    
        logger.info(f"Found {found_events} events. Unique participants: {len(participants)}")
        
    except Exception as e:
        logger.error(f"Error scanning logs: {e}")
        return

    if not participants:
        logger.warning("No participants found in logs.")
        return

    # Now fetch current balance for each participant
    
    # Contract ABI for getXpBalance
    abi = [
        {
            "type": "function",
            "name": "getXpBalance",
            "inputs": [
                {"name": "campaignId", "type": "bytes32"},
                {"name": "participant", "type": "address"},
            ],
            "outputs": [{"name": "", "type": "uint256"}],
            "stateMutability": "view",
        }
    ]
    contract = w3.eth.contract(address=w3.to_checksum_address(registry_address), abi=abi)
    campaign_id_bytes = w3.keccak(text="demo-campaign") 
    
    logger.info("Fetching current XP balances and Farcaster profiles...")
    
    # Initialize Farcaster Tool
    from src.tools.farcaster import FarcasterToolbox
    farcaster_tool = FarcasterToolbox(
        base_url=settings.farcaster_hub_api or "https://api.neynar.com/v2",
        neynar_key=settings.neynar_api_key
    )
    
    leaderboard_data = []
    
    for i, participant in enumerate(participants):
        # 1. Get XP
        xp = 0
        try:
            xp = contract.functions.getXpBalance(campaign_id_bytes, participant).call()
        except Exception as e:
            logger.error(f"Error fetching XP for {participant}: {e}")
            
        # 2. Get Farcaster Profile
        username = f"User {participant[:6]}"
        fid = None
        
        try:
            # Add delay to avoid rate limits
            if i > 0:
                await asyncio.sleep(0.5)
                
            fc_user = await farcaster_tool.fetch_user_by_address(participant)
            if fc_user:
                username = fc_user.get("username")
                fid = fc_user.get("fid")
                logger.info(f"✅ Resolved {participant} -> @{username} (FID: {fid})")
            else:
                logger.info(f"⚠️ No Farcaster user found for {participant}")
        except Exception as e:
            logger.warning(f"Failed to resolve Farcaster user for {participant}: {e}")

        logger.info(f"[{i+1}/{len(participants)}] {participant}: {xp} XP (@{username})")
        
        leaderboard_data.append({
            "address": participant,
            "xp": xp,
            "score": 0.0, 
            "username": username,
            "fid": fid,
            "campaign_id": "demo-campaign",
            "reward_type": "xp",
            "timestamp": int(os.times().elapsed) # Just now (using os.times().elapsed as roughly current time relative to start, but time.time() is better)
        })
        # Fix timestamp to use time.time()
        leaderboard_data[-1]["timestamp"] = int(__import__("time").time())

    # Sort by XP
    leaderboard_data.sort(key=lambda x: x["xp"], reverse=True)
    
    logger.info(f"Saving {len(leaderboard_data)} entries to leaderboard...")
    
    # Direct write to ensure clean state
    data_path = Path(__file__).resolve().parents[1] / "data" / "leaderboard.json"
    with open(data_path, "w") as f:
        json.dump(leaderboard_data, f, indent=2)
        
    logger.info("✅ Leaderboard rebuilt successfully!")

if __name__ == "__main__":
    asyncio.run(rebuild_leaderboard())
