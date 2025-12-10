import asyncio
import os
import sys
from pathlib import Path
from web3 import Web3

# Add src to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

# Load env vars manually since we can't import config easily without deps
from dotenv import load_dotenv
load_dotenv("apps/agents/.env")

def main():
    print("Checking Agent Wallet...")
    
    private_key = os.getenv("CELO_PRIVATE_KEY")
    rpc_url = os.getenv("CELO_RPC_URL")
    registry_address = os.getenv("REGISTRY_ADDRESS")
    
    if not private_key:
        print("❌ Error: CELO_PRIVATE_KEY not found in env")
        return

    # Handle WebSocket vs HTTP
    if rpc_url.startswith("wss://"):
        print(f"⚠️ WebSocket URL detected: {rpc_url}")
        print("🔄 Switching to HTTP for this script...")
        rpc_url = "https://forno.celo.org"

    web3 = Web3(Web3.HTTPProvider(rpc_url))
    account = web3.eth.account.from_key(private_key)
    
    print(f"🔑 Agent Address: {account.address}")
    print(f"🌐 RPC URL: {rpc_url}")
    print(f"📝 Registry Address: {registry_address}")
    
    nonce = web3.eth.get_transaction_count(account.address)
    print(f"🔢 Transaction Count (Nonce): {nonce}")
    
    balance = web3.eth.get_balance(account.address)
    print(f"💰 Balance: {web3.from_wei(balance, 'ether')} CELO")

if __name__ == "__main__":
    main()
