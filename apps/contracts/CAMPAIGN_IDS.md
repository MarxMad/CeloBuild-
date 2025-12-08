# 📋 Campaign IDs - Explicación Completa

## 🎯 ¿Qué son los Campaign IDs?

Los **Campaign IDs** son identificadores únicos (bytes32) que se usan para agrupar recompensas relacionadas con una misma tendencia o evento en Farcaster.

## 🔢 Cómo se Generan

### 1. **Campañas Dinámicas (Producción)**

Cuando el agente detecta una tendencia en Farcaster, genera un `campaign_id` automáticamente:

```python
# En eligibility.py línea 28
campaign_id = f"{context.get('frame_id', 'global')}-loot"
```

**Formato típico:**
- `cast-{hash}-loot` - Basado en el hash del cast viral
- `{frame_id}-loot` - Basado en un frame específico
- `global-loot` - Si no hay frame_id específico

**Ejemplo:**
- Si el cast_hash es `0x812abc123...`
- El campaign_id será: `cast-0x812abc123-loot`
- El bytes32 se calcula: `keccak256("cast-0x812abc123-loot")`

### 2. **demo-campaign (Fallback)**

Es una campaña estática que se usa cuando:
- Hay un error al configurar la campaña dinámica
- Es una prueba/desarrollo
- El agente no puede configurar la campaña automáticamente

**ID:** `keccak256("demo-campaign")`

## 📍 Dónde se Usan

Los campaign IDs se usan en **3 contratos**:

1. **LootAccessRegistry**: Para controlar cooldowns (1 día por defecto)
2. **LootBoxMinter**: Para asociar NFTs con metadata
3. **LootBoxVault**: Para distribuir cUSD (requiere fondos depositados)

## 🔍 Cómo Ver Campaign IDs Activos

### Opción 1: Script Automatizado

```bash
cd apps/contracts
./list-campaigns.sh
```

### Opción 2: Manual con `cast`

```bash
# Calcular campaign_id para "demo-campaign"
cast keccak "demo-campaign"

# Calcular campaign_id para un cast específico
cast keccak "cast-0x812abc123-loot"

# Verificar en Registry
cast call $REGISTRY_ADDRESS \
    "campaignRules(bytes32)(uint64,bool)" \
    $(cast keccak "demo-campaign") \
    --rpc-url $CELO_RPC_URL

# Verificar en Vault
cast call $LOOTBOX_VAULT_ADDRESS \
    "getCampaign(bytes32)(address,uint96,uint256,bool)" \
    $(cast keccak "demo-campaign") \
    --rpc-url $CELO_RPC_URL
```

### Opción 3: Revisar Logs del Backend

Cuando el agente ejecuta un scan, verás en los logs:

```
Configurando campaña real automáticamente: cast-0x812abc123-loot
✅ Campaña cast-0x812abc123-loot configurada (o ya existía)
```

### Opción 4: Leaderboard API

```bash
curl http://localhost:8001/api/lootbox/leaderboard?limit=10
```

Las entradas incluyen el `campaign_id` usado.

## 💰 Depositar Fondos en Campañas Dinámicas

Cuando el agente crea una campaña dinámica, **NO deposita fondos automáticamente**. Necesitas hacerlo manualmente:

```bash
# 1. Obtener el campaign_id del log del backend
# Ejemplo: "cast-0x812abc123-loot"

# 2. Depositar fondos
cd apps/contracts
CAMPAIGN_ID="cast-0x812abc123-loot" FUND_AMOUNT_CUSD=50 ./fund-campaign.sh
```

## 🎯 Flujo Completo

1. **TrendWatcherAgent** detecta un cast viral → genera `cast_hash`
2. **EligibilityAgent** crea `campaign_id = f"cast-{hash}-loot"`
3. **RewardDistributorAgent**:
   - Si `campaign_id != "demo-campaign"`:
     - Configura automáticamente en Registry, Minter y Vault
     - **PERO NO deposita fondos** (debes hacerlo manualmente)
   - Si falla → usa `demo-campaign` como fallback
4. **Distribución**: Usa el `campaign_id` para otorgar recompensas

## ⚠️ Importante

- **demo-campaign**: Ya está configurada y puedes depositar fondos fácilmente
- **Campañas dinámicas**: Se crean automáticamente, pero necesitas:
  1. Ver el `campaign_id` en los logs
  2. Depositar fondos manualmente usando el script
- **Sin fondos**: Si no hay fondos en el vault, las recompensas de cUSD fallarán

## 🔧 Solución Rápida

Para empezar rápido, deposita fondos en `demo-campaign`:

```bash
cd apps/contracts
CAMPAIGN_ID="demo-campaign" FUND_AMOUNT_CUSD=100 ./fund-campaign.sh
```

Esto permitirá que las recompensas funcionen incluso si las campañas dinámicas no tienen fondos.

