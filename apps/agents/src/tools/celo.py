from __future__ import annotations

from dataclasses import dataclass
import json
import logging
from typing import Any
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware

logger = logging.getLogger(__name__)

@dataclass
class CeloToolbox:
    """Envoltorio para consultar y escribir en contratos de Celo."""

    rpc_url: str
    private_key: str | None = None

    def __post_init__(self) -> None:
        self.web3 = Web3(Web3.HTTPProvider(self.rpc_url))
        # Inyectar middleware para compatibilidad con redes POA como Alfajores/Sepolia
        self.web3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        
        if self.private_key:
            self.account = self.web3.eth.account.from_key(self.private_key)

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

        try:
            # Usar nonce "pending" para incluir transacciones pendientes
            nonce = self.web3.eth.get_transaction_count(self.account.address, "pending")
            tx = contract.functions.grantXp(campaign_bytes, checksum_recipient, amount).build_transaction(
                {
                    "from": self.account.address,
                    "nonce": nonce,
                    "gasPrice": self.web3.eth.gas_price,
                }
            )
            signed_tx = self.web3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            logger.info("XP grant transaction sent: %s", tx_hash.hex())
            return tx_hash.hex()
        except ValueError as e:
            error_msg = str(e)
            if "replacement transaction underpriced" in error_msg.lower() or "nonce too low" in error_msg.lower():
                # Reintentar con gas price más alto y actualizar nonce
                logger.warning("Transacción XP rechazada (gas/nonce), reintentando...")
                import time
                time.sleep(2) # Esperar propagación
                
                nonce = self.web3.eth.get_transaction_count(self.account.address, "pending")
                gas_price = int(self.web3.eth.gas_price * 1.5)
                
                tx = contract.functions.grantXp(campaign_bytes, checksum_recipient, amount).build_transaction(
                    {
                        "from": self.account.address,
                        "nonce": nonce,
                        "gasPrice": gas_price,
                    }
                )
                signed_tx = self.web3.eth.account.sign_transaction(tx, self.private_key)
                tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
                logger.info("XP grant transaction sent (retry): %s", tx_hash.hex())
                return tx_hash.hex()
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
        
        try:
            # Usar nonce "pending" para incluir transacciones pendientes
            nonce = self.web3.eth.get_transaction_count(self.account.address, "pending")
            tx = contract.functions.mintBatch(
                campaign_bytes,
                [checksum_recipient],
                [metadata_uri],
                [False] # Transferible
            ).build_transaction({
                "from": self.account.address,
                "nonce": nonce,
                "gasPrice": self.web3.eth.gas_price,
            })

            # Firmar y enviar
            signed_tx = self.web3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            
            logger.info(f"NFT mint transaction sent: {tx_hash.hex()}")
            return tx_hash.hex()
            raise
        except Exception as exc:  # noqa: BLE001
            error_str = str(exc)
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
            else:
                logger.error(
                    "Error al mintear NFT: %s. Minter: %s, Campaign: %s, Recipient: %s",
                    exc, minter_address, campaign_id, recipient
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
        tx = contract.functions.distributeERC20(campaign_bytes, checksum_recipients).build_transaction(
            {
                "from": self.account.address,
                "nonce": nonce,
                "gasPrice": self.web3.eth.gas_price,
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
        
        # Obtener nonce y gas price con manejo de errores
        # Usar nonce "pending" para incluir transacciones pendientes
        nonce = self.web3.eth.get_transaction_count(self.account.address, "pending")
        base_gas_price = self.web3.eth.gas_price
        
        # Si hay transacciones pendientes, aumentar gas price para priorizar
        confirmed_nonce = self.web3.eth.get_transaction_count(self.account.address)
        if nonce > confirmed_nonce:
            # Hay transacciones pendientes, aumentar gas price en 20%
            gas_price = int(base_gas_price * 1.2)
            logger.warning(
                "Transacciones pendientes detectadas (nonce: %s -> %s), usando gas price aumentado: %s",
                confirmed_nonce, nonce, gas_price
            )
        else:
            gas_price = base_gas_price
        
        try:
            tx = contract.functions.configureCampaign(campaign_bytes, cooldown_seconds).build_transaction({
                "from": self.account.address,
                "nonce": nonce,
                "gasPrice": gas_price,
            })
            
            signed_tx = self.web3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            logger.info("Campaign configured in Registry: %s (tx: %s)", campaign_id, tx_hash.hex())
            return tx_hash.hex()
        except ValueError as e:
            error_msg = str(e)
            if "replacement transaction underpriced" in error_msg.lower():
                # Reintentar con gas price aún más alto
                logger.warning("Transacción rechazada por gas price bajo, reintentando con precio más alto...")
                gas_price = int(base_gas_price * 1.5)
                tx = contract.functions.configureCampaign(campaign_bytes, cooldown_seconds).build_transaction({
                    "from": self.account.address,
                    "nonce": nonce,
                    "gasPrice": gas_price,
                })
                signed_tx = self.web3.eth.account.sign_transaction(tx, self.private_key)
                tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
                logger.info("Campaign configured in Registry (retry): %s (tx: %s)", campaign_id, tx_hash.hex())
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
        
        # Obtener nonce y gas price con manejo de errores
        # Usar nonce "pending" para incluir transacciones pendientes
        nonce = self.web3.eth.get_transaction_count(self.account.address, "pending")
        base_gas_price = self.web3.eth.gas_price
        
        # Si hay transacciones pendientes, aumentar gas price para priorizar
        confirmed_nonce = self.web3.eth.get_transaction_count(self.account.address)
        if nonce > confirmed_nonce:
            # Hay transacciones pendientes, aumentar gas price en 20%
            gas_price = int(base_gas_price * 1.2)
            logger.warning(
                "Transacciones pendientes detectadas (nonce: %s -> %s), usando gas price aumentado: %s",
                confirmed_nonce, nonce, gas_price
            )
        else:
            gas_price = base_gas_price
        
        try:
            tx = contract.functions.configureCampaign(campaign_bytes, base_uri).build_transaction({
                "from": self.account.address,
                "nonce": nonce,
                "gasPrice": gas_price,
            })
            
            signed_tx = self.web3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            logger.info("Campaign configured in Minter: %s (tx: %s)", campaign_id, tx_hash.hex())
            return tx_hash.hex()
        except ValueError as e:
            error_msg = str(e)
            if "replacement transaction underpriced" in error_msg.lower() or "nonce too low" in error_msg.lower():
                # Reintentar con gas price aún más alto y actualizar nonce
                logger.warning("Transacción rechazada (gas price bajo o nonce), reintentando...")
                # Actualizar nonce por si acaso
                nonce = self.web3.eth.get_transaction_count(self.account.address, "pending")
                gas_price = int(base_gas_price * 1.5)
                tx = contract.functions.configureCampaign(campaign_bytes, base_uri).build_transaction({
                    "from": self.account.address,
                    "nonce": nonce,
                    "gasPrice": gas_price,
                })
                signed_tx = self.web3.eth.account.sign_transaction(tx, self.private_key)
                tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
                logger.info("Campaign configured in Minter (retry): %s (tx: %s)", campaign_id, tx_hash.hex())
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
        base_gas_price = self.web3.eth.gas_price
        
        # Si hay transacciones pendientes, aumentar gas price
        confirmed_nonce = self.web3.eth.get_transaction_count(self.account.address)
        if nonce > confirmed_nonce:
            gas_price = int(base_gas_price * 1.2)
            logger.warning(
                "Transacciones pendientes detectadas (nonce: %s -> %s), usando gas price aumentado: %s",
                confirmed_nonce, nonce, gas_price
            )
        else:
            gas_price = base_gas_price
        
        try:
            tx = contract.functions.initializeCampaign(
                campaign_bytes,
                token_checksum,
                reward_per_recipient
            ).build_transaction({
                "from": self.account.address,
                "nonce": nonce,
                "gasPrice": gas_price,
            })
            
            signed_tx = self.web3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            logger.info(
                "Campaign initialized in Vault: %s (token: %s, reward: %s wei) (tx: %s)",
                campaign_id, token_address, reward_per_recipient, tx_hash.hex()
            )
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
            elif "replacement transaction underpriced" in error_msg.lower() or "nonce too low" in error_msg.lower():
                # Reintentar con gas price más alto
                logger.warning("Transacción rechazada (gas price bajo o nonce), reintentando...")
                nonce = self.web3.eth.get_transaction_count(self.account.address, "pending")
                gas_price = int(base_gas_price * 1.5)
                tx = contract.functions.initializeCampaign(
                    campaign_bytes,
                    token_checksum,
                    reward_per_recipient
                ).build_transaction({
                    "from": self.account.address,
                    "nonce": nonce,
                    "gasPrice": gas_price,
                })
                signed_tx = self.web3.eth.account.sign_transaction(tx, self.private_key)
                tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
                logger.info("Campaign initialized in Vault (retry): %s (tx: %s)", campaign_id, tx_hash.hex())
                return tx_hash.hex()
            raise

