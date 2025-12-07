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
        contract = self.web3.eth.contract(address=registry_address, abi=abi)
        campaign_bytes = self._campaign_bytes(campaign_id)
        participant_checksum = self.checksum(participant)
        return bool(contract.functions.canClaim(campaign_bytes, participant_checksum).call())

    def grant_xp(self, registry_address: str, campaign_id: str, participant: str, amount: int) -> str:
        """Invoca grantXp en el LootAccessRegistry."""
        if not self.private_key:
            raise ValueError("Private key requerida para transacciones")
        if amount <= 0:
            raise ValueError("XP amount inválido")

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
        contract = self.web3.eth.contract(address=registry_address, abi=abi)
        campaign_bytes = self._campaign_bytes(campaign_id)
        checksum_recipient = self.checksum(participant)

        tx = contract.functions.grantXp(campaign_bytes, checksum_recipient, amount).build_transaction(
            {
                "from": self.account.address,
                "nonce": self.web3.eth.get_transaction_count(self.account.address),
                "gasPrice": self.web3.eth.gas_price,
            }
        )
        signed_tx = self.web3.eth.account.sign_transaction(tx, self.private_key)
        tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        logger.info("XP grant transaction sent: %s", tx_hash.hex())
        return tx_hash.hex()

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

        contract = self.web3.eth.contract(address=minter_address, abi=abi)
        campaign_bytes = self._campaign_bytes(campaign_id)
        
        # Asegurar checksum de la dirección
        try:
            checksum_recipient = self.checksum(recipient)
        except ValueError:
             # Si falla la validación, lanzamos error claro
             raise ValueError(f"Dirección inválida: {recipient}")

        # Construir transacción
        metadata_uri = metadata_uri or "ipfs://QmExample"
        
        tx = contract.functions.mintBatch(
            campaign_bytes,
            [checksum_recipient],
            [metadata_uri],
            [False] # Transferible
        ).build_transaction({
            "from": self.account.address,
            "nonce": self.web3.eth.get_transaction_count(self.account.address),
            "gasPrice": self.web3.eth.gas_price,
        })

        # Firmar y enviar
        signed_tx = self.web3.eth.account.sign_transaction(tx, self.private_key)
        tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        logger.info(f"NFT mint transaction sent: {tx_hash.hex()}")
        return tx_hash.hex()

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

        contract = self.web3.eth.contract(address=vault_address, abi=abi)
        campaign_bytes = self._campaign_bytes(campaign_id)
        checksum_recipients = [self.checksum(r) for r in recipients]

        tx = contract.functions.distributeERC20(campaign_bytes, checksum_recipients).build_transaction(
            {
                "from": self.account.address,
                "nonce": self.web3.eth.get_transaction_count(self.account.address),
                "gasPrice": self.web3.eth.gas_price,
            }
        )

        signed_tx = self.web3.eth.account.sign_transaction(tx, self.private_key)
        tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        logger.info("cUSD distribution transaction sent: %s", tx_hash.hex())
        return tx_hash.hex()

