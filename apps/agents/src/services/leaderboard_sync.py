import asyncio
import logging
import time
from web3 import Web3
from ..config import settings
from ..tools.farcaster import FarcasterToolbox
from ..stores.leaderboard import LeaderboardStore

logger = logging.getLogger(__name__)

class LeaderboardSyncer:
    def __init__(self, store: LeaderboardStore):
        self.store = store
        # Configure robust HTTP session for Web3
        import requests
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        session = requests.Session()
        retry_strategy = Retry(
            total=5,
            backoff_factor=1.0,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST", "GET"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        
        self.w3 = Web3(Web3.HTTPProvider(settings.celo_rpc_url, session=session))
        
        self.farcaster = FarcasterToolbox(
            base_url=settings.farcaster_hub_api or "https://api.neynar.com/v2",
            neynar_key=settings.neynar_api_key
        )
        
    async def sync(self):
        """Sincroniza el leaderboard con los datos on-chain y Farcaster de forma paralela."""
        logger.info("🔄 Iniciando Sincronización de Leaderboard desde bloque %s...", settings.deployment_block)
        
        try:
            registry_address = settings.registry_address
            if not registry_address:
                logger.warning("⚠️ Registry address no configurado, saltando sync.")
                return

            loop = asyncio.get_running_loop()
            current_block = self.w3.eth.block_number
            from_block = settings.deployment_block
            
            # Ensure we don't go backwards
            if from_block > current_block:
                from_block = current_block - 1000
            
            chunk_size = 10000 # Reduced chunk size for stability
            
            logger.info(f"Fetching logs from {from_block} to {current_block} (chunks of {chunk_size})")
            
            # 1. Parallel Log Fetching
            rpc_sem = asyncio.Semaphore(3) # Reduce concurrent RPC calls to avoid disconnects

            def fetch_chunk_blocking(s, e):
                # Helper for clean blocking call
                # FIX: ABI updated to match LootAccessRegistry.sol event XpGranted
                abi = [{"anonymous": False, "inputs": [{"indexed": True, "name": "campaignId", "type": "bytes32"}, {"indexed": True, "name": "participant", "type": "address"}, {"indexed": False, "name": "amount", "type": "uint32"}, {"indexed": False, "name": "newBalance", "type": "uint256"}], "name": "XpGranted", "type": "event"}]
                contract = self.w3.eth.contract(address=self.w3.to_checksum_address(registry_address), abi=abi)
                return contract.events.XpGranted.get_logs(from_block=s, to_block=e)

            async def fetch_chunk_safe(start, end):
                async with rpc_sem:
                    for attempt in range(3):
                        try:
                            # Run in thread pool
                            return await loop.run_in_executor(None, fetch_chunk_blocking, start, end)
                        except Exception as e:
                            logger.warning(f"Error fetching chunk {start}-{end} (attempt {attempt+1}): {e}")
                            await asyncio.sleep(1)
                    logger.error(f"Failed to fetch chunk {start}-{end} after retries")
                    return []

            tasks = []
            for start_block in range(from_block, current_block + 1, chunk_size):
                end_block = min(start_block + chunk_size - 1, current_block)
                tasks.append(fetch_chunk_safe(start_block, end_block))
            
            results = await asyncio.gather(*tasks)
            logs = []
            for res in results:
                logs.extend(res)
            
            participants = set()
            for log in logs:
                # FIX: Argument name is 'participant', not 'recipient'
                participants.add(log["args"]["participant"])
                
            logger.info("Found %d unique participants in blockchain history", len(participants))
            
            # 2. Parallel Participant Processing (XP + Farcaster)
            campaign_id_bytes = self.w3.keccak(text="demo-campaign")
            xp_abi = [{"type": "function", "name": "getXpBalance", "inputs": [{"name": "campaignId", "type": "bytes32"}, {"name": "participant", "type": "address"}], "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view"}]
            xp_contract = self.w3.eth.contract(address=self.w3.to_checksum_address(registry_address), abi=xp_abi)
            
            # Step 2a: Batch fetch Farcaster profiles (Optimization)
            unique_addresses = list(participants)
            logger.info("Resolving Farcaster profiles for %d users...", len(unique_addresses))
            
            users_map = {}
            try:
                users_map = await self.farcaster.fetch_users_by_addresses(unique_addresses)
                logger.info("Found %d Farcaster profiles via API", len(users_map))
            except Exception as e:
                logger.warning("Bulk user fetch failed (partial fallback will occur): %s", e)

            async def process_participant(participant):
                # Get XP (Blocking)
                xp = 0
                try:
                    def get_xp_blocking():
                        return xp_contract.functions.getXpBalance(campaign_id_bytes, participant).call()
                    # Use semaphore if RPC limits are strict, but read calls are usually fine
                    async with rpc_sem:
                         xp = await loop.run_in_executor(None, get_xp_blocking)
                except Exception as e:
                    logger.error(f"Error fetching XP for {participant}: {e}")
                
                if xp == 0:
                    return None # Solo incluir usuarios con XP > 0

                # Get Farcaster from Batch Map
                username = None
                fid = None
                
                # Check bulk map first
                if participant.lower() in users_map:
                    u = users_map[participant.lower()]
                    username = u.get("username")
                    fid = u.get("fid")
                
                # Fallback: Try individual fetch if missing and critical (optional, skip for speed)
                # We skip individual fetch to avoid 429s loop again
                
                return {
                    "address": participant,
                    "xp": xp,
                    "username": username,
                    "fid": fid,
                    "campaign_id": "demo-campaign",
                    "reward_type": "xp",
                    "timestamp": int(time.time())
                }

            # Process all users in parallel
            user_tasks = [process_participant(p) for p in participants]
            processed_entries = await asyncio.gather(*user_tasks)
            
            # Filter None and save
            leaderboard_data = [e for e in processed_entries if e is not None]
            
            # Batch record (LeaderboardStore handles sorting/limiting internally per record loop, 
            # but we can just invoke it sequentially or optimize store to accept batch. 
            # For now, sequential record is fast enough as it's just JSON manipulation)
            for entry in leaderboard_data:
                self.store.record(entry)
            
            logger.info("✅ Leaderboard Sync Complete. Updated %d active entries.", len(leaderboard_data))
            return len(leaderboard_data)
            
        except Exception as e:
            logger.error("❌ Leaderboard Sync Failed: %s", e, exc_info=True)
            return 0
