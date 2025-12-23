# 🚀 Configuración para Producción - Campañas Reales

## ⚠️ IMPORTANTE: Campañas Reales vs Demo

En producción, el sistema debe usar **campañas reales** generadas dinámicamente cuando se detectan nuevas tendencias en Farcaster. Las campañas se crean automáticamente con el formato:
- `cast-0x812abc-loot` (basado en el hash del cast viral)
- `global-loot` (para tendencias globales)

## 🔧 Paso 1: Desplegar Contratos con Ownership del Agente

El script `DeployProduction` despliega los contratos y **automáticamente transfiere el ownership al agente** para que pueda crear campañas dinámicamente:

```bash
cd apps/contracts

# Configurar variables
export DEPLOYER_PRIVATE_KEY=0x...  # Tu private key para desplegar
export AGENT_ADDRESS=0x...          # Dirección del agente (derivada de CELO_PRIVATE_KEY)
export CELO_RPC_URL=https://...
export CUSD_ADDRESS=0x874069Fa1Eb16D44d622F2e0Ca25eeA172369bC1  # Opcional

# Ejecutar deployment completo
./deploy-production.sh
```

**⚠️ ADVERTENCIA**: El script transfiere el control completo de los contratos al agente. Asegúrate de:
- Que la `CELO_PRIVATE_KEY` del agente esté segura
- Que confíes completamente en el código del agente
- Considerar usar una wallet multisig para mayor seguridad

## ✅ Paso 2: Verificar Ownership

Después de transferir, verifica que el agente es owner:

```bash
# Verificar LootBoxVault
cast call $LOOTBOX_VAULT_ADDRESS "owner()(address)" --rpc-url $CELO_RPC_URL
# Debe retornar: $AGENT_ADDRESS

# Verificar LootAccessRegistry
cast call $REGISTRY_ADDRESS "owner()(address)" --rpc-url $CELO_RPC_URL
# Debe retornar: $AGENT_ADDRESS

# Verificar LootBoxMinter
cast call $MINTER_ADDRESS "owner()(address)" --rpc-url $CELO_RPC_URL
# Debe retornar: $AGENT_ADDRESS
```

## 🎯 Paso 3: Configurar cUSD Address (Ya incluido en deployment)

Asegúrate de tener la dirección correcta de cUSD en tu `.env`:

```bash
# Celo Sepolia
CUSD_ADDRESS="0x874069Fa1Eb16D44d622F2e0Ca25eeA172369bC1"

# Celo Mainnet (cuando lances)
# CUSD_ADDRESS="0x765DE816845861e75A25fCA122bb6898B8B1282a"
```

## 🔄 Cómo Funciona en Producción

1. **Detección de Tendencias**: El `TrendWatcherAgent` detecta un cast viral en Farcaster
2. **Generación de Campaign ID**: Se crea un `campaign_id` único basado en el cast (ej: `cast-0x812abc-loot`)
3. **Configuración Automática**: El `RewardDistributorAgent` configura automáticamente la campaña en:
   - ✅ `LootAccessRegistry`: Cooldown de 1 día
   - ✅ `LootBoxMinter`: Metadata base para NFTs
   - ✅ `LootBoxVault`: Inicialización con token cUSD y reward amount
4. **Distribución**: Las recompensas se distribuyen usando la campaña recién creada

## 💰 Fondos en LootBoxVault

Para que las campañas de cUSD funcionen desde el vault, necesitas depositar fondos:

```bash
# 1. Aprobar el vault para transferir tus cUSD
cast send $CUSD_ADDRESS \
    "approve(address,uint256)" \
    $LOOTBOX_VAULT_ADDRESS \
    $(cast --to-wei 1000 ether) \
    --private-key $DEPLOYER_PRIVATE_KEY \
    --rpc-url $CELO_RPC_URL

# 2. Depositar fondos en la campaña (después de que se cree)
# Nota: Esto debe hacerse DESPUÉS de que el agente cree la campaña
cast send $LOOTBOX_VAULT_ADDRESS \
    "fundCampaign(bytes32,uint256)" \
    $(cast keccak "cast-0x812abc-loot") \
    $(cast --to-wei 100 ether) \
    --private-key $DEPLOYER_PRIVATE_KEY \
    --rpc-url $CELO_RPC_URL
```

**Alternativa**: Usa MiniPay Tool API para cUSD (no requiere fondos en vault):
- Configura `MINIPAY_PROJECT_SECRET` en `.env`
- El sistema usará la API en lugar del vault

## 📊 Monitoreo de Campañas

Para ver qué campañas están activas:

```bash
# Ver campaña en Registry
cast call $REGISTRY_ADDRESS \
    "campaignRules(bytes32)(uint64,bool)" \
    $(cast keccak "cast-0x812abc-loot") \
    --rpc-url $CELO_RPC_URL

# Ver campaña en Minter
cast call $MINTER_ADDRESS \
    "campaigns(bytes32)(string,bool)" \
    $(cast keccak "cast-0x812abc-loot") \
    --rpc-url $CELO_RPC_URL

# Ver campaña en Vault
cast call $LOOTBOX_VAULT_ADDRESS \
    "getCampaign(bytes32)(address,uint96,uint256,bool)" \
    $(cast keccak "cast-0x812abc-loot") \
    --rpc-url $CELO_RPC_URL
```

## 🔒 Seguridad

- **Private Key del Agente**: Debe estar en un lugar seguro (variables de entorno, no en código)
- **Límites de Recompensas**: Configurados en `.env` (`MAX_REWARD_RECIPIENTS`, `MAX_ONCHAIN_REWARDS`)
- **Cooldowns**: Las campañas tienen cooldown de 1 día para evitar spam
- **Validación On-chain**: El `LootAccessRegistry` previene doble gasto

## 🎯 Resumen

✅ **Campañas Reales**: Se crean automáticamente cuando se detectan tendencias
✅ **Sin Intervención Manual**: El agente configura todo automáticamente
✅ **Producción Ready**: Listo para lanzar con campañas dinámicas

