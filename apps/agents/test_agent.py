import asyncio
import os
from src.config import Settings
from src.graph.trend_watcher import TrendWatcherAgent

# Configuración mock para la prueba
os.environ["GOOGLE_API_KEY"] = "mock"
os.environ["TAVILY_API_KEY"] = "mock"
os.environ["CELO_RPC_URL"] = "https://alfajores-forno.celo-testnet.org"
os.environ["FARCASTER_HUB_API"] = "https://api.warpcast.com" # Usará mock si falla auth
os.environ["MINIPAY_TOOL_URL"] = "https://mock.minipay"
os.environ["MINIPAY_PROJECT_ID"] = "test"
os.environ["AGENT_WEBHOOK_SECRET"] = "secret"

async def main():
    settings = Settings()
    agent = TrendWatcherAgent(settings)
    
    print("--- Test 1: Auto-detect trending ---")
    result = await agent.handle({})
    print("Result:", result)
    
    print("\n--- Test 2: Analyze specific frame ---")
    result_specific = await agent.handle({"frame_id": "specific-frame-123"})
    print("Result:", result_specific)

if __name__ == "__main__":
    asyncio.run(main())
