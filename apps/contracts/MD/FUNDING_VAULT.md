# 💰 Cómo Depositar Fondos en LootBoxVault

## 🎯 Problema

El `LootBoxVault` necesita fondos cUSD depositados para poder distribuir recompensas cuando los usuarios seleccionan "cUSD Drop" y no tienes la API de MiniPay configurada.

## ✅ Solución: Depositar Fondos

### Opción 1: Usar el Script Automatizado (Recomendado)

```bash
cd apps/contracts

# Configurar variables (si no están en .env)
# Usa CELO_PRIVATE_KEY (del agente) o DEPLOYER_PRIVATE_KEY
export CELO_PRIVATE_KEY="tu_private_key"  # O DEPLOYER_PRIVATE_KEY
export CELO_RPC_URL="https://celo-sepolia.infura.io/v3/tu_key"
export LOOTBOX_VAULT_ADDRESS="0x..."
export CUSD_ADDRESS="0x874069Fa1Eb16D44d622F2e0Ca25eeA172369bC1"

# Depositar 100 cUSD en demo-campaign (por defecto)
./fund-campaign.sh

# O depositar en una campaña específica con cantidad personalizada
CAMPAIGN_ID="cast-0x812abc-loot" FUND_AMOUNT_CUSD=50 ./fund-campaign.sh
```

### Opción 2: Usar Foundry Script

```bash
cd apps/contracts

# Configurar variables en .env
export CAMPAIGN_ID="demo-campaign"  # o el nombre de tu campaña
export FUND_AMOUNT=100000000000000000000  # 100 cUSD en wei

# Ejecutar script
forge script script/FundCampaign.s.sol:FundCampaign \
    --rpc-url $CELO_RPC_URL \
    --broadcast \
    --private-key $DEPLOYER_PRIVATE_KEY \
    --chain celo-sepolia
```

### Opción 3: Manual con `cast`

```bash
# Usar CELO_PRIVATE_KEY (del agente) o DEPLOYER_PRIVATE_KEY
PRIVATE_KEY="${CELO_PRIVATE_KEY:-$DEPLOYER_PRIVATE_KEY}"

# 1. Aprobar el vault para transferir cUSD
cast send $CUSD_ADDRESS \
    "approve(address,uint256)" \
    $LOOTBOX_VAULT_ADDRESS \
    $(cast --to-wei 100 ether) \
    --private-key $PRIVATE_KEY \
    --rpc-url $CELO_RPC_URL \
    --chain celo-sepolia

# 2. Calcular campaign_id
CAMPAIGN_ID=$(cast keccak "demo-campaign")
# O para una campaña específica:
# CAMPAIGN_ID=$(cast keccak "cast-0x812abc-loot")

# 3. Depositar fondos
cast send $LOOTBOX_VAULT_ADDRESS \
    "fundCampaign(bytes32,uint256)" \
    $CAMPAIGN_ID \
    $(cast --to-wei 100 ether) \
    --private-key $PRIVATE_KEY \
    --rpc-url $CELO_RPC_URL \
    --chain celo-sepolia
```

## 📋 Verificar Fondos Depositados

```bash
# Ver información de la campaña
cast call $LOOTBOX_VAULT_ADDRESS \
    "getCampaign(bytes32)" \
    $(cast keccak "demo-campaign") \
    --rpc-url $CELO_RPC_URL

# Esto retornará:
# - token: dirección del token cUSD
# - rewardPerRecipient: cantidad por recipient (ej: 0.15 cUSD)
# - remainingBudget: fondos restantes disponibles
# - active: si la campaña está activa
```

## 🔄 Para Campañas Dinámicas

Cuando el agente crea una campaña dinámica (basada en un cast de Farcaster), el `campaign_id` se genera automáticamente. Para depositar fondos en estas campañas:

1. **Esperar a que se cree la campaña**: El agente la inicializa automáticamente
2. **Obtener el campaign_id**: Revisa los logs del backend o calcula:
   ```bash
   # Si el cast hash es 0x812abc...
   CAMPAIGN_ID=$(cast keccak "cast-0x812abc-loot")
   ```
3. **Depositar fondos**: Usa el script o `cast` con ese `campaign_id`

## 💡 Alternativa: Usar MiniPay Tool API

Si tienes acceso a la API de MiniPay Tool, puedes evitar depositar fondos en el vault:

1. Configura `MINIPAY_PROJECT_SECRET` en `apps/agents/.env`
2. El sistema usará la API de MiniPay en lugar del vault
3. No necesitas depositar fondos manualmente

## ⚠️ Notas Importantes

- **Solo el owner puede depositar fondos**: Asegúrate de que tu wallet sea el owner del vault
- **Aprobar antes de depositar**: Siempre aprueba el vault antes de llamar a `fundCampaign`
- **Cantidad suficiente**: Deposita suficiente para cubrir múltiples recompensas (ej: 100 cUSD para ~666 recompensas de 0.15 cUSD)
- **Campañas dinámicas**: Las campañas se crean automáticamente, pero los fondos deben depositarse manualmente (o automatizarse con un script)

## 🚀 Automatización Futura

Para producción, considera:
- Un script que monitoree nuevas campañas y deposite fondos automáticamente
- Un fondo de reserva que se recargue automáticamente
- Integración con MiniPay Tool API para evitar gestión manual de fondos

