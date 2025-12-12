from __future__ import annotations

import json
import time
import logging
from pathlib import Path
from threading import Lock
from typing import TypedDict, Dict

logger = logging.getLogger(__name__)


class EnergyState(TypedDict):
    last_consume_time: float  # Timestamp of the last energy consumption
    energy_consumed: int      # How many bolts are currently "consumed" / recharging


class EnergyService:
    """
    Manages user energy (stamina).
    - Max 3 bolts.
    - Recharge 1 bolt every 20 minutes.
    - Persistent storage in JSON.
    """

    MAX_ENERGY = 3
    RECHARGE_TIME = 20 * 60  # 20 minutes in seconds

    def __init__(self, storage_path: str = None):
        if storage_path is None:
            import os
            if os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
                # Serverless environment (read-only filesystem except /tmp)
                self.storage_path = "/tmp/energy_store.json"
            else:
                self.storage_path = "data/energy_store.json"
        else:
            self.storage_path = storage_path
            
        self._lock = Lock()
        self._data: Dict[str, EnergyState] = self._load()

    def _load(self) -> Dict[str, EnergyState]:
        """Loads energy data from JSON file."""
        path = Path(self.storage_path)
        if not path.exists():
            return {}
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load energy store: {e}")
            return {}

    def _save(self):
        """Saves energy data to JSON file."""
        path = Path(self.storage_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(path, "w") as f:
                json.dump(self._data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save energy store: {e}")

    def get_status(self, address: str) -> dict:
        """
        Calculates and returns the user's current energy status.
        
        Returns:
            {
                "current_energy": int,      # 0-3
                "max_energy": int,          # 3
                "next_refill_at": float,    # Timestamp or None if full
                "seconds_to_refill": int    # Seconds remaining or 0 if full
            }
        """
        address = address.lower()
        state = self._data.get(address)

        if not state:
            return {
                "current_energy": self.MAX_ENERGY,
                "max_energy": self.MAX_ENERGY,
                "next_refill_at": None,
                "seconds_to_refill": 0
            }

        now = time.time()
        last_consume = state["last_consume_time"]
        consumed_count = state["energy_consumed"]

        if consumed_count == 0:
            return {
                "current_energy": self.MAX_ENERGY,
                "max_energy": self.MAX_ENERGY,
                "next_refill_at": None,
                "seconds_to_refill": 0
            }

        # Calculate recovered energy based on elapsed time since last consume
        # Simplified model: We track "consumed" bolts. Each bolt takes RECHARGE_TIME to recover independently?
        # OR: Linear refill from the last consumption point?
        
        # Let's use a linear refill model bucket.
        # Energy = Max - Consumed + (Elapsed / RechargeRate)
        elapsed = now - last_consume
        recovered = int(elapsed // self.RECHARGE_TIME)
        
        new_consumed = max(0, consumed_count - recovered)
        current_energy = self.MAX_ENERGY - new_consumed
        
        seconds_remaining = 0
        next_refill_at = None
        
        if current_energy < self.MAX_ENERGY:
            # Time until next single bolt recharge
            # The 'recovered' part covers full intervals. The remainder is progress towards next.
            # Example: Elapsed 300s. Recovered 0. Remainder 300s. Need 1200s. Remaining = 1200 - 300 = 900.
            progress_in_current_interval = elapsed % self.RECHARGE_TIME
            seconds_remaining = int(self.RECHARGE_TIME - progress_in_current_interval)
            next_refill_at = now + seconds_remaining

        return {
            "current_energy": current_energy,
            "max_energy": self.MAX_ENERGY,
            "next_refill_at": next_refill_at,
            "seconds_to_refill": seconds_remaining
        }

    def consume_energy(self, address: str) -> bool:
        """
        Attempts to consume 1 energy bolt.
        Returns True if successful, False if not enough energy.
        """
        with self._lock:
            address = address.lower()
            status = self.get_status(address) # This recalculates state based on time
            
            if status["current_energy"] <= 0:
                logger.warning(f"User {address} has no energy to consume.")
                return False
            
            # Update state
            # If we were full, this is the start of a drain cycle.
            # If we were partially full, we just add to the debt.
            # We need to be careful with the timestamp.
            # Ideally:
            # If full: last_consume = now, consumed = 1
            # If partial: we need to preserve the "progress" of the recharge.
            # But "progress" is tied to last_consume_time.
            # If we reset last_consume_time to 'now', we lose the credit for the time passed so far for the OTHER bolts.
            
            # Better logic based on 'virtual' bucket:
            # We calculated `new_consumed` in get_status. We should persist that first if it changed.
            
            now = time.time()
            state = self._data.get(address)
            
            if not state:
                # First time consumption
                self._data[address] = {
                    "last_consume_time": now,
                    "energy_consumed": 1
                }
                self._save()
                return True
                
            # Recalculate official drained amount based on time pass
            elapsed = now - state["last_consume_time"]
            recovered = int(elapsed // self.RECHARGE_TIME)
            current_consumed = max(0, state["energy_consumed"] - recovered)
            
            # Now consume one more
            new_consumed = current_consumed + 1
            
            # To "preserve" the partial progress of the CURRENT recharge cycle:
            # The last consume time effectively needs to move forward by 'recovered' intervals, 
            # BUT we just consumed again.
            # Actually, the simplest linear model is:
            # Refill happens at T_last + N * RechargeTime.
            # If we consume, we are just increasing the debt.
            # We shouldn't reset the timer for the *existing* debt.
            # BUT we need a reference point.
            
            # Alternative model: "Energy available at timestamp X".
            # Let's stick to the simple linear model:
            # If you perform an action, you just increment "consumed".
            # But we must update "last_consume_time" to reflect that we have "settled" the previous recovery?
            # No, if we update last_consume_time to Now, we erase the partial progress of the previous bolts.
            
            # Correct approach for linear refill:
            # If Energy was Full (Consumed=0): set last_consume = Now.
            # If Energy was NOT Full: Keep the old last_consume! 
            #   Because the "refill train" is still running from that point.
            #   We just add another passenger (bolt) to the queue (increment consumed).
            
            if current_consumed == 0:
                # Was full (or became full just now). 
                # Reset timer to start efficiently from this consumption.
                self._data[address] = {
                    "last_consume_time": now,
                    "energy_consumed": 1
                }
            else:
                # Was already draining.
                # We update the 'consumed' count to the new reality (after accounting for recovery).
                # But we keep the OLD time anchor, but we might need to shift it?
                # If we recovered 1 bolt, that means we moved 1 interval forward.
                # To keep math consistent:
                # pending_debt = old_consumed - recovered (which is what we calculated as current_consumed)
                # If we keep old_time, then (now - old_time) would still include that recovered interval!
                # So we MUST shift the time forward by (recovered * 20min) to "cash in" the recovery.
                
                time_shift = recovered * self.RECHARGE_TIME
                new_anchor_time = state["last_consume_time"] + time_shift
                
                # Check edge case: new_anchor_time shouldn't be in the future (it won't be, recovered is floor)
                
                # However, there's a trick: if we just consumed, does the timer reset? 
                # No, standard stamina systems usually have independent timers or a serial queue.
                # In a serial queue (one by one), the next bolt comes X minutes after the *previous* bolt finished refilling
                # OR X minutes after it was consumed if it was the only one.
                # The simple "Reference Time" model works if:
                # Energy = Max - CLAMP( (InitialConsumed - (Now - RefTime)/Rate) )
                
                # So:
                # 1. Calculate new pending debt (current_consumed).
                # 2. Add 1 to debt -> new_consumed.
                # 3. Update RefTime: 
                #    If we had recovery (recovered > 0), we shift RefTime forward.
                #    If we had NO recovery (recovered == 0), RefTime stays same (progress continues).
                
                self._data[address] = {
                    "last_consume_time": new_anchor_time,
                    "energy_consumed": new_consumed
                }
            
            self._save()
            logger.info(f"Consumed 1 energy for {address}. Remaining: {self.MAX_ENERGY - new_consumed}")
            return True

    def refill_energy(self, address: str, amount: int = 3) -> dict:
        """
        Refills energy for the user immediately (e.g. via specific action).
        Default amount=3 (Full Refill).
        """
        with self._lock:
            address = address.lower()
            status = self.get_status(address) # Update state first
            
            # get_status doesn't update storage unless we did something?
            # actually get_status is read-only computation usually.
            # We should probably "settle" the state first.
            
            # To settle: copy logic from consume but without adding +1.
            now = time.time()
            state = self._data.get(address)
            if not state:
                # Already full implicitly
                return self.get_status(address)
            
            elapsed = now - state["last_consume_time"]
            recovered = int(elapsed // self.RECHARGE_TIME)
            current_consumed = max(0, state["energy_consumed"] - recovered)
            
            # Apply refill
            new_consumed = max(0, current_consumed - amount)
            
            if new_consumed == 0:
                # Fully refilled
                if address in self._data:
                    del self._data[address] # Remove entry = Full Energy
            else:
                # Partially refilled
                # We need to adjust time to match the new consumed count while preserving progress?
                # Actually, if we just set 'energy_consumed' to 'new_consumed', and KEEP 'last_consume_time',
                # then 'recovered' will still be calculated as 'elapsed // 20'.
                # So effective consumed = new_consumed - recovered. 
                # This double counts the recovery!
                
                # We must "reset" the baseline.
                # Treat 'new_consumed' as the starting debt from NOW.
                # But we want to preserve partial progress of the *current* bolt?
                # If we just refilled a WHOLE bolt, we don't care about partial progress of the *previous* bolt?
                # Usually "Refill" adds +1 Bolt.
                # If I was 10 mins into refilling Bolt #2. And I get +1 Bolt.
                # Now I have Bolt #2. I am working on Bolt #3?
                # No, if I gain energy, my debt decreases.
                
                # Simplest: Reset time to NOW, and set consumed to 'new_consumed'.
                # this loses the partial progress (e.g. 10 mins) of the current recharge.
                # But for a "Share to Recharge" (Full Recharge usually), it doesn't matter.
                # If amount=3, we delete the key.
                
                # If we want to be nice and preserve progress:
                # shift time like in consume.
                
                # For now, let's just reset anchor to NOW for simplicity and robustness.
                self._data[address] = {
                    "last_consume_time": now,
                    "energy_consumed": new_consumed
                }
            
            self._save()
            logger.info(f"Refilled {amount} energy for {address}. New Consumed: {new_consumed}")
            return self.get_status(address)


# Global instance
energy_service = EnergyService()
