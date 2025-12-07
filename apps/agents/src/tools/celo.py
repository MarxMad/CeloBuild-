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

    def mint_nft(self, minter_address: str, campaign_id: str, recipient: str) -> str:
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
        
        # Convertir campaign_id a bytes32
        campaign_bytes = self.web3.keccak(text=campaign_id)
        
        # Asegurar checksum de la dirección
        try:
            checksum_recipient = self.web3.to_checksum_address(recipient)
        except ValueError:
             # Si falla la validación, lanzamos error claro
             raise ValueError(f"Dirección inválida: {recipient}")

        # Construir transacción
        # Usamos un URI genérico por ahora
        metadata_uri = "ipfs://QmExample" 
        
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
