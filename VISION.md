# 🎯 Visión del Proyecto Premio.xyz

## Objetivo Principal

**Premio.xyz** es una plataforma que **gamifica la interacción en comunidades Web3** mediante un sistema de agentes autónomos que:

1. **Detecta tendencias virales en Farcaster** en tiempo real
2. **Identifica usuarios valiosos** basándose en engagement, reputación y participación
3. **Distribuye recompensas instantáneamente** directamente a las wallets de los usuarios

---

## 🔄 Flujo Completo del Sistema

### 1. **Detección de Tendencias (TrendWatcherAgent)**

**¿Qué hace?**
- Escanea Farcaster usando Neynar API buscando conversaciones que están ganando tracción
- Analiza engagement (likes, recasts, replies, tiempo desde publicación)
- Usa IA (Gemini) para entender el contexto y relevancia para la comunidad Celo/MiniPay
- Calcula un `trend_score` (0-1) que determina si vale la pena recompensar

**¿Cómo funciona?**
- Se ejecuta periódicamente o cuando el usuario activa el sistema
- Busca en canales específicos o globalmente
- Identifica el cast más viral del momento
- Extrae tags, análisis de IA y metadata relevante

**Output:**
```python
{
  "frame_id": "cast-abc123",
  "cast_hash": "0x...",
  "trend_score": 0.85,
  "source_text": "¡MiniPay está cambiando el juego! 🚀",
  "ai_analysis": "Post relevante sobre adopción de MiniPay...",
  "topic_tags": ["minipay", "celo", "web3"],
  "channel_id": "builders"
}
```

---

### 2. **Elegibilidad y Scoring (EligibilityAgent)**

**¿Qué hace?**
- Toma los datos de la tendencia detectada
- Identifica a los usuarios que participaron en esa conversación (likes, replies, recasts)
- Calcula un `user_score` para cada participante basado en:
  - **Reputación social**: Follower count, power badge, engagement histórico
  - **Engagement en el cast**: Qué tan activo fue en esa conversación específica
  - **Historial on-chain**: Si ya recibió premios recientemente (cooldown)
- Filtra usuarios que no pueden reclamar (cooldown activo)
- Selecciona los top N usuarios elegibles

**¿Cómo funciona?**
- Consulta Neynar API para obtener participantes del cast
- Para cada participante, obtiene su perfil de Farcaster (followers, badges)
- Consulta `LootAccessRegistry` on-chain para verificar cooldowns
- Calcula score combinando: `trend_score * 40 + follower_score + badge_bonus + engagement_weight`
- Ordena por score y selecciona los mejores

**Output:**
```python
{
  "campaign_id": "cast-abc123-loot",
  "recipients": ["0xUser1", "0xUser2", "0xUser3"],
  "rankings": [
    {
      "fid": 12345,
      "username": "celo_builder",
      "address": "0xUser1",
      "score": 92.5,
      "follower_count": 5000,
      "power_badge": True,
      "reasons": ["top_engager", "power_badge", "high_followers"]
    },
    ...
  ]
}
```

---

### 3. **Distribución de Recompensas (RewardDistributorAgent)**

**¿Qué hace?**
- Toma los usuarios elegibles y el tipo de recompensa seleccionado
- Distribuye la recompensa según el tipo:
  - **NFT**: Mintea un NFT conmemorativo usando `LootBoxMinter`
  - **cUSD**: Envía micropago usando **MiniPay Tool API** (método preferido)
  - **XP**: Otorga puntos de reputación on-chain usando `LootAccessRegistry.grantXp`
- Registra todo en el leaderboard para que el frontend lo muestre

**¿Cómo funciona con MiniPay?**

#### Para cUSD Drops (Método Principal):
1. **Si MiniPay Tool API está configurada** (`MINIPAY_PROJECT_SECRET`):
   - Usa `MiniPayToolbox.send_micropayment()` para enviar cUSD directamente
   - Más rápido, menos gas, mejor UX
   - El usuario recibe la notificación instantáneamente en su wallet MiniPay

2. **Si MiniPay Tool API NO está disponible** (fallback):
   - Usa el contrato `LootBoxVault.distributeERC20()` 
   - Distribuye cUSD desde el contrato (requiere fondos pre-depositados)
   - Más gas, pero funciona sin API externa

#### Para NFTs:
- Usa `LootBoxMinter.mintBatch()` para mintear NFTs directamente
- El NFT aparece en la wallet del usuario (MiniPay o cualquier wallet compatible)

#### Para XP:
- Usa `LootAccessRegistry.grantXp()` para otorgar puntos on-chain
- Los puntos quedan registrados en el contrato y se pueden consultar

**Output:**
```python
{
  "mode": "micropayments",  # o "nft_minted" o "xp_granted"
  "tx_hash": "0x...",
  "recipients": ["0xUser1", "0xUser2"],
  "minted": {},  # si fue NFT
  "micropayments": {"0xUser1": "0xtx1", "0xUser2": "0xtx2"},  # si fue cUSD
  "xp_awards": {},  # si fue XP
  "reward_type": "cusd"
}
```

---

## 🎮 Experiencia del Usuario

### Flujo en el Frontend (MiniApp):

1. **Usuario abre la MiniApp en MiniPay**
   - MiniPay inyecta `window.ethereum` automáticamente
   - El usuario está conectado sin hacer clic
   - Ve su balance de CELO y cUSD

2. **Usuario hace clic en "Activar Recompensas"**
   - El frontend llama a `/api/lootbox/run` con su `target_address`
   - Los agentes empiezan a trabajar en background

