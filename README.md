# Agente de Loot Box Social (MiniPay + Foundry + Multi-Agentes)

Monorepo generado con **Celo Composer (plantilla MiniPay + Foundry)** para construir un agente que detecta conversaciones trending en Farcaster y reparte recompensas sorpresa (micropagos y cNFTs) vía MiniPay. El proyecto incorpora un servicio multiagente inspirado en el [example-multi-agent-system](https://github.com/celo-org/example-multi-agent-system).

---

## Visión

- **Detección social:** un agente `TrendWatcher` monitorea frames y canales Farcaster; cuando un tema supera cierto umbral, abre una campaña “loot box”.
- **Elegibilidad híbrida:** `EligibilityAgent` cruza actividad social con participación on-chain (contratos Foundry) y, opcionalmente, pruebas ZK que preservan privacidad.
- **Distribución MiniPay:** `RewardDistributor` coordina micropagos y minteo de cNFTs mediante el MiniPay Tool y contratos `LootBoxVault`/`LootBoxMinter`.
- **Experiencia móvil:** MiniPay sirve de wallet y superficie UX para canjear, confirmar o compartir los drops.

---

## Arquitectura (alto nivel)

1. **apps/web** – Frontend Next.js 14 preparado para MiniPay (RainbowKit + shadcn/ui).
2. **apps/contracts** – Entorno Foundry (añadiremos contratos `LootBoxVault`, `LootBoxMinter`, `LootAccessRegistry`, `ChannelSemaphoreVerifier`).
3. **apps/agents** – Nuevo servicio Python (LangGraph + LangChain) con supervisor, agentes especializados y herramientas (Farcaster, Celo, MiniPay).
4. **PNPM Workspace + Turborepo** – Orquesta pipelines JS; el servicio Python vive fuera de PNPM pero dentro del monorepo para compartir CI/CD.

---

## Roadmap por fases

1. **Fundación (completo)**  
   - Crear monorepo con plantilla MiniPay + Foundry.  
   - Añadir carpeta `apps/agents` y dependencias base de LangGraph.

2. **Contratos Foundry (en curso)**  
   - Diseñar/interfaces de `LootBoxVault`, `LootBoxMinter`, `LootAccessRegistry`.  
   - Añadir scripts `forge script` para deploy a Alfajores y pruebas `forge test`.

3. **Servicio multiagente**  
   - Completar lógica de cada agente, conectar herramientas reales (Warpcast, Tavily, MiniPay Tool).  
   - Persistencia de threads y memoria usando LangGraph + storage (p. ej. Redis).

4. **Integración MiniPay y frontend**  
   - Crear componentes en `apps/web` para listar campañas, mostrar estado de reclamos y disparar pruebas ZK.  
   - Exponer API Gateway que conecte web ↔ agentes ↔ contratos.

5. **Observabilidad y hardening**  
   - Métricas Prometheus/Grafana, logging estructurado, colas de reintentos.  
   - Auditorías de contratos y límites anti-bots (cooldowns, verificación reputacional).

---

## Puesta en marcha

### 1. Monorepo JS

```bash
cd lootbox-minipay
pnpm install          # si el CLI saltó la instalación
pnpm dev              # lanza apps web/contratos en paralelo
```

### 2. Foundry

```bash
cd apps/contracts
forge install         # instala deps (si falló durante el scaffolding)
forge test
```

### 3. Servicio multiagente

```bash
cd apps/agents
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp env.sample .env    # completa claves (Gemini, Tavily, Farcaster, MiniPay)
uvicorn src.main:app --reload --port 8001
```

---

## Detalle del sistema multiagente (`apps/agents`)

| Componente | Rol | Herramientas |
| --- | --- | --- |
| `TrendWatcherAgent` | Analiza frames trending (Warpcast + Tavily) y genera contexto de campaña | Farcaster API, búsqueda contextual |
| `EligibilityAgent` | Cruza actividad social, on-chain y pruebas ZK para decidir receptores | Celo RPC, contratos Foundry, ZK (Semaphore) |
| `RewardDistributorAgent` | Orquesta micropagos y cNFTs, escribe eventos on-chain | MiniPay Tool API, Web3 |
| `SupervisorOrchestrator` | Hilo principal (LangGraph) que encadena agentes, mantiene thread_id | LangGraph, memoria persistente |

`apps/agents/src` ya incluye esqueletos de clases y herramientas (`tools/celo.py`, `tools/farcaster.py`, `tools/minipay.py`) para empezar a conectar APIs reales.

---

## Contratos Foundry previstos

1. **`LootBoxVault`** – Custodia fondos cUSD/cEUR, define campañas, distribuye ERC20/cNFT en batch, soporta roles (`AGENT_ROLE`, `TREASURY_ROLE`).  
2. **`LootBoxMinter`** – ERC721/ERC1155 modular; metadata refleja la conversación trending, soporte para loot “soulbound” y rarezas.  
3. **`LootAccessRegistry`** – Historial de reclamos, cooldown y reglas reputacionales. Expone `canClaim(address, campaignId)` y eventos para el agente.  
4. **`ChannelSemaphoreVerifier` (opcional)** – Mantiene Merkle roots por canal Farcaster y verifica pruebas ZK para pertenencia privada.

Próximos pasos inmediatos:

- Modelar storage y eventos de `LootBoxVault`.  
- Añadir pruebas unitarias/grupales (fuzz) que simulen campañas con cientos de usuarios.  
- Escribir script `script/LootBoxDeployer.s.sol` para automatizar despliegues.

---

## Integración MiniPay

- **MiniPay Tool API**: `RewardDistributor` usará un backend firmado que ejecuta micropagos (push) o genera deep-links de claim (pull).  
- **Experiencia MiniPay**: componentes en `apps/web` mostrarán campañas activas, historial y botones “Claim”.  
- **Notificaciones**: el agente puede llamar a MiniPay para enviar anuncios cuando una nueva campaña se abre o cuando quedan pocos loot boxes.

---

## Checklist / Backlog inmediato

- [ ] Esquematizar contratos (`LootBoxVault`, `LootAccessRegistry`) y generar stubs en `apps/contracts/src`.  
- [ ] Conectar `TrendWatcherAgent` con Warpcast (frames endpoint) y añadir un mock service para desarrollo offline.  
- [ ] Implementar `MiniPayToolbox.send_micropayment` con autenticación y manejo de errores.  
- [ ] Crear endpoints en `apps/web` que consulten el servicio multiagente y muestren campañas.  
- [ ] Añadir pruebas unitarias para cada agente y pipeline E2E básico.

Con esta guía ya tienes el plan detallado y el scaffolding inicial tanto del monorepo MiniPay como del sistema multiagente. Continúa completando cada fase siguiendo el roadmap. ¡Vamos! 🚀
