import os
import sys
from web3 import Web3

def check_events():
    rpc_url = "https://forno.celo.org"
    registry_address = "0x4a948a06422116fcd8dcd9eacac32e5c40b0e400"
    deployment_block = 53338074
    
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    
    print(f"Registry: {registry_address}")
    print(f"RPC: {rpc_url}")
    print(f"Current Block: {w3.eth.block_number}")
    
    # Contract ABI for XpGranted (Corrected)
    abi = [{"anonymous": False, "inputs": [{"indexed": True, "name": "campaignId", "type": "bytes32"}, {"indexed": True, "name": "participant", "type": "address"}, {"indexed": False, "name": "amount", "type": "uint32"}, {"indexed": False, "name": "newBalance", "type": "uint256"}], "name": "XpGranted", "type": "event"}]
    
    contract = w3.eth.contract(address=w3.to_checksum_address(registry_address), abi=abi)
    
    # Scan last 10,000 blocks first
    current = w3.eth.block_number
    
    # Check historical range from deployment
    print(f"Scanning from Deployment Block: {deployment_block} (Chunk 10k)")
    
    # Scan first 100k blocks after deployment to find initial activity
    logs_total = []
    chunk_size = 10000
    # Limit to 10 chunks (100k blocks) just for check
    for start in range(deployment_block, deployment_block + 100000, chunk_size):
        end = min(start + chunk_size, current)
        print(f"Fetching {start}-{end}...")
        try:
             logs = contract.events.XpGranted.get_logs(from_block=start, to_block=end)
             if logs:
                 print(f"  FOUND {len(logs)} logs!")
                 logs_total.extend(logs)
        except Exception as e:
            print(f"  Error: {e}")
            
    print(f"Total entries found: {len(logs_total)}")
    
    # Check "Most recent" activity
    print("Checking most recent 10k blocks...")
    try:
        logs_recent = contract.events.XpGranted.get_logs(from_block=current-10000, to_block=current)
        print(f"Recent logs: {len(logs_recent)}")
    except Exception as e:
        print(f"Error recent: {e}")

if __name__ == "__main__":
    check_events()
