import os
from dotenv import load_dotenv
from .tools.celo import CeloToolbox

load_dotenv()

def main():
    rpc_url = os.getenv("CELO_RPC_URL", "https://forno.celo.org")
    private_key = os.getenv("CELO_PRIVATE_KEY")
    
    if not private_key:
        print("Error: CELO_PRIVATE_KEY not found in environment")
        return

    toolbox = CeloToolbox(rpc_url=rpc_url, private_key=private_key)
    address = toolbox.account.address
    print(f"Checking balance for address: {address}")
    
    try:
        balance = toolbox.get_balance(address)
        print(f"Balance: {balance} CELO")
        
        if balance < 0.1:
            print("⚠️ WARNING: Balance is very low! This is likely causing 'gas required exceeds allowance' errors.")
        else:
            print("✅ Balance seems sufficient for basic transactions.")
            
    except Exception as e:
        print(f"Error checking balance: {e}")

if __name__ == "__main__":
    main()
