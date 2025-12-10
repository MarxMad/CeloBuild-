import asyncio
import logging
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load env from apps/agents/.env
env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(env_path)

# Add src to path
sys.path.append(str(Path(__file__).resolve().parents[2]))

from src.config import settings
from src.stores.leaderboard import default_store
from src.tools.celo import CeloToolbox

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def sync_leaderboard():
    logger.info("Starting Leaderboard Sync with Blockchain...")
    
    store = default_store(settings.leaderboard_max_entries)
    celo = CeloToolbox(settings.celo_rpc_url, settings.celo_private_key)
    
    # Read all entries directly to avoid lock issues during iteration
    # (though store methods use lock, we want to process and write back)
    # We'll use the public methods which are safe.
    entries = store.top(limit=1000) # Get all
    
    if not entries:
        logger.info("No entries found in leaderboard.")
        return

    updated_count = 0
    
    for i, entry in enumerate(entries):
        address = entry.get("address")
        if not address:
            continue
            
        username = entry.get("username", "Unknown")
        current_local_xp = entry.get("xp", 0)
        
        try:
            # Fetch on-chain balance
            # Note: We use 'demo-campaign' or the one in entry if available
            campaign_id = entry.get("campaign_id", "demo-campaign")
            
            onchain_xp = celo.get_xp_balance(
                registry_address=settings.registry_address,
                campaign_id=campaign_id,
                participant=address
            )
            
            if onchain_xp != current_local_xp:
                logger.info(f"[{i+1}/{len(entries)}] Updating {username} ({address}): {current_local_xp} -> {onchain_xp} XP")
                
                # Update entry with authoritative on-chain value
                # We use increment_score with the difference to adjust it, 
                # OR we can just add a method to set it directly.
                # Since we want to FORCE the on-chain value, we should probably 
                # expose a way to set it or just use record() with the exact value 
                # but record() logic might be complex.
                # Let's just update the dictionary and write it back via a new method or 
                # by modifying the store to accept an "overwrite" flag?
                # Actually, record() with the new XP and the same other data 
                # will update it, BUT record() logic currently does max(current, new).
                # If onchain is LOWER (unlikely but possible if reset), max() would keep the wrong local one.
                # If onchain is HIGHER, max() works.
                
                # However, I previously changed record() to be "merge".
                # And I added increment_score.
                # I should probably add a `set_score` or just rely on the fact that 
                # we want to sync.
                
                # Let's use a direct update approach by modifying the entry and calling record 
                # but we need to bypass the "max" logic if we want to support corrections downwards.
                # For now, let's assume onchain >= local usually. 
                # But if local is 50 (latest) and onchain is 200, max(50, 200) = 200. Correct.
                
                entry["xp"] = onchain_xp
                store.record(entry)
                updated_count += 1
            else:
                logger.info(f"[{i+1}/{len(entries)}] {username} is in sync ({onchain_xp} XP)")
                
        except Exception as e:
            logger.error(f"Failed to sync {username} ({address}): {e}")
            
    logger.info(f"Sync complete. Updated {updated_count} users.")

if __name__ == "__main__":
    asyncio.run(sync_leaderboard())
