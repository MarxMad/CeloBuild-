from __future__ import annotations

import json
import os
import shutil
import time
import logging
from pathlib import Path
from threading import Lock
from typing import TypedDict, Dict, Optional

logger = logging.getLogger(__name__)

# Try to import Upstash Redis, fallback to file storage if not available
try:
    from upstash_redis import Redis
    UPSTASH_AVAILABLE = True
except ImportError:
    UPSTASH_AVAILABLE = False
    Redis = None


class EnergyState(TypedDict):
    consumed_bolts: list[float]  # Array of timestamps when each bolt was consumed


class EnergyService:
    """
    Manages user energy (stamina).
    - Max 3 bolts.
    - Each bolt recharges independently every 60 minutes.
    - Persistent storage in JSON.
    """

    MAX_ENERGY = 3
    RECHARGE_TIME = 60 * 60  # 60 minutes in seconds

    def __init__(self, storage_path: str = None):
        self._lock = Lock()
        self._use_redis = False
        self._redis_client: Optional[Redis] = None
        
        # Try to initialize Upstash Redis if available
        if UPSTASH_AVAILABLE:
            upstash_url = os.getenv("UPSTASH_REDIS_REST_URL")
            upstash_token = os.getenv("UPSTASH_REDIS_REST_TOKEN")
            
            if upstash_url and upstash_token:
                try:
                    self._redis_client = Redis(url=upstash_url, token=upstash_token)
                    self._use_redis = True
                    logger.info("✅ [Energy] Usando Upstash Redis para persistencia")
                except Exception as e:
                    logger.warning(f"⚠️ [Energy] Error inicializando Upstash Redis: {e}. Usando almacenamiento en archivo.")
                    self._use_redis = False
            else:
                logger.info("ℹ️ [Energy] Upstash Redis no configurado. Usando almacenamiento en archivo.")
        
        # Fallback to file storage
        if not self._use_redis:
            if storage_path is None:
                if os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
                    # Serverless environment (read-only filesystem except /tmp)
                    self.storage_path = "/tmp/energy_store.json"
                else:
                    self.storage_path = "data/energy_store.json"
            else:
                self.storage_path = storage_path
            logger.info(f"📁 [Energy] Usando almacenamiento en archivo: {self.storage_path}")
            
        self._data: Dict[str, EnergyState] = self._load()

    def _load(self) -> Dict[str, EnergyState]:
        """Loads energy data from Redis or JSON file and migrates old format if needed."""
        if self._use_redis and self._redis_client:
            try:
                # Load from Redis
                redis_data = self._redis_client.get("energy:store")
                if redis_data is None:
                    logger.info("📂 [Load] ⚠️ No hay datos en Redis, retornando datos vacíos")
                    return {}
                
                # Parse JSON string
                if isinstance(redis_data, bytes):
                    redis_data = redis_data.decode('utf-8')
                data = json.loads(redis_data)
                logger.info(f"📂 [Load] ✅ Datos cargados desde Redis: {len(data)} usuarios")
                if data:
                    logger.info(f"📂 [Load] Direcciones encontradas: {list(data.keys())[:5]}...")
            except Exception as e:
                logger.error(f"❌ [Load] Error cargando desde Redis: {e}", exc_info=True)
                return {}
        else:
            # Load from file
        path = Path(self.storage_path)
        if not path.exists():
                logger.info(f"📂 [Load] ⚠️ Archivo no existe: {self.storage_path}, retornando datos vacíos")
                logger.info(f"📂 [Load] Directorio padre existe: {path.parent.exists() if path.parent else 'N/A'}")
                logger.info(f"📂 [Load] Ruta completa: {path.absolute()}")
            return {}
        try:
            with open(path, "r") as f:
                    data = json.load(f)
                logger.info(f"📂 [Load] ✅ Datos cargados desde {self.storage_path}: {len(data)} usuarios")
                if data:
                    logger.info(f"📂 [Load] Direcciones encontradas: {list(data.keys())[:5]}...")  # Primeras 5
                
                # Migrate old format to new format
                migrated = False
                for address, state in data.items():
                    if "last_consume_time" in state and "energy_consumed" in state:
                        # Old format detected - migrate to new format
                        logger.info(f"Migrating energy data for {address} from old format to new format")
                        last_consume = state["last_consume_time"]
                        consumed_count = state["energy_consumed"]
                        
                        # Convert to new format: create array of timestamps
                        # For old data, we approximate by creating timestamps spaced by RECHARGE_TIME
                        consumed_bolts = []
                        for i in range(consumed_count):
                            # Approximate: each bolt was consumed RECHARGE_TIME apart
                            bolt_time = last_consume - (i * self.RECHARGE_TIME)
                            consumed_bolts.append(bolt_time)
                        
                        data[address] = {"consumed_bolts": consumed_bolts}
                        migrated = True
                
                if migrated:
                    # Save migrated data
                    try:
                        with open(path, "w") as f:
                            json.dump(data, f, indent=2)
                        logger.info("Energy data migration completed successfully")
                    except Exception as e:
                        logger.error(f"Failed to save migrated energy data: {e}")
                
                return data
        except Exception as e:
                logger.error(f"❌ [Load] Failed to load energy store from {self.storage_path}: {e}", exc_info=True)
            return {}

    def _save(self):
        """Saves energy data to Redis or JSON file."""
        if self._use_redis and self._redis_client:
            try:
                # Save to Redis
                data_json = json.dumps(self._data)
                self._redis_client.set("energy:store", data_json)
                logger.info(f"💾 [Save] ✅ Datos guardados en Redis: {len(self._data)} usuarios")
            except Exception as e:
                logger.error(f"❌ [Save] Error guardando en Redis: {e}", exc_info=True)
        else:
            # Save to file
        path = Path(self.storage_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
                # Usar modo 'w' con flush para asegurar que se escriba inmediatamente
            with open(path, "w") as f:
                json.dump(self._data, f, indent=2)
                    f.flush()
                    import os
                    os.fsync(f.fileno())  # Forzar escritura a disco
                # Verificar que se escribió correctamente
                if path.exists():
                    file_size = path.stat().st_size
                    logger.info(f"💾 [Save] Datos guardados en {self.storage_path}: {len(self._data)} usuarios, {file_size} bytes")
                else:
                    logger.error(f"❌ [Save] ADVERTENCIA: Archivo no existe después de guardar: {self.storage_path}")
        except Exception as e:
                logger.error(f"❌ [Save] Failed to save energy store to {self.storage_path}: {e}", exc_info=True)

    def get_all_addresses(self) -> list[str]:
        """Obtiene todas las direcciones que tienen estado de energía guardado."""
        with self._lock:
            self._data = self._load()
            return list(self._data.keys())

    def get_status(self, address: str) -> dict:
        """
        Calculates and returns the user's current energy status.
        Each bolt recharges independently every 60 minutes.
        
        Returns:
            {
                "current_energy": int,      # 0-3
                "max_energy": int,          # 3
                "next_refill_at": float,    # Timestamp of next bolt recharge or None if full
                "seconds_to_refill": int,   # Seconds remaining until next bolt recharges or 0 if full
                "bolts": [                  # Información detallada de cada rayo
                    {
                        "index": int,           # 0, 1, 2
                        "available": bool,      # Si está disponible
                        "seconds_to_refill": int,  # Segundos hasta recarga (0 si está disponible)
                        "refill_at": float      # Timestamp de recarga (None si está disponible)
                    },
                    ...
                ]
            }
        """
        # CRITICAL: En serverless (Vercel), recargar datos del archivo/Redis antes de leer
        # porque cada invocación puede ser una nueva instancia
        # Esto asegura que siempre tengamos el estado más reciente
        with self._lock:
            self._data = self._load()
            logger.info(f"📖 [GetStatus] Datos cargados para {address}: {len(self._data)} usuarios en memoria")
            logger.info(f"📖 [GetStatus] Usando {'Redis' if self._use_redis else 'archivo'} para almacenamiento")
        
        address = address.lower()
        state = self._data.get(address)

        if not state or not state.get("consumed_bolts"):
            # Todos los rayos disponibles
            bolts_info = [
                {"index": i, "available": True, "seconds_to_refill": 0, "refill_at": None}
                for i in range(self.MAX_ENERGY)
            ]
            return {
                "current_energy": self.MAX_ENERGY,
                "max_energy": self.MAX_ENERGY,
                "next_refill_at": None,
                "seconds_to_refill": 0,
                "bolts": bolts_info
            }

        now = time.time()
        consumed_bolts = state.get("consumed_bolts", [])
        
        # Filter out bolts that have already recharged (elapsed >= RECHARGE_TIME)
        active_consumed = []
        for bolt_time in consumed_bolts:
            elapsed = now - bolt_time
            if elapsed < self.RECHARGE_TIME:
                active_consumed.append(bolt_time)
        
        # Update state if some bolts recharged
        if len(active_consumed) != len(consumed_bolts):
            if active_consumed:
                self._data[address] = {"consumed_bolts": active_consumed}
            else:
                # All bolts recharged, remove entry
                del self._data[address]
            self._save()
        
        current_energy = self.MAX_ENERGY - len(active_consumed)
        
        # Calculate time until next bolt recharges
        seconds_remaining = 0
        next_refill_at = None
        
        if active_consumed:
            # Find the oldest consumed bolt (will recharge first)
            oldest_bolt_time = min(active_consumed)
            elapsed = now - oldest_bolt_time
            seconds_remaining = int(self.RECHARGE_TIME - elapsed)
            next_refill_at = oldest_bolt_time + self.RECHARGE_TIME
            
            # Ensure we don't return negative time
            if seconds_remaining < 0:
                seconds_remaining = 0

        # Crear información detallada de cada rayo
        # Ordenar los rayos consumidos por tiempo (más antiguo primero)
        sorted_consumed = sorted(active_consumed)
        bolts_info = []
        
        for i in range(self.MAX_ENERGY):
            if i < len(sorted_consumed):
                # Este rayo está consumido
                bolt_time = sorted_consumed[i]
                elapsed = now - bolt_time
                seconds_to_refill = max(0, int(self.RECHARGE_TIME - elapsed))
                refill_at = bolt_time + self.RECHARGE_TIME
                bolts_info.append({
                    "index": i,
                    "available": False,
                    "seconds_to_refill": seconds_to_refill,
                    "refill_at": refill_at
                })
            else:
                # Este rayo está disponible
                bolts_info.append({
                    "index": i,
                    "available": True,
                    "seconds_to_refill": 0,
                    "refill_at": None
                })

        return {
            "current_energy": current_energy,
            "max_energy": self.MAX_ENERGY,
            "next_refill_at": next_refill_at,
            "seconds_to_refill": max(0, seconds_remaining),
            "bolts": bolts_info
        }

    def consume_energy(self, address: str) -> bool:
        """
        Attempts to consume 1 energy bolt.
        Returns True if successful, False if not enough energy.
        Each bolt recharges independently 60 minutes after it was consumed.
        """
        with self._lock:
            address = address.lower()
            
            # CRITICAL: Recargar datos del archivo ANTES de verificar estado
            # En serverless, cada invocación puede ser nueva
            self._data = self._load()
            logger.info(f"⚡ [Consume] Datos recargados: {len(self._data)} usuarios en memoria")
            
            # Calcular estado actual directamente sin modificar _data
            now = time.time()
            state = self._data.get(address)
            
            # Filtrar rayos que ya recargaron
            active_consumed = []
            if state and state.get("consumed_bolts"):
                consumed_bolts = state.get("consumed_bolts", [])
                for bolt_time in consumed_bolts:
                    elapsed = now - bolt_time
                    if elapsed < self.RECHARGE_TIME:
                        active_consumed.append(bolt_time)
            
            current_energy = self.MAX_ENERGY - len(active_consumed)
            logger.info(f"⚡ [Consume] Estado antes de consumir para {address}: {current_energy}/{self.MAX_ENERGY}")
            
            if current_energy <= 0:
                logger.warning(f"User {address} has no energy to consume.")
                return False
            
            # Actualizar estado con rayos activos (ya filtrados)
            if active_consumed:
                self._data[address] = {"consumed_bolts": active_consumed}
            else:
                # Si no hay rayos activos, eliminar entrada
                if address in self._data:
                    del self._data[address]
            
            # Agregar nuevo rayo consumido
            active_consumed.append(now)
            self._data[address] = {"consumed_bolts": active_consumed}
            logger.info(f"⚡ [Consume] Agregando timestamp {now} a consumed_bolts. Total consumidos: {len(active_consumed)}")
            
            # Guardar inmediatamente
            self._save()
            logger.info(f"⚡ [Consume] Datos guardados en {'Upstash Redis' if self._use_redis else self.storage_path}")
            
            # CRITICAL: En serverless, forzar escritura sincrónica y verificar
            try:
                # Forzar sincronización del sistema de archivos
                if hasattr(os, 'sync'):
                    os.sync()
                
                # Verificar que el archivo existe y tiene el contenido correcto
                if os.path.exists(self.storage_path):
                    with open(self.storage_path, "r") as f:
                        saved_data = json.load(f)
                        saved_state = saved_data.get(address)
                        if saved_state:
                            saved_bolts = saved_state.get("consumed_bolts", [])
                            logger.info(f"✅ [Consume] Verificación: Archivo contiene {len(saved_bolts)} bolts para {address}")
                            
                            # Verificar que el último timestamp es el que acabamos de agregar
                            if saved_bolts and abs(saved_bolts[-1] - now) < 5:  # 5 segundos de tolerancia
                                logger.info(f"✅ [Consume] Timestamp verificado: {saved_bolts[-1]} ≈ {now}")
                            else:
                                logger.warning(f"⚠️ [Consume] Timestamp no coincide: esperado {now}, encontrado {saved_bolts[-1] if saved_bolts else 'None'}")
                        else:
                            logger.error(f"❌ [Consume] ERROR CRÍTICO: No se encontró {address} en archivo después de guardar!")
                else:
                    logger.error(f"❌ [Consume] ERROR CRÍTICO: Archivo {self.storage_path} no existe después de guardar!")
            except Exception as e:
                logger.error(f"❌ [Consume] Error verificando archivo: {e}", exc_info=True)
            
            remaining = self.MAX_ENERGY - len(active_consumed)
            logger.info(f"⚡ [Consume] ✅ Consumido 1 energía para {address}. Restantes: {remaining}/{self.MAX_ENERGY}")
            return True

    def refill_energy(self, address: str, amount: int = 3) -> dict:
        """
        Refills energy for the user immediately (e.g. via specific action).
        Default amount=3 (Full Refill).
        Removes the oldest consumed bolt timestamps.
        """
        with self._lock:
            address = address.lower()
            status = self.get_status(address)  # Update state first (removes recharged bolts)
            
            state = self._data.get(address)
            if not state or not state.get("consumed_bolts"):
                # Already full
                return self.get_status(address)
            
            consumed_bolts = state.get("consumed_bolts", [])
            
            # Remove the oldest bolts (amount to refill)
            # Sort by timestamp (oldest first) and remove the first 'amount' entries
            consumed_bolts.sort()  # Oldest first
            new_consumed_bolts = consumed_bolts[amount:]  # Remove first 'amount' entries
            
            if not new_consumed_bolts:
                # Fully refilled - remove entry
                if address in self._data:
                    del self._data[address]
            else:
                # Partially refilled - keep remaining bolts
                self._data[address] = {
                    "consumed_bolts": new_consumed_bolts
                }
            
            self._save()
            remaining_consumed = len(new_consumed_bolts) if new_consumed_bolts else 0
            logger.info(f"Refilled {amount} energy for {address}. Remaining consumed bolts: {remaining_consumed}")
            return self.get_status(address)


# Global instance
energy_service = EnergyService()
