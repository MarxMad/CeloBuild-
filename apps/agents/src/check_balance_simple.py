import os
from dotenv import load_dotenv
from web3 import Web3

load_dotenv()

def main():
    rpc_url = os.getenv("CELO_RPC_URL", "https://forno.celo.org")
    private_key = os.getenv("CELO_PRIVATE_KEY")
    
    if not private_key:
        print("Error: CELO_PRIVATE_KEY not found in environment")
        return

    # Force HTTP provider explicitly
    if rpc_url.startswith("http"):
        w3 = Web3(Web3.HTTPProvider(rpc_url))
    else:
        w3 = Web3(Web3.HTTPProvider("https://forno.celo.org"))
    account = w3.eth.account.from_key(private_key)
    address = account.address
    
    print(f"Checking balance for address: {address}")
    
    try:
        balance_wei = w3.eth.get_balance(address)
        balance_celo = w3.from_wei(balance_wei, "ether")
        print(f"Balance: {balance_celo} CELO")
        
        if balance_celo < 0.1:
            print("⚠️ WARNING: Balance is very low! This is likely causing 'gas required exceeds allowance' errors.")
        else:
            print("✅ Balance seems sufficient for basic transactions.")
            
    except Exception as e:
        print(f"Error checking balance: {e}")

if __name__ == "__main__":
    main()
