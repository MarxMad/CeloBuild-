# 🚀 Deployment en Celo Mainnet

## ⚠️ IMPORTANTE: Producción Real

Este deployment es para **CELO MAINNET** (red principal). Las transacciones costarán **CELO real**.

## 📋 Prerrequisitos

1. **Tener Foundry instalado**: `foundryup`
2. **Tener CELO en tu wallet** para pagar gas fees
3. **Configurar variables de entorno**:
   ```bash
   export DEPLOYER_PRIVATE_KEY=0x...  # Tu private key para desplegar
   export AGENT_ADDRESS=0x...          # Dirección del agente (backend)
   export CELO_RPC_URL=https://rpc.ankr.com/celo  # RPC de Mainnet
   export CUSD_ADDRESS=0x765DE816845861e75A25fCA122bb6898B8B1282a  # cUSD en Mainnet
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

## 🚀 Paso 2: Desplegar contratos en Mainnet

```bash
cd apps/contracts

# Usar el script automático (recomendado)
./deploy-mainnet.sh

# O manualmente:
forge script script/DeployMainnet.s.sol:DeployMainnet \
    --rpc-url https://rpc.ankr.com/celo \
    --broadcast \
    --verify \
    -vvv
```

**Nota:** El script `DeployMainnet` incluye:
- ✅ Deployment de los 3 contratos en Celo Mainnet
- ✅ Configuración de roles para el agente
- ✅ Transferencia de ownership al agente (para campañas dinámicas)
- ✅ Configuración de campaña demo (opcional)
- ✅ Uso de cUSD oficial de Mainnet

## 📝 Paso 3: Guardar direcciones en .env

Después del deployment, copia las direcciones mostradas y agrégalas a `apps/agents/.env`:

```bash
# Celo Mainnet
CELO_RPC_URL="https://rpc.ankr.com/celo"
CUSD_ADDRESS="0x765DE816845861e75A25fCA122bb6898B8B1282a"
LOOTBOX_VAULT_ADDRESS="0x..."
REGISTRY_ADDRESS="0x..."
MINTER_ADDRESS="0x..."
```

## ⚙️ Paso 4: Fondear el Vault con cUSD

Para que el sistema pueda distribuir recompensas en cUSD, necesitas fondear el Vault:

```bash
# 1. Aprobar cUSD para el Vault
cast send 0x765DE816845861e75A25fCA122bb6898B8B1282a \
    "approve(address,uint256)" \
    $LOOTBOX_VAULT_ADDRESS \
    $(cast --to-wei 1000 ether) \
    --private-key $DEPLOYER_PRIVATE_KEY \
    --rpc-url https://rpc.ankr.com/celo

# 2. Fondear campaña demo (opcional)
cast send $LOOTBOX_VAULT_ADDRESS \
    "fundCampaign(bytes32,uint256)" \
    $(cast keccak "demo-campaign") \
    $(cast --to-wei 100 ether) \
    --private-key $DEPLOYER_PRIVATE_KEY \
    --rpc-url https://rpc.ankr.com/celo
```

## ✅ Verificación

Verifica que los roles estén configurados:

```bash
# Verificar que el agente tiene rol en LootBoxMinter
cast call $MINTER_ADDRESS "agents(address)" $AGENT_ADDRESS --rpc-url https://rpc.ankr.com/celo

# Verificar que el agente tiene rol en LootAccessRegistry
cast call $REGISTRY_ADDRESS "reporters(address)" $AGENT_ADDRESS --rpc-url https://rpc.ankr.com/celo

# Verificar que el agente tiene rol en LootBoxVault
cast call $LOOTBOX_VAULT_ADDRESS "agents(address)" $AGENT_ADDRESS --rpc-url https://rpc.ankr.com/celo
```

Todos deberían retornar `true`.

## 🔗 Direcciones Oficiales de Celo Mainnet

- **cUSD**: `0x765DE816845861e75A25fCA122bb6898B8B1282a`
- **cEUR**: `0xD8763CBa276a3738E6DE85b4b3bF5FDed6D6cA73`
- **CELO**: Native token (no tiene contrato)
- **Explorer**: https://celoscan.io

## 🎯 Resumen

- ✅ Contratos desplegados en Celo Mainnet
- ✅ Roles configurados (agente puede distribuir)
- ✅ Campaña demo configurada
- ✅ Direcciones guardadas en .env
- ✅ **Usuario NO necesita firmar** - todo es automático
- ⚠️ **Producción real** - usa CELO y cUSD reales

## ⚠️ Advertencias

1. **Gas Fees**: Cada transacción en Mainnet cuesta CELO real
2. **cUSD Real**: Las recompensas distribuidas serán cUSD reales
3. **Irreversible**: Las transacciones en Mainnet son permanentes
4. **Seguridad**: Asegúrate de que tu `CELO_PRIVATE_KEY` esté segura

