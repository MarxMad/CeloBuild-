from __future__ import annotations

from dataclasses import dataclass
import json
import logging
from typing import Any
from web3 import Web3
from web3.exceptions import Web3RPCError
from web3.middleware import ExtraDataToPOAMiddleware

logger = logging.getLogger(__name__)

@dataclass
class CeloToolbox:
    """Envoltorio para consultar y escribir en contratos de Celo."""

    rpc_url: str
    private_key: str | None = None

    def __post_init__(self) -> None:
        if self.rpc_url.startswith("wss://") or self.rpc_url.startswith("ws://"):
            try:
                self.web3 = Web3(Web3.LegacyWebSocketProvider(self.rpc_url))
            except AttributeError:
                # Fallback for older web3 versions or if Legacy is not found directly
                from web3.providers.websocket import WebSocketProvider
                self.web3 = Web3(WebSocketProvider(self.rpc_url))
        else:
            self.web3 = Web3(Web3.HTTPProvider(self.rpc_url))
            
        # Inyectar middleware para compatibilidad con redes POA como Alfajores/Sepolia
        self.web3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        
        if self.private_key:
            self.account = self.web3.eth.account.from_key(self.private_key)

    def wait_for_receipt(self, tx_hash: str, timeout: int = 30) -> Any:
        """Espera a que una transacción sea minada."""
        try:
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout)
            return receipt
        except Exception as e:
            logger.warning(f"Timeout o error esperando receipt para {tx_hash}: {e}")
            return None

    def _get_gas_fees(self, multiplier: float = 1.2) -> dict:
        """
        Calcula los gas fees usando EIP-1559 (maxFeePerGas y maxPriorityFeePerGas).
        Asegura que maxFeePerGas sea mayor que el baseFee del bloque con un margen de seguridad.
        
        Args:
            multiplier: Multiplicador de seguridad para el baseFee (default 1.2 = 20% más)
        
        Returns:
            dict con 'maxFeePerGas' y 'maxPriorityFeePerGas', o 'gasPrice' si EIP-1559 no está disponible
        """
        try:
            # Obtener el bloque más reciente
            latest_block = self.web3.eth.get_block('latest')
            base_fee = latest_block.get('baseFeePerGas')
            
            if base_fee is None:
                # Si no hay baseFee, usar gasPrice legacy
                gas_price = self.web3.eth.gas_price
                logger.info(f"Usando gasPrice legacy: {gas_price}")
                return {"gasPrice": gas_price}
            
            # Calcular maxPriorityFeePerGas (tip para el minero)
            # Usar 2 gwei como tip mínimo, o 10% del baseFee, lo que sea mayor
            priority_fee = max(2_000_000_000, int(base_fee * 0.1))  # 2 gwei o 10% del baseFee
            
            # Calcular maxFeePerGas con margen de seguridad
            # maxFeePerGas debe ser >= baseFee + maxPriorityFeePerGas
            # Agregamos un multiplicador de seguridad para evitar errores
            max_fee_per_gas = int(base_fee * multiplier) + priority_fee
            
            logger.info(f"Gas fees EIP-1559: baseFee={base_fee}, priorityFee={priority_fee}, maxFee={max_fee_per_gas}")
            
            return {
                "maxFeePerGas": max_fee_per_gas,
                "maxPriorityFeePerGas": priority_fee
            }
        except Exception as e:
            # Fallback a gasPrice legacy si hay error
            logger.warning(f"Error calculando gas fees EIP-1559: {e}. Usando gasPrice legacy.")
            gas_price = self.web3.eth.gas_price
            return {"gasPrice": gas_price}

    def get_balance(self, address: str) -> float:
        """Devuelve el balance nativo en CELO."""
        wei = self.web3.eth.get_balance(address)
        return float(self.web3.from_wei(wei, "ether"))

    def checksum(self, address: str) -> str:
        """Devuelve la versión checksum de una address."""
        return self.web3.to_checksum_address(address)

    def _campaign_bytes(self, campaign_id: str) -> bytes:
        return self.web3.keccak(text=campaign_id)

    def can_claim(self, registry_address: str, campaign_id: str, participant: str) -> bool:
        """Consulta el LootAccessRegistry para validar cooldowns."""
        try:
            abi = [
                {
                    "type": "function",
                    "name": "canClaim",
                    "stateMutability": "view",
                    "inputs": [
                        {"name": "campaignId", "type": "bytes32"},
                        {"name": "participant", "type": "address"},
                    ],
                    "outputs": [{"name": "", "type": "bool"}],
                }
            ]
            contract = self.web3.eth.contract(address=self.checksum(registry_address), abi=abi)
            campaign_bytes = self._campaign_bytes(campaign_id)
            participant_checksum = self.checksum(participant)
            return bool(contract.functions.canClaim(campaign_bytes, participant_checksum).call())
        except Exception as exc:  # noqa: BLE001
            error_str = str(exc)
            # Decodificar códigos de error comunes
            if "0x050aad92" in error_str:
                logger.warning(
                    "LootAccessRegistry: Error al consultar canClaim. "
                    "Posibles causas: contrato no desplegado, dirección incorrecta, o función no disponible. "
                    "Registry: %s, Campaign: %s, Participant: %s",
                    registry_address, campaign_id, participant
                )
            else:
                logger.warning(
                    "Error consultando LootAccessRegistry (canClaim): %s. "
                    "Registry: %s, Campaign: %s",
                    exc, registry_address, campaign_id
                )
            raise

    def grant_xp(self, registry_address: str, campaign_id: str, participant: str, amount: int) -> str:
        """Invoca grantXp en el LootAccessRegistry."""
        if not self.private_key:
            raise ValueError("Private key requerida para transacciones")
        
        # Validaciones de seguridad
        if amount <= 0:
            raise ValueError("Amount debe ser mayor a 0")
        if amount > 10000:  # Límite máximo del contrato
            raise ValueError(f"Amount ({amount}) excede el límite máximo (10000)")
        
        # Validar formato de dirección
        if not participant or not participant.startswith("0x") or len(participant) != 42:
            raise ValueError(f"Dirección de participante inválida: {participant}")

        abi = [
            {
                "type": "function",
                "name": "grantXp",
                "inputs": [
                    {"name": "campaignId", "type": "bytes32"},
                    {"name": "participant", "type": "address"},
                    {"name": "amount", "type": "uint32"},
                ],
                "outputs": [],
                "stateMutability": "nonpayable",
            }
        ]
        contract = self.web3.eth.contract(address=self.checksum(registry_address), abi=abi)
        campaign_bytes = self._campaign_bytes(campaign_id)
        checksum_recipient = self.checksum(participant)

        # Reintentos robustos para manejar race conditions de nonce
        # Reintentos robustos para manejar race conditions de nonce
        max_retries = 5
        manual_nonce = None
        
        for attempt in range(max_retries):
            try:
                # Usar nonce "pending" para incluir transacciones pendientes
                # Si tenemos un manual_nonce (por error previo), usarlo. Si no, consultar red.
                if manual_nonce is not None:
                    nonce = manual_nonce
                else:
                    nonce = self.web3.eth.get_transaction_count(self.account.address, "pending")
                
                # Calcular gas fees con EIP-1559
                # Aumentar multiplicador en reintentos
                gas_multiplier = 1.2 * (1.5 ** attempt) if attempt > 0 else 1.2
                gas_fees = self._get_gas_fees(multiplier=gas_multiplier)
                if attempt > 0:
                    logger.info("Reintento XP %d/%d con gas fees aumentados", attempt + 1, max_retries)

                tx = contract.functions.grantXp(campaign_bytes, checksum_recipient, amount).build_transaction(
                    {
                        "from": self.account.address,
                        "nonce": nonce,
                        **gas_fees,  # Usar maxFeePerGas/maxPriorityFeePerGas o gasPrice
                    }
                )
                signed_tx = self.web3.eth.account.sign_transaction(tx, self.private_key)
                tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
                logger.info("XP grant transaction sent: %s", tx_hash.hex())
                return tx_hash.hex()
            
            except (ValueError, Web3RPCError) as e:
                error_msg = str(e)
                
                # Si la transacción ya es conocida, significa que ya está en el mempool.
                # Podemos asumir que se envió correctamente y devolver el hash.
                if "already known" in error_msg.lower():
                    logger.info("Transacción ya conocida en mempool, retornando hash existente.")
                    return signed_tx.hash.hex()

                is_retryable = (
                    "replacement transaction underpriced" in error_msg.lower() or 
                    "nonce too low" in error_msg.lower()
                )
                
                if is_retryable and attempt < max_retries - 1:
                    wait_time = 2 * (attempt + 1)
                    logger.warning("Transacción XP rechazada (nonce/gas), reintentando en %ds... (%s)", wait_time, error_msg)
                    import time
                    time.sleep(wait_time)
                    
                    # CRITICAL FIX: Si dice "replacement transaction underpriced", significa que hay una tx pendiente
                    # con el mismo nonce. Debemos reemplazarla con mayor gas, NO cambiar el nonce.
                    if "replacement transaction underpriced" in error_msg.lower():
                         logger.info("Detectado conflicto de nonce (replacement underpriced). Reintentando con mismo nonce y mayor gas.")
                         manual_nonce = nonce # Mantener mismo nonce
                         # Forzar un bump de gas mayor para el siguiente intento
                         # El loop ya hace bump, pero aseguramos que sea suficiente
                    else:
                        # Para otros errores, limpiar manual_nonce para volver a consultar a la red
                        manual_nonce = None
                    
                    continue
                
                # Si no es retryable o se acabaron los intentos, relanzar
                logger.error("Fallo definitivo enviando XP tras %d intentos: %s", attempt + 1, error_msg)
                raise
    
    def get_xp_balance(self, registry_address: str, campaign_id: str, participant: str) -> int:
        """Lee el balance de XP de un participante desde el contrato LootAccessRegistry."""
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
        contract = self.web3.eth.contract(address=self.checksum(registry_address), abi=abi)
        campaign_bytes = self._campaign_bytes(campaign_id)
        checksum_participant = self.checksum(participant)
        
        try:
            xp_balance = contract.functions.getXpBalance(campaign_bytes, checksum_participant).call()
            return int(xp_balance)
        except Exception as exc:
            logger.warning("Error leyendo XP balance para %s: %s", participant, exc)
            return 0


    def mint_nft(
        self,
        minter_address: str,
        campaign_id: str,
        recipient: str,
        metadata_uri: str | None = None,
    ) -> str:
        """Mintea un NFT usando el contrato LootBoxMinter."""
        if not self.private_key:
            raise ValueError("Private key requerida para transacciones")

        # ABI mínima para la función mintBatch
        # function mintBatch(bytes32 campaignId, address[] calldata recipients, string[] calldata metadataURIs, bool[] calldata soulboundFlags)
        abi = [
            {
                "type": "function",
                "name": "mintBatch",
                "inputs": [
                    {"name": "campaignId", "type": "bytes32"},
                    {"name": "recipients", "type": "address[]"},
                    {"name": "metadataURIs", "type": "string[]"},
                    {"name": "soulboundFlags", "type": "bool[]"}
                ],
                "outputs": [],
                "stateMutability": "nonpayable"
            }
        ]

        contract = self.web3.eth.contract(address=self.checksum(minter_address), abi=abi)
        campaign_bytes = self._campaign_bytes(campaign_id)
        
        # Asegurar checksum de la dirección
        try:
            checksum_recipient = self.checksum(recipient)
        except ValueError:
             # Si falla la validación, lanzamos error claro
             raise ValueError(f"Dirección inválida: {recipient}")

        # Construir transacción
        metadata_uri = metadata_uri or "ipfs://QmExample"
        
        # Reintentos robustos para manejar race conditions de nonce
        max_retries = 5
        manual_nonce = None
        
        for attempt in range(max_retries):
            try:
                # Usar nonce "pending" para incluir transacciones pendientes
                if manual_nonce is not None:
                    nonce = manual_nonce
                else:
                    nonce = self.web3.eth.get_transaction_count(self.account.address, "pending")
                
                # Calcular gas fees con EIP-1559
                # Aumentar multiplicador en reintentos
                gas_multiplier = 1.2 * (1.5 ** attempt) if attempt > 0 else 1.2
                gas_fees = self._get_gas_fees(multiplier=gas_multiplier)
                if attempt > 0:
                    logger.info("Reintento NFT %d/%d con gas fees aumentados", attempt + 1, max_retries)

                tx = contract.functions.mintBatch(
                    campaign_bytes,
                    [checksum_recipient],
                    [metadata_uri],
                    [False] # Transferible
                ).build_transaction({
                    "from": self.account.address,
                    "nonce": nonce,
                    **gas_fees,  # Usar maxFeePerGas/maxPriorityFeePerGas o gasPrice
                })

                # Firmar y enviar
                signed_tx = self.web3.eth.account.sign_transaction(tx, self.private_key)
                tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
                
                logger.info(f"NFT mint transaction sent: {tx_hash.hex()}")
                return tx_hash.hex()
            
            except Exception as exc:  # noqa: BLE001
                error_str = str(exc)
                
                # Handle "already known" (transaction already in mempool)
                if "already known" in error_str.lower():
                    logger.info("Transacción NFT ya conocida en mempool, retornando hash existente.")
                    # En este punto signed_tx ya está definido si falló en send_raw_transaction
                    if 'signed_tx' in locals():
                        return signed_tx.hash.hex()
                    else:
                        # Si falló antes de firmar (raro para already known), no podemos recuperar el hash
                        raise

                is_retryable = (
                    "replacement transaction underpriced" in error_str.lower() or 
                    "nonce too low" in error_str.lower()
                )
                
                if is_retryable and attempt < max_retries - 1:
                    wait_time = 2 * (attempt + 1)
                    logger.warning("Transacción NFT rechazada (nonce/gas), reintentando en %ds... (%s)", wait_time, error_str)
                    import time
                    time.sleep(wait_time)
                    
                    if "replacement transaction underpriced" in error_str.lower():
                         logger.info("Detectado conflicto de nonce en NFT. Reintentando con mismo nonce y mayor gas.")
                         manual_nonce = nonce # Mantener mismo nonce
                    else:
                        manual_nonce = None
                    
                    continue
                    
                logger.error(f"FULL ERROR MINTING NFT: {error_str}")
                # Decodificar códigos de error comunes
                if "0x477a3e50" in error_str:
                    logger.error(
                        "LootBoxMinter: Error al mintear NFT. "
                        "Posibles causas: contrato no desplegado, dirección incorrecta, falta de permisos (minter role), "
                        "o campaña no configurada. Minter: %s, Campaign: %s, Recipient: %s",
                        minter_address, campaign_id, recipient
                    )
                elif "0x050aad92" in error_str:
                    logger.error(
                        "LootBoxMinter: Error de acceso o permisos. "
                        "Verifica que la cuenta tenga el rol 'minter' en el contrato. "
                        "Minter: %s, Campaign: %s",
                        minter_address, campaign_id
                    )
                raise


    def distribute_cusd(
        self,
        vault_address: str,
        campaign_id: str,
        recipients: list[str],
        token_address: str | None = None,
    ) -> str:
        """Distribuye cUSD usando el contrato LootBoxVault como alternativa a MiniPay Tool API."""
        if not self.private_key:
            raise ValueError("Private key requerida para transacciones")
        if not recipients:
            raise ValueError("Lista de recipients vacía")

        # ABI para distributeERC20
        abi = [
            {
                "type": "function",
                "name": "distributeERC20",
                "inputs": [
                    {"name": "campaignId", "type": "bytes32"},
                    {"name": "recipients", "type": "address[]"},
                ],
                "outputs": [],
                "stateMutability": "nonpayable",
            }
        ]

        contract = self.web3.eth.contract(address=self.checksum(vault_address), abi=abi)
        campaign_bytes = self._campaign_bytes(campaign_id)
        checksum_recipients = [self.checksum(r) for r in recipients]

        # Usar nonce "pending" para incluir transacciones pendientes
        nonce = self.web3.eth.get_transaction_count(self.account.address, "pending")
        gas_fees = self._get_gas_fees(multiplier=1.2)
        tx = contract.functions.distributeERC20(campaign_bytes, checksum_recipients).build_transaction(
            {
                "from": self.account.address,
                "nonce": nonce,
                **gas_fees,  # Usar maxFeePerGas/maxPriorityFeePerGas o gasPrice
            }
        )

        signed_tx = self.web3.eth.account.sign_transaction(tx, self.private_key)
        tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        logger.info("cUSD distribution transaction sent: %s", tx_hash.hex())
        return tx_hash.hex()

    def configure_campaign_registry(self, registry_address: str, campaign_id: str, cooldown_seconds: int = 86400) -> str:
        """Configura una campaña en LootAccessRegistry si no existe."""
        if not self.private_key:
            raise ValueError("Private key requerida para transacciones")
        
        abi = [
            {
                "type": "function",
                "name": "configureCampaign",
                "inputs": [
                    {"name": "campaignId", "type": "bytes32"},
                    {"name": "cooldownSeconds", "type": "uint64"},
                ],
                "outputs": [],
                "stateMutability": "nonpayable",
            }
        ]
        
        contract = self.web3.eth.contract(address=self.checksum(registry_address), abi=abi)
        campaign_bytes = self._campaign_bytes(campaign_id)
        
        # Obtener nonce con manejo de errores
        # Usar nonce "pending" para incluir transacciones pendientes
        nonce = self.web3.eth.get_transaction_count(self.account.address, "pending")
        
        # Si hay transacciones pendientes, aumentar multiplicador de gas
        confirmed_nonce = self.web3.eth.get_transaction_count(self.account.address)
        gas_multiplier = 1.4 if nonce > confirmed_nonce else 1.2
        if nonce > confirmed_nonce:
            logger.warning(
                "Transacciones pendientes detectadas (nonce: %s -> %s), usando gas fees aumentados",
                confirmed_nonce, nonce
            )
        
        try:
            gas_fees = self._get_gas_fees(multiplier=gas_multiplier)
            tx = contract.functions.configureCampaign(campaign_bytes, cooldown_seconds).build_transaction({
                "from": self.account.address,
                "nonce": nonce,
                **gas_fees,
            })
            
            signed_tx = self.web3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            logger.info("Campaign configured in Registry: %s (tx: %s)", campaign_id, tx_hash.hex())
            # Esperar confirmación para evitar race conditions
            self.web3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
            return tx_hash.hex()
        except ValueError as e:
            error_msg = str(e)
            if "replacement transaction underpriced" in error_msg.lower() or "max fee per gas" in error_msg.lower():
                # Reintentar con gas fees aún más altos
                logger.warning("Transacción rechazada por gas fees bajos, reintentando con fees más altos...")
                gas_fees = self._get_gas_fees(multiplier=1.8)
                tx = contract.functions.configureCampaign(campaign_bytes, cooldown_seconds).build_transaction({
                    "from": self.account.address,
                    "nonce": nonce,
                    **gas_fees,
                })
                signed_tx = self.web3.eth.account.sign_transaction(tx, self.private_key)
                tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
                logger.info("Campaign configured in Registry (retry): %s (tx: %s)", campaign_id, tx_hash.hex())
                # Esperar confirmación
                self.web3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
                return tx_hash.hex()
            raise

    def configure_campaign_minter(self, minter_address: str, campaign_id: str, base_uri: str = "ipfs://QmExample/") -> str:
        """Configura una campaña en LootBoxMinter si no existe."""
        if not self.private_key:
            raise ValueError("Private key requerida para transacciones")
        
        abi = [
            {
                "type": "function",
                "name": "configureCampaign",
                "inputs": [
                    {"name": "campaignId", "type": "bytes32"},
                    {"name": "baseURI", "type": "string"},
                ],
                "outputs": [],
                "stateMutability": "nonpayable",
            }
        ]
        
        contract = self.web3.eth.contract(address=self.checksum(minter_address), abi=abi)
        campaign_bytes = self._campaign_bytes(campaign_id)
        
        # Obtener nonce con manejo de errores
        # Usar nonce "pending" para incluir transacciones pendientes
        nonce = self.web3.eth.get_transaction_count(self.account.address, "pending")
        
        # Si hay transacciones pendientes, aumentar multiplicador de gas
        confirmed_nonce = self.web3.eth.get_transaction_count(self.account.address)
        gas_multiplier = 1.4 if nonce > confirmed_nonce else 1.2
        if nonce > confirmed_nonce:
            logger.warning(
                "Transacciones pendientes detectadas (nonce: %s -> %s), usando gas fees aumentados",
                confirmed_nonce, nonce
            )
        
        try:
            gas_fees = self._get_gas_fees(multiplier=gas_multiplier)
            tx = contract.functions.configureCampaign(campaign_bytes, base_uri).build_transaction({
                "from": self.account.address,
                "nonce": nonce,
                **gas_fees,
            })
            
            signed_tx = self.web3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            logger.info("Campaign configured in Minter: %s (tx: %s)", campaign_id, tx_hash.hex())
            # Esperar confirmación para evitar race conditions
            self.web3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
            return tx_hash.hex()
        except ValueError as e:
            error_msg = str(e)
            if "replacement transaction underpriced" in error_msg.lower() or "nonce too low" in error_msg.lower() or "max fee per gas" in error_msg.lower():
                # Reintentar con gas fees aún más altos y actualizar nonce
                logger.warning("Transacción rechazada (gas fees bajos o nonce), reintentando...")
                # Actualizar nonce por si acaso
                nonce = self.web3.eth.get_transaction_count(self.account.address, "pending")
                gas_fees = self._get_gas_fees(multiplier=1.8)
                tx = contract.functions.configureCampaign(campaign_bytes, base_uri).build_transaction({
                    "from": self.account.address,
                    "nonce": nonce,
                    **gas_fees,
                })
                signed_tx = self.web3.eth.account.sign_transaction(tx, self.private_key)
                tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
                logger.info("Campaign configured in Minter (retry): %s (tx: %s)", campaign_id, tx_hash.hex())
                # Esperar confirmación
                self.web3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
                return tx_hash.hex()
            raise

    def initialize_campaign_vault(
        self,
        vault_address: str,
        campaign_id: str,
        token_address: str,
        reward_per_recipient: int,  # En wei (ej: 0.15 * 1e18 para 0.15 cUSD)
    ) -> str:
        """Inicializa una campaña en LootBoxVault si no existe."""
        if not self.private_key:
            raise ValueError("Private key requerida para transacciones")
        
        # Validaciones de seguridad
        if reward_per_recipient <= 0:
            raise ValueError("reward_per_recipient debe ser mayor a 0")
        
        # Límite máximo: 10,000 tokens (10,000 * 1e18 wei)
        max_reward = 10000 * 10**18
        if reward_per_recipient > max_reward:
            raise ValueError(f"reward_per_recipient ({reward_per_recipient}) excede el límite máximo ({max_reward})")
        
        # Validar formato de direcciones
        if not token_address or not token_address.startswith("0x") or len(token_address) != 42:
            raise ValueError(f"Dirección de token inválida: {token_address}")
        
        abi = [
            {
                "type": "function",
                "name": "initializeCampaign",
                "inputs": [
                    {"name": "campaignId", "type": "bytes32"},
                    {"name": "token", "type": "address"},
                    {"name": "rewardPerRecipient", "type": "uint96"},
                ],
                "outputs": [],
                "stateMutability": "nonpayable",
            }
        ]
        
        contract = self.web3.eth.contract(address=self.checksum(vault_address), abi=abi)
        campaign_bytes = self._campaign_bytes(campaign_id)
        token_checksum = self.checksum(token_address)
        
        # Usar nonce "pending" para incluir transacciones pendientes
        nonce = self.web3.eth.get_transaction_count(self.account.address, "pending")
        
        # Si hay transacciones pendientes, aumentar multiplicador de gas
        confirmed_nonce = self.web3.eth.get_transaction_count(self.account.address)
        gas_multiplier = 1.4 if nonce > confirmed_nonce else 1.2
        if nonce > confirmed_nonce:
            logger.warning(
                "Transacciones pendientes detectadas (nonce: %s -> %s), usando gas fees aumentados",
                confirmed_nonce, nonce
            )
        
        try:
            gas_fees = self._get_gas_fees(multiplier=gas_multiplier)
            tx = contract.functions.initializeCampaign(
                campaign_bytes,
                token_checksum,
                reward_per_recipient
            ).build_transaction({
                "from": self.account.address,
                "nonce": nonce,
                **gas_fees,
            })
            
            signed_tx = self.web3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            logger.info(
                "Campaign initialized in Vault: %s (token: %s, reward: %s wei) (tx: %s)",
                campaign_id, token_address, reward_per_recipient, tx_hash.hex()
            )
            # Esperar confirmación para evitar race conditions
            self.web3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
            return tx_hash.hex()
        except (ValueError, Exception) as e:  # noqa: BLE001
            error_msg = str(e)
            error_repr = repr(e)
            
            # Detectar si la campaña ya está inicializada
            # El contrato revierte con InvalidInput() cuando campaign.token != address(0)
            # Esto puede aparecer como diferentes formatos de error
            is_already_initialized = (
                "0xb4fa3fb3" in error_msg or 
                "0xb4fa3fb3" in error_repr or
                "CampaignAlreadyInitialized" in error_msg or 
                "already initialized" in error_msg.lower() or
                "InvalidInput" in error_msg or
                ("execution reverted" in error_msg.lower() and "0xb4fa3fb3" in error_repr)
            )
            
            if is_already_initialized:
                logger.debug("Campaña %s ya está inicializada en LootBoxVault (esto es normal)", campaign_id)
                # Lanzar error específico para que el caller lo maneje silenciosamente
                raise ValueError(f"Campaign {campaign_id} already initialized in Vault") from e
            elif "replacement transaction underpriced" in error_msg.lower() or "nonce too low" in error_msg.lower() or "max fee per gas" in error_msg.lower():
                # Reintentar con gas fees más altos
                logger.warning("Transacción rechazada (gas fees bajos o nonce), reintentando...")
                nonce = self.web3.eth.get_transaction_count(self.account.address, "pending")
                gas_fees = self._get_gas_fees(multiplier=1.8)
                tx = contract.functions.initializeCampaign(
                    campaign_bytes,
                    token_checksum,
                    reward_per_recipient
                ).build_transaction({
                    "from": self.account.address,
                    "nonce": nonce,
                    **gas_fees,
                })
                signed_tx = self.web3.eth.account.sign_transaction(tx, self.private_key)
                tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
                logger.info("Campaign initialized in Vault (retry): %s (tx: %s)", campaign_id, tx_hash.hex())
                # Esperar confirmación
                self.web3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
                return tx_hash.hex()
            raise