3. **Sistema analiza Farcaster**
   - TrendWatcher busca tendencias
   - Eligibility identifica usuarios valiosos
   - El usuario ve animaciones en el "Live Monitor"

4. **Usuario elige su recompensa**
   - Aparece el selector: "Rare NFT", "cUSD Drop", "+100 XP"
   - El usuario selecciona una opción
   - El frontend envía `reward_type` al backend

5. **Recompensa se distribuye**
   - Si eligió **NFT**: Se mintea y aparece en su wallet
   - Si eligió **cUSD**: MiniPay Tool API envía micropago → notificación instantánea
   - Si eligió **XP**: Se otorga on-chain y aparece en el leaderboard

6. **Usuario ve confirmación**
   - Link a la transacción en Blockscout
   - Su nombre aparece en el leaderboard
   - Puede ver su XP acumulado

---

## 🔑 Puntos Clave de la Arquitectura

### MiniPay como Método Principal de Distribución de cUSD

**¿Por qué MiniPay Tool API?**
- **UX Superior**: El usuario recibe notificación push instantánea
- **Menos Gas**: La API optimiza las transacciones
- **Escalable**: Puede manejar muchos micropagos eficientemente
- **Mobile-First**: Perfecto para usuarios de MiniPay en móviles

**¿Cuándo usar el fallback (LootBoxVault)?**
- Si no tienes acceso a MiniPay Tool API
- Si quieres control total on-chain
- Si prefieres batch transactions para ahorrar gas en múltiples recipients

### Agentes Autónomos

**Los agentes deben:**
- Funcionar sin intervención manual
- Analizar datos reales de Farcaster (no mocks)
- Tomar decisiones inteligentes sobre quién merece recompensa
- Registrar todo on-chain para transparencia

**Los agentes NO deben:**
- Requerir aprobación manual para cada recompensa
- Usar datos ficticios en producción
- Ignorar cooldowns o reglas de elegibilidad

---

## 📊 Flujo de Datos

```
Farcaster (Neynar API)
    ↓
TrendWatcherAgent (detecta tendencia)
    ↓
EligibilityAgent (identifica usuarios + calcula scores)
    ↓
RewardDistributorAgent (distribuye según reward_type)
    ├─→ NFT: LootBoxMinter.mintBatch()
    ├─→ cUSD: MiniPayToolbox.send_micropayment() [PREFERIDO]
    │        o LootBoxVault.distributeERC20() [FALLBACK]
    └─→ XP: LootAccessRegistry.grantXp()
    ↓
LeaderboardStore (guarda histórico)
    ↓
Frontend (muestra leaderboard en vivo)
```

---

## 🎯 Objetivos del Sistema

1. **Gamificación Real**: Los usuarios se sienten recompensados por participar activamente en Farcaster
2. **Transparencia Total**: Todo queda registrado on-chain (quién recibió qué y cuándo)
3. **UX Invisible**: El usuario solo hace clic y recibe su premio automáticamente
4. **Escalable**: Puede manejar muchas tendencias y usuarios simultáneamente
5. **Mobile-First**: Optimizado para MiniPay y usuarios móviles

---

## ❓ Preguntas para Clarificar

1. **¿Los agentes deben ejecutarse automáticamente en background?** (ej: cada 5 minutos buscar nuevas tendencias)
   - O solo cuando el usuario activa manualmente desde el frontend?

2. **¿MiniPay Tool API es el método PRINCIPAL para cUSD?**
   - ¿O prefieres usar siempre el contrato LootBoxVault?

3. **¿Cómo quieres manejar múltiples usuarios elegibles?**
   - ¿Todos reciben el mismo tipo de recompensa?
   - ¿O el top 1 recibe NFT, top 2-3 reciben cUSD, resto recibe XP?

4. **¿El usuario elige la recompensa ANTES de que los agentes analicen?**
   - O los agentes determinan automáticamente qué recompensa dar según el score?

5. **¿El flujo de datos de Farcaster?**
   - ¿Los agentes deben analizar el cast específico donde el usuario participó?
   - ¿O analizan tendencias globales y luego verifican si el usuario participó en ellas?

---

## ✅ Respuestas Implementadas

1. **✅ Agentes automáticos cada 30 minutos**
   - Scheduler configurado con APScheduler
   - Ejecuta scans automáticos en background cada 30 minutos
   - Opción `AUTO_SCAN_ON_STARTUP` para ejecutar al iniciar

2. **✅ MiniPay Tool API como método principal**
   - Prioriza MiniPay Tool API para distribuir cUSD
   - Fallback automático a LootBoxVault si no está configurado
   - Perfecto para el hackathon de Celo

3. **✅ Sistema de tiers dinámico**
   - **Tier 1 (Score >= 85)**: NFT
   - **Tier 2 (Score >= 60)**: cUSD via MiniPay Tool
   - **Tier 3 (Score < 60)**: XP on-chain
   - Configurable mediante `TIER_NFT_THRESHOLD` y `TIER_CUSD_THRESHOLD`

4. **✅ Agentes determinan recompensa automáticamente**
   - Si `reward_type` no se proporciona, se determina por score
   - Cada usuario recibe la recompensa según su tier
   - El usuario puede forzar un tipo específico si lo desea

5. **✅ Análisis de participación en tendencias globales**
   - Analiza tendencias globales primero
   - Verifica si el usuario participó (like/recast/reply)
   - Analiza casts del usuario sobre el tema
   - Ponderación basada en likes (1x), recasts (2x), replies (0.6x)

