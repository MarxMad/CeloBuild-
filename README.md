# 🎁 Loot Box Social (Celo + MiniPay + Multi-Agentes)

Una plataforma descentralizada que combina el poder de la **Inteligencia Artificial** con la velocidad de **Celo** para crear campañas de recompensas automáticas ("Loot Boxes") basadas en tendencias sociales de Farcaster.

---

## 🌟 Visión

El objetivo es gamificar la interacción en comunidades Web3. Cuando un tema se vuelve viral en Farcaster, nuestro sistema de agentes autónomos entra en acción:

1.  **Detecta** la tendencia (TrendWatcher).
2.  **Identifica** a los usuarios más valiosos y activos (Eligibility).
3.  **Recompensa** instantáneamente con micropagos (cUSD) o NFTs coleccionables directamente en su wallet MiniPay.

Todo esto ocurre de forma transparente y verificable on-chain, con una experiencia de usuario "invisible" gracias a MiniPay.

---

## 🏗 Arquitectura del Sistema

El proyecto es un Monorepo que integra tres componentes principales:

### 1. 🤖 Servicio Multi-Agente (Python / LangGraph)
El "cerebro" de la operación. Orquesta un pipeline de agentes especializados:
*   **`TrendWatcherAgent`**: Escanea Farcaster (Warpcast) buscando frames y casts virales.
*   **`EligibilityAgent`**: Aplica filtros de reputación (ej. antigüedad, POAPs) y verifica si el usuario ya participó (consultando la blockchain).
*   **`RewardDistributorAgent`**: Ejecuta la distribución de premios. Interactúa con la API de MiniPay para micropagos y con los contratos inteligentes para mintear NFTs.

### 2. 📜 Contratos Inteligentes (Solidity / Foundry)
La capa de seguridad y liquidación en Celo (Alfajores/Sepolia):
*   **`LootBoxVault`**: Bóveda segura que custodia el presupuesto (cUSD/CELO) de las campañas.
*   **`LootAccessRegistry`**: Registro on-chain que evita el "doble gasto" de recompensas (cooldowns, historial).
*   **`LootBoxMinter`**: Contrato ERC721 optimizado para emitir NFTs conmemorativos de cada campaña.

### 3. 📱 Frontend & MiniPay (Next.js 14)
La interfaz de usuario optimizada para móviles:
*   Integrada nativamente con **MiniPay Wallet** (injected provider).
*   Permite a los administradores simular campañas manualmente.
*   Muestra a los usuarios su historial de victorias y saldo en tiempo real.

---

## 🚀 Tecnologías Clave

*   **Blockchain**: Celo (Compatible EVM, Mobile-first).
*   **Framework de Agentes**: LangGraph + LangChain (Python).
*   **Smart Contracts**: Foundry (Test, Script, Deploy).
*   **Frontend**: Next.js, TailwindCSS, RainbowKit, Wagmi.
*   **Social**: Farcaster (Warpcast API).

---

## 🛠 Puesta en Marcha (Local)

Sigue estos pasos para levantar todo el entorno de desarrollo en tu máquina.

### Prerrequisitos
*   Node.js 18+ y PNPM.
*   Python 3.11+.
*   Foundry (Forge/Cast).

### 1. Configuración Inicial
Clona el repo e instala dependencias del workspace JS:

```bash
pnpm install
```

### 2. Levantar el Servicio de Agentes (Backend)
Este servicio corre en el puerto `8001`.

```bash
cd apps/agents
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Copia y configura las variables de entorno (puedes usar los valores mock por defecto)
cp env.sample .env

# Inicia el servidor con recarga automática
uvicorn src.main:app --reload --port 8001
```

> **Nota**: El servicio incluye un "Mock Mode". Si no tienes API keys reales de Farcaster, usará datos simulados para que puedas probar el flujo completo.

### 3. Levantar el Frontend (Web)
La aplicación web corre en el puerto `3000`.

```bash
# En una nueva terminal, desde la raíz del proyecto
cd apps/web
cp env.sample .env
pnpm dev
```

Abre [http://localhost:3000](http://localhost:3000) en tu navegador.

### 4. (Opcional) Compilar y Probar Contratos
Si deseas modificar la lógica on-chain:

```bash
cd apps/contracts
forge install
forge test    # Ejecuta la suite de pruebas (incluye Fuzz testing)
forge build
```

---

## 🧪 Probando el Flujo (Demo)

1.  Asegúrate de tener el **Backend (Agents)** y el **Frontend (Web)** corriendo.
2.  Ve a `http://localhost:3000`.
3.  En la sección **"Prueba el pipeline multiagente"**, verás un formulario precargado.
4.  Haz clic en **"Ejecutar agente"**.
5.  Verás cómo el frontend se comunica con el servicio Python, el cual simula la detección de una tendencia, selecciona ganadores y "envía" los pagos (verás los logs en la terminal de Python).

---

## 📂 Estructura del Proyecto

```
lootbox-minipay/
├── apps/
│   ├── agents/       # Servicio Python (LangGraph)
│   │   ├── src/
│   │   │   ├── graph/    # Lógica de los agentes (TrendWatcher, Eligibility...)
│   │   │   ├── tools/    # Integraciones (Farcaster, MiniPay, Celo)
│   │   │   └── main.py   # Entrypoint FastAPI
│   │
│   ├── contracts/    # Smart Contracts (Foundry)
│   │   ├── src/          # .sol files (Vault, Registry, Minter)
│   │   ├── test/         # Tests unitarios y fuzzing
│   │   └── script/       # Scripts de despliegue
│   │
│   └── web/          # Frontend (Next.js)
│       ├── src/app/      # Rutas y API Proxy
│       └── components/   # UI Components (shadcn/ui)
│
└── packages/         # Librerías compartidas (si aplica)
```

---

## 🔮 Próximos Pasos

*   [ ] **Despliegue en Testnet**: Enviar los contratos a Celo Sepolia una vez la wallet tenga fondos.
*   [ ] **Producción**: Conectar las API keys reales de Farcaster y MiniPay.
*   [ ] **ZK Proofs**: Integrar Semaphore para validación de identidad privada.
