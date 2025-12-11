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
        """Sincroniza el leaderboard con los datos on-chain y Farcaster."""
        logger.info("🔄 Iniciando Sincronización de Leaderboard desde bloque %s...", settings.deployment_block)
        
        try:
            # 1. Fetch participants from events (BLOCKING CALL -> ThreadPool)
            registry_address = settings.registry_address
            if not registry_address:
                logger.warning("⚠️ Registry address no configurado, saltando sync.")
                return

            loop = asyncio.get_running_loop()
            
            def fetch_logs_blocking():
                abi = [{"anonymous": False, "inputs": [{"indexed": True, "name": "campaignId", "type": "bytes32"}, {"indexed": True, "name": "recipient", "type": "address"}, {"indexed": False, "name": "amount", "type": "uint256"}], "name": "GrantXp", "type": "event"}]
                contract = self.w3.eth.contract(address=self.w3.to_checksum_address(registry_address), abi=abi)
                current_block = self.w3.eth.block_number
                from_block = settings.deployment_block
                return contract.events.GrantXp.get_logs(from_block=from_block, to_block=current_block)

            # Run blocking web3 call in executor with retries
            max_retries = 3
            logs = []
            
            for attempt in range(max_retries):
                try:
                    logs = await loop.run_in_executor(None, fetch_logs_blocking)
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    logger.warning(f"Error fetching logs (attempt {attempt+1}/{max_retries}): {e}. Retrying...")
                    await asyncio.sleep(2 * (attempt + 1))
            
            participants = set()
            for log in logs:
                participants.add(log["args"]["recipient"])
                
            logger.info("Found %d unique participants", len(participants))
            
            # 2. Fetch current XP balances
            xp_abi = [{"type": "function", "name": "getXpBalance", "inputs": [{"name": "campaignId", "type": "bytes32"}, {"name": "participant", "type": "address"}], "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view"}]
            xp_contract = self.w3.eth.contract(address=self.w3.to_checksum_address(registry_address), abi=xp_abi)
            campaign_id_bytes = self.w3.keccak(text="demo-campaign")

            leaderboard_data = []
            
            for i, participant in enumerate(participants):
                # Get XP (BLOCKING CALL -> ThreadPool)
                try:
                    def get_xp_blocking():
                        return xp_contract.functions.getXpBalance(campaign_id_bytes, participant).call()
                    
                    xp = await loop.run_in_executor(None, get_xp_blocking)
                except Exception as e:
                    logger.error(f"Error fetching XP for {participant}: {e}")
                    xp = 0
                
                # Get User Info (Async - Non-blocking)
                username = f"User {participant[:6]}"
                fid = None
                
                try:
                    # Parallelize Farcaster lookup or just do it fast
                    # Removed artificial delay to prevent Vercel timeout
                    fc_user = await self.farcaster.fetch_user_by_address(participant)
                    if fc_user:
                        username = fc_user.get("username")
                        fid = fc_user.get("fid")
                except Exception as e:
                    logger.warning(f"Failed to resolve Farcaster user for {participant}: {e}")
                
                entry = {
                    "address": participant,
                    "xp": xp,
                    "score": 0.0,
                    "username": username,
                    "fid": fid,
                    "campaign_id": "demo-campaign",
                    "reward_type": "xp",
                    "timestamp": int(time.time())
                }
                
                leaderboard_data.append(entry)
                # Save immediately to avoid data loss on timeout
                self.store.record(entry)
            
            logger.info("✅ Leaderboard Sync Complete. Updated %d entries.", len(leaderboard_data))
            return len(leaderboard_data)
            
        except Exception as e:
            logger.error("❌ Leaderboard Sync Failed: %s", e, exc_info=True)
            return 0
