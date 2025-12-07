import os
import sys
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

load_dotenv("apps/agents/.env")

RPC_URL = os.getenv("CELO_RPC_URL")
PRIVATE_KEY = os.getenv("CELO_PRIVATE_KEY")
MINTER_ADDRESS = os.getenv("MINTER_ADDRESS")

def main():
    if not PRIVATE_KEY or not MINTER_ADDRESS:
        print("Missing env vars")
        return

    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    
    account = w3.eth.account.from_key(PRIVATE_KEY)
    print(f"Using account: {account.address}")

    # ABI for configureCampaign
    abi = [
        {
            "type": "function",
            "name": "configureCampaign",
            "inputs": [
                {"name": "campaignId", "type": "bytes32"},
                {"name": "baseURI", "type": "string"}
            ],
            "outputs": [],
            "stateMutability": "nonpayable"
        }
    ]

    contract = w3.eth.contract(address=MINTER_ADDRESS, abi=abi)
    
    campaign_name = "frame-demo-loot"
    campaign_id = w3.keccak(text=campaign_name)
    base_uri = "ipfs://QmDemoBaseURI/"

    print(f"Configuring campaign: {campaign_name}")
    print(f"Campaign ID (bytes32): {campaign_id.hex()}")

    # Build tx
    tx = contract.functions.configureCampaign(
        campaign_id,
        base_uri
    ).build_transaction({
        "from": account.address,
        "nonce": w3.eth.get_transaction_count(account.address),
        "gasPrice": w3.eth.gas_price,
    })

    # Sign and send
    signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    
    print(f"Transaction sent: {tx_hash.hex()}")
    
    # Wait for receipt
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"Transaction confirmed in block {receipt.blockNumber}")

if __name__ == "__main__":
    main()
