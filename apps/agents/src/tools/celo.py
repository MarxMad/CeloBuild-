from __future__ import annotations

from dataclasses import dataclass

from web3 import Web3


@dataclass
class CeloToolbox:
    """Pequeño envoltorio para consultar contratos en Celo."""

    rpc_url: str

    def __post_init__(self) -> None:
        self.web3 = Web3(Web3.HTTPProvider(self.rpc_url))

    def get_balance(self, address: str) -> int:
        """Devuelve el balance nativo (placeholder)."""

        return self.web3.eth.get_balance(address)

