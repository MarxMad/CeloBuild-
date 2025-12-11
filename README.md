<div align="center">
  <img src="apps/web/public/prevewpremio.svg" alt="Premio.xyz Banner" width="100%" />

  # 🏆 Premio.xyz
  
  **Viral Rewards on Farcaster powered by Celo & AI**

  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
  [![Celo](https://img.shields.io/badge/Built_On-Celo-FBCC5C?logo=celo&logoColor=white)](https://celo.org)
  [![MiniPay](https://img.shields.io/badge/Mobile-MiniPay-000000)](https://minipay.celo.org)
  [![Farcaster](https://img.shields.io/badge/Social-Farcaster-855DCD)](https://farcaster.xyz)
</div>

---

> **Hackathon Submission:** Celo Build the Future 🚀  
> **Mission:** Gamify Web3 communities by rewarding genuine engagement automatically.

## 🌟 Overview

**Premio.xyz** is a decentralized agentic platform that turns social engagement into tangible rewards. When a topic goes viral on Farcaster, our autonomous AI agents detect it, identify the top contributors, and instantly reward them with **NFTs**, **cUSD**, or **XP** directly to their MiniPay wallet.

No claiming, no signing, no friction. Just participate and get rewarded.

### ✨ Key Features

- **🤖 Autonomous Agents:** LangGraph-based agents that scan, analyze, and execute transactions without human intervention.
- **📱 Mobile-First:** Designed specifically for **MiniPay** inside Opera Mini.
- **⚡ Instant Rewards:** Automated distribution of cUSD (via MiniPay) and NFTs (via Contracts).
- **🧠 AI Analysis:** Google Gemini AI analyzes sentiment and "viral score" to filter spam.
- **🌍 Bilingual & Themed:** Full English/Spanish support and Dark/Light modes.

---

## 🏗 System Architecture

We employ a **Multi-Agent System** architecture where specialized agents handle specific tasks in a pipeline.

```mermaid
graph TD
    subgraph "📱 User Experience (MiniApp)"
        UI[Next.js Frontend]
        Wallet[MiniPay Wallet]
    end
    
    subgraph "🧠 Agentic Brain (Python/LangGraph)"
        Orchestrator[Orchestrator Agent]
        Trend[Trend Watcher]
        Elig[Eligibility Engine]
        Dist[Reward Distributor]
    end
    
    subgraph "🔗 On-Chain Infrastructure (Celo)"
        Registry[LootAccessRegistry]
        Vault[LootBoxVault (Funds)]
        NFT[LootBoxMinter (NFTs)]
    end

    subgraph "🌐 Data Sources"
        Neynar[Neynar API (Farcaster)]
        Gemini[Google Gemini AI]
    end

    UI -->|1. Trigger Scan| Orchestrator
    Orchestrator -->|2. Delegate| Trend
    Trend -->|3. Fetch Casts| Neynar
    Trend -->|4. Analyze Sentiment| Gemini
    Trend -->|5. Viral Candidates| Elig
    
    Elig -->|6. Check Reputation| Registry
    Elig -->|7. Verify User| Dist
    
    Dist -->|8. Mint NFT| NFT
    Dist -->|9. Send cUSD| Vault
    Dist -->|10. Grant XP| Registry
    
    NFT -.->|Ownership| Wallet
    Vault -.->|cUSD Transfer| Wallet
```

---

## 🔄 How it Works

1.  **Detection**: The `TrendWatcher` agent constantly scans Farcaster for hashtags or keywords associated with active campaigns.
2.  **Scoring**: User interactions are analyzed. A "Viral Score" (0-100) is calculated based on likes, recasts, replies, and user reputation (Power Badge).
3.  **Reward**:
    *   **Score > 85**: Grants a **Rare Loot NFT** 🎨.
    *   **Score > 60**: Sends **cUSD** directly to the user (Micropayments) 💵.
    *   **Score < 60**: Awards **XP** (On-chain reputation) ⭐.

---

## 🛠 Tech Stack

### Frontend (Apps/Web)
*   **Next.js 14**: App Router, Server Components.
*   **TailwindCSS**: Styling with custom "Sci-Fi" design system.
*   **Wagmi / Viem**: Blockchain interaction.
*   **Farcaster Auth**: Farcaster Kit for login.
*   **I18n**: Custom lightweight internationalization.

### Backend Agents (Apps/Agents)
*   **Python 3.11**: Core runtime.
*   **LangGraph**: Orchestration of stateful multi-agent workflows.
*   **FastAPI**: REST API entrypoints.
*   **Pydantic**: Data validation and typed settings.
*   **AsyncIO**: High-concurrency task management.

### Contracts (Apps/Contracts)
*   **Solidity 0.8.20**: Smart contract language.
*   **Foundry**: Development, testing, and deployment framework.
*   **OpenZeppelin**: Standard secure implementations (ERC20, ERC721).

---

## 🚀 Getting Started

### Prerequisites
- Node.js 18+ & PNPM
- Python 3.10+ & Poetry/Pip
- Foundry (Forge)

### 1. Installation

```bash
# Clone the repo
git clone https://github.com/MarxMad/CeloBuild-.git
cd lootbox-minipay

# Install JS dependencies
pnpm install
```

### 2. Setup Agents (Backend)

```bash
cd apps/agents
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Configure environment
cp env.sample .env
# Add NEYNAR_API_KEY, CELO_PRIVATE_KEY, etc.
```

### 3. Run Development Server

```bash
# In separate terminals:
# 1. Run Agents
cd apps/agents
uvicorn src.main:app --reload --port 8001

# 2. Run Frontend
cd apps/web
pnpm dev
```

Visit `http://localhost:3000` to see the app running.

---

## 📜 Deployed Contracts (Celo Mainnet)

| Contract | Address |
|----------|---------|
| **LootBoxVault** | [`0x4f7aa310c1f90e435f292f5d9ba07cb102409990`](https://celoscan.io/address/0x4f7aa310c1f90e435f292f5d9ba07cb102409990) |
| **LootAccessRegistry** | [`0x28a499be43d2e9720e129725e052781746e59d1d`](https://celoscan.io/address/0x28a499be43d2e9720e129725e052781746e59d1d) |
| **LootBoxMinter** | [`0x39b93bac43ed50df42ea9e0dde38bcd072f0a771`](https://celoscan.io/address/0x39b93bac43ed50df42ea9e0dde38bcd072f0a771) |

---

<div align="center">
  <sub>Built with ❤️ by Gerry & The Team for Celo Build 2025</sub>
</div>
