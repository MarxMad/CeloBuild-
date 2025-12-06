import asyncio
import os
import httpx
from src.config import Settings
from src.tools.minipay import MiniPayToolbox

async def mock_handler(request: httpx.Request):
    if request.url.path == "/micropay":
        # Simulate 500 error first two times, then success
        if not hasattr(mock_handler, "calls"):
            mock_handler.calls = 0
        mock_handler.calls += 1
        
        if mock_handler.calls < 3:
            return httpx.Response(500, json={"error": "server error"})
        return httpx.Response(200, json={"status": "success", "tx": "0x123"})
    return httpx.Response(404)

async def main():
    # Setup Mock Transport
    transport = httpx.MockTransport(mock_handler)
    
    # Patch httpx.AsyncClient to use our transport in the tool
    # (In a real test we would use unittest.mock, but this is a quick script)
    original_client = httpx.AsyncClient
    
    def mocked_client(*args, **kwargs):
        kwargs["transport"] = transport
        return original_client(*args, **kwargs)
        
    httpx.AsyncClient = mocked_client
    
    print("--- Test MiniPay Retries ---")
    tool = MiniPayToolbox("https://mock.minipay", "proj_1", "sec_1")
    
    try:
        result = await tool.send_micropayment("0xUser", 1.5)
        print("Success:", result)
    except Exception as e:
        print("Failed:", e)

if __name__ == "__main__":
    asyncio.run(main())
