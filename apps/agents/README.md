# Lootbox Agents Service

Servicio Python que alberga el sistema multiagente utilizado por el proyecto **Agente de Loot Box Social**. Se inspira en el [example-multi-agent-system](https://github.com/celo-org/example-multi-agent-system) y lo extiende con agentes especializados para detectar tendencias en Farcaster, validar elegibilidad on-chain y orquestar recompensas distribuidas vía MiniPay.

## Estructura

```
apps/agents
├── pyproject.toml
├── README.md
├── .env.example
└── src/
    ├── config.py
    ├── main.py
    ├── graph/
    │   ├── supervisor.py
    │   ├── trend_watcher.py
    │   ├── eligibility.py
    │   └── reward_distributor.py
    └── tools/
        ├── celo.py
        ├── farcaster.py
        └── minipay.py
```

## Variables de entorno

Copia `env.sample` a `.env` y completa los valores:

| Variable | Descripción |
| --- | --- |
| `GOOGLE_API_KEY` | API key para Gemini (LangChain) |
| `TAVILY_API_KEY` | API key para búsquedas contextuales |
| `CELO_RPC_URL` | Endpoint RPC (Alfajores/Mainnet) |
| `CELO_EXPLORER_API` | API opcional para métricas on-chain |
| `FARCASTER_HUB_API` | Endpoint del hub o Warpcast API |
| `MINIPAY_TOOL_URL` | Endpoint del MiniPay Tool backend |
| `MINIPAY_PROJECT_ID` | Identificador del MiniPay Tool |

## Comandos

```bash
cd apps/agents
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn src.main:app --reload --port 8001
```

## Próximos pasos

- Completar la lógica de cada agente dentro de `src/graph`.
- Implementar herramientas reales en `src/tools` (consultas Farcaster, verificación on-chain, integración MiniPay Tool).
- Añadir tests de regresión (`pytest`) y flujos LangGraph persistentes (threads).***

