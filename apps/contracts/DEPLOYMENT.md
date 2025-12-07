# 🚀 Guía de Deployment de Contratos

## ⚠️ IMPORTANTE: Flujo de Recompensas

**El usuario NO necesita firmar transacciones para recibir premios.**

El sistema funciona así:
1. **Backend (agente)** detecta tendencias y usuarios elegibles
2. **Backend** distribuye automáticamente las recompensas usando su `CELO_PRIVATE_KEY`
3. **Usuario** recibe la recompensa directamente en su wallet (NFT, cUSD, o XP)
4. **No hay interacción del usuario** - todo es automático

## 📋 Prerrequisitos

1. **Tener Foundry instalado**: `foundryup`
2. **Tener una cuenta con CELO** en Celo Sepolia para pagar gas
3. **Configurar variables de entorno**:
   ```bash
   export DEPLOYER_PRIVATE_KEY=0x...  # Tu private key para desplegar
   export AGENT_ADDRESS=0x...          # Dirección del agente (backend)
   export CELO_RPC_URL=https://celo-sepolia.infura.io/v3/YOUR_KEY
   ```

## 🔧 Paso 1: Obtener la dirección del agente

La dirección del agente debe ser la cuenta que usa el backend (derivada de `CELO_PRIVATE_KEY`):

```bash
# Si tienes CELO_PRIVATE_KEY configurada
cast wallet address --private-key $CELO_PRIVATE_KEY

# O desde el código Python:
python3 -c "
from web3 import Web3
from eth_account import Account
key = 'TU_PRIVATE_KEY_AQUI'
account = Account.from_key(key)
print(account.address)
"
```

## 🚀 Paso 2: Desplegar contratos

```bash
cd apps/contracts

# Opción 1: Usar el script automático (recomendado)
./deploy.sh

# Opción 2: Manual
forge script script/DeployAndSetup.s.sol:DeployAndSetup \
    --rpc-url $CELO_RPC_URL \
    --broadcast \
    --verify \
    -vvv
```

## 📝 Paso 3: Guardar direcciones en .env

Después del deployment, copia las direcciones mostradas y agrégalas a `apps/agents/.env`:

```bash
LOOTBOX_VAULT_ADDRESS="0x..."
REGISTRY_ADDRESS="0x..."
MINTER_ADDRESS="0x..."
```

## ⚙️ Paso 4: Configurar campañas (opcional)

El script ya configura una campaña demo, pero puedes crear más:

```bash
# Configurar campaña en LootAccessRegistry (cooldown de 1 día)
cast send $REGISTRY_ADDRESS \
    "configureCampaign(bytes32,uint64)" \
    $(cast keccak "mi-campana") \
    86400 \
    --private-key $DEPLOYER_PRIVATE_KEY \
    --rpc-url $CELO_RPC_URL

# Configurar campaña en LootBoxMinter
cast send $MINTER_ADDRESS \
    "configureCampaign(bytes32,string)" \
    $(cast keccak "mi-campana") \
    "ipfs://QmExample/" \
    --private-key $DEPLOYER_PRIVATE_KEY \
    --rpc-url $CELO_RPC_URL

# Inicializar campaña en LootBoxVault (requiere token cUSD)
# Primero necesitas aprobar y depositar cUSD en el vault
cast send $CUSD_ADDRESS \
    "approve(address,uint256)" \
    $LOOTBOX_VAULT_ADDRESS \
    $(cast --to-wei 1000 ether) \
    --private-key $DEPLOYER_PRIVATE_KEY \
    --rpc-url $CELO_RPC_URL

cast send $LOOTBOX_VAULT_ADDRESS \
    "fundCampaign(bytes32,uint256)" \
    $(cast keccak "mi-campana") \
    $(cast --to-wei 100 ether) \
    --private-key $DEPLOYER_PRIVATE_KEY \
    --rpc-url $CELO_RPC_URL
```

## ✅ Verificación

Verifica que los roles estén configurados:

```bash
# Verificar que el agente tiene rol en LootBoxMinter
cast call $MINTER_ADDRESS "agents(address)" $AGENT_ADDRESS --rpc-url $CELO_RPC_URL

# Verificar que el agente tiene rol en LootAccessRegistry
cast call $REGISTRY_ADDRESS "reporters(address)" $AGENT_ADDRESS --rpc-url $CELO_RPC_URL

# Verificar que el agente tiene rol en LootBoxVault
cast call $LOOTBOX_VAULT_ADDRESS "agents(address)" $AGENT_ADDRESS --rpc-url $CELO_RPC_URL
```

Todos deberían retornar `true`.

## 🎯 Resumen

- ✅ Contratos desplegados
- ✅ Roles configurados (agente puede distribuir)
- ✅ Campaña demo configurada
- ✅ Direcciones guardadas en .env
- ✅ **Usuario NO necesita firmar** - todo es automático

