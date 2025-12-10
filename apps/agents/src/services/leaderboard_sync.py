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
        self.w3 = Web3(Web3.HTTPProvider(settings.celo_rpc_url))
        self.farcaster = FarcasterToolbox(neynar_key=settings.neynar_api_key)
        
    async def sync(self):
        """Sincroniza el leaderboard con los datos on-chain y Farcaster."""
        logger.info("🔄 Iniciando Sincronización de Leaderboard desde bloque %s...", settings.deployment_block)
        
        try:
            # 1. Fetch participants from events
            registry_address = settings.registry_address
            if not registry_address:
                logger.warning("⚠️ Registry address no configurado, saltando sync.")
                return

            abi = [{"anonymous": False, "inputs": [{"indexed": True, "name": "campaignId", "type": "bytes32"}, {"indexed": True, "name": "recipient", "type": "address"}, {"indexed": False, "name": "amount", "type": "uint256"}], "name": "GrantXp", "type": "event"}]
            contract = self.w3.eth.contract(address=self.w3.to_checksum_address(registry_address), abi=abi)
            
            current_block = self.w3.eth.block_number
            from_block = settings.deployment_block
            
            # Fetch logs
            # TODO: Pagination if range is too large, but for 160k blocks it should be fine on Celo
            logs = contract.events.GrantXp.get_logs(fromBlock=from_block, toBlock=current_block)
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
                # Get XP
                try:
                    xp = xp_contract.functions.getXpBalance(campaign_id_bytes, participant).call()
                except Exception as e:
                    logger.error(f"Error fetching XP for {participant}: {e}")
                    xp = 0
                
                # Get User Info
                username = f"User {participant[:6]}"
                fid = None
                
                try:
                    # Add small delay to be nice to API even with bulk endpoint
                    if i > 0:
                        await asyncio.sleep(0.2)
                        
                    fc_user = await self.farcaster.fetch_user_by_address(participant)
                    if fc_user:
                        username = fc_user.get("username")
                        fid = fc_user.get("fid")
                except Exception as e:
                    logger.warning(f"Failed to resolve Farcaster user for {participant}: {e}")
                
                leaderboard_data.append({
                    "address": participant,
                    "xp": xp,
                    "score": 0.0,
                    "username": username,
                    "fid": fid,
                    "campaign_id": "demo-campaign",
                    "reward_type": "xp",
                    "timestamp": int(time.time())
                })
            
            # 3. Update Store
            # We iterate and record each one to merge/update
            for entry in leaderboard_data:
                self.store.record(entry)
                
            logger.info("✅ Leaderboard Sync Complete. Updated %d entries.", len(leaderboard_data))
            return len(leaderboard_data)
            
        except Exception as e:
            logger.error("❌ Leaderboard Sync Failed: %s", e, exc_info=True)
            return 0
