import json
import logging
import os
from threading import Lock

logger = logging.getLogger(__name__)

class MintHistoryService:
    """
    Tracks which casts have already been used to mint an NFT by a specific user.
    Prevents users from farming rewards with the same cast repeatedly.
    """
    def __init__(self, storage_path: str = None):
        if storage_path is None:
            if os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
                # Serverless environment (read-only filesystem except /tmp)
                self.storage_path = "/tmp/mint_history.json"
            else:
                self.storage_path = "data/mint_history.json"
        else:
            self.storage_path = storage_path
            
        self._lock = Lock()
        self._data = self._load()

    def _load(self) -> dict:
        """Loads mint history from JSON file."""
        if not os.path.exists(self.storage_path):
            return {}
        try:
            with open(self.storage_path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load mint history: {e}")
            return {}

    def _save(self):
        """Saves mint history to JSON file."""
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, "w") as f:
                json.dump(self._data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save mint history: {e}")

    def has_minted(self, address: str, cast_hash: str) -> bool:
        """Checks if the user has already minted an NFT for this cast."""
        address = address.lower()
        user_history = self._data.get(address, [])
        return cast_hash in user_history

    def record_mint(self, address: str, cast_hash: str):
        """Records a successful mint for a user and cast."""
        with self._lock:
            address = address.lower()
            if address not in self._data:
                self._data[address] = []
            
            if cast_hash not in self._data[address]:
                self._data[address].append(cast_hash)
                self._save()
                logger.info(f"Recorded mint for user {address} and cast {cast_hash}")

# Singleton instance for easy import
mint_history = MintHistoryService()
