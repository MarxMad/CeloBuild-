# 🚀 Guía Rápida: Deployment en Celo Mainnet

## ⚠️ IMPORTANTE
Este deployment es para **CELO MAINNET** (producción real). Las transacciones costarán **CELO y cUSD reales**.

## 📋 Checklist Pre-Deployment

- [ ] Tener Foundry instalado (`foundryup`)
- [ ] Tener CELO en tu wallet para gas fees (mínimo 0.5 CELO recomendado)
- [ ] Tener cUSD para fondear el Vault (opcional, mínimo 10 cUSD recomendado)
- [ ] Tener `DEPLOYER_PRIVATE_KEY` configurada
- [ ] Tener `AGENT_ADDRESS` (dirección del backend)

## 🔧 Paso 1: Obtener la dirección del agente

La dirección del agente debe coincidir con la cuenta que usa el backend:

```bash
# Opción 1: Si tienes CELO_PRIVATE_KEY configurada
cast wallet address --private-key $CELO_PRIVATE_KEY

# Opción 2: Desde Python (si tienes el backend corriendo)
python3 -c "
from web3 import Web3
from eth_account import Account
import os
key = os.getenv('CELO_PRIVATE_KEY', 'TU_PRIVATE_KEY_AQUI')
account = Account.from_key(key)
print('AGENT_ADDRESS:', account.address)
"
```

## 🚀 Paso 2: Configurar variables de entorno

```bash
export DEPLOYER_PRIVATE_KEY=0x...  # Tu private key para desplegar
export AGENT_ADDRESS=0x...          # Dirección obtenida en Paso 1
export CELO_RPC_URL=https://rpc.ankr.com/celo
export CUSD_ADDRESS=0x765DE816845861e75A25fCA122bb6898B8B1282a
```

## 📦 Paso 3: Desplegar contratos

```bash
cd apps/contracts

# Ejecutar el script de deployment
./deploy-mainnet.sh
```

El script:
- ✅ Verifica que estás en Celo Mainnet (Chain ID: 42220)
- ✅ Verifica tu balance de CELO
- ✅ Despliega los 3 contratos (Vault, Registry, Minter)
- ✅ Configura roles para el agente
- ✅ Transfiere ownership al agente
- ✅ Configura campaña demo con cUSD de Mainnet

## 📝 Paso 4: Guardar direcciones en .env

Después del deployment, copia las direcciones mostradas y agrégalas a `apps/agents/.env`:

```bash
# Celo Mainnet
CELO_RPC_URL="https://rpc.ankr.com/celo"
CUSD_ADDRESS="0x765DE816845861e75A25fCA122bb6898B8B1282a"
LOOTBOX_VAULT_ADDRESS="0x..."  # Copiar del output del deployment
REGISTRY_ADDRESS="0x..."        # Copiar del output del deployment
MINTER_ADDRESS="0x..."         # Copiar del output del deployment
CELO_PRIVATE_KEY="0x..."       # La misma que usaste para AGENT_ADDRESS
```

## 💰 Paso 5: Fondear el Vault con cUSD

Para que el sistema pueda distribuir recompensas en cUSD, necesitas fondear el Vault:

```bash
# 1. Aprobar cUSD para el Vault (ejemplo: 1000 cUSD)
cast send 0x765DE816845861e75A25fCA122bb6898B8B1282a \
    "approve(address,uint256)" \
    $LOOTBOX_VAULT_ADDRESS \
    $(cast --to-wei 1000 ether) \
    --private-key $DEPLOYER_PRIVATE_KEY \
    --rpc-url https://rpc.ankr.com/celo

# 2. Fondear campaña demo (ejemplo: 100 cUSD)
cast send $LOOTBOX_VAULT_ADDRESS \
    "fundCampaign(bytes32,uint256)" \
    $(cast keccak "demo-campaign") \
    $(cast --to-wei 100 ether) \
    --private-key $DEPLOYER_PRIVATE_KEY \
    --rpc-url https://rpc.ankr.com/celo
```

**Nota:** El agente puede crear campañas dinámicas automáticamente, pero necesitas fondearlas antes de que puedan distribuir recompensas.

## ✅ Paso 6: Verificar deployment

```bash
# Verificar que el agente tiene rol en LootBoxMinter
cast call $MINTER_ADDRESS "agents(address)" $AGENT_ADDRESS --rpc-url https://rpc.ankr.com/celo

# Verificar que el agente tiene rol en LootAccessRegistry
cast call $REGISTRY_ADDRESS "reporters(address)" $AGENT_ADDRESS --rpc-url https://rpc.ankr.com/celo

# Verificar que el agente tiene rol en LootBoxVault
cast call $LOOTBOX_VAULT_ADDRESS "agents(address)" $AGENT_ADDRESS --rpc-url https://rpc.ankr.com/celo

# Verificar balance del Vault para la campaña demo
cast call $LOOTBOX_VAULT_ADDRESS \
    "getCampaign(bytes32)" \
    $(cast keccak "demo-campaign") \
    --rpc-url https://rpc.ankr.com/celo
```

Todos los roles deberían retornar `true`, y el balance del Vault debería mostrar el monto que fondaste.

## 🔄 Paso 7: Actualizar backend

1. **Actualizar variables de entorno en Vercel/Railway:**
   - Ve a tu proyecto del backend en Vercel/Railway
   - Ve a **Settings → Environment Variables**
   - Actualiza:
     - `CELO_RPC_URL` → `https://rpc.ankr.com/celo`
     - `CUSD_ADDRESS` → `0x765DE816845861e75A25fCA122bb6898B8B1282a`
     - `LOOTBOX_VAULT_ADDRESS` → (dirección del deployment)
     - `REGISTRY_ADDRESS` → (dirección del deployment)
     - `MINTER_ADDRESS` → (dirección del deployment)
     - `CELO_PRIVATE_KEY` → (debe coincidir con AGENT_ADDRESS)

2. **Redeploy el backend:**
   - En Vercel: **Deployments → ⋯ → Redeploy**
   - En Railway: El redeploy es automático al hacer push

## 🎯 Resumen

- ✅ Contratos desplegados en Celo Mainnet
- ✅ Roles configurados (agente puede distribuir)
- ✅ Campaña demo configurada con cUSD de Mainnet
- ✅ Vault fondeado con cUSD
- ✅ Backend actualizado con nuevas direcciones
- ✅ **Usuario NO necesita firmar** - todo es automático
- ⚠️ **Producción real** - usa CELO y cUSD reales

## 🔗 Enlaces Útiles

- **Explorer**: https://celoscan.io
- **RPC**: https://rpc.ankr.com/celo
- **cUSD Mainnet**: `0x765DE816845861e75A25fCA122bb6898B8B1282a`
- **Chain ID**: 42220

## ⚠️ Advertencias Finales

1. **Gas Fees**: Cada transacción en Mainnet cuesta CELO real (aprox. 0.001-0.01 CELO por transacción)
2. **cUSD Real**: Las recompensas distribuidas serán cUSD reales
3. **Irreversible**: Las transacciones en Mainnet son permanentes
4. **Seguridad**: 
   - Asegúrate de que tu `CELO_PRIVATE_KEY` esté segura
   - No compartas tu private key
   - Usa un wallet dedicado para el agente
   - Considera usar un multisig para el ownership del Vault

## 🆘 Troubleshooting

### Error: "insufficient funds for gas"
- Asegúrate de tener CELO en tu wallet (mínimo 0.5 CELO)

### Error: "execution reverted"
- Verifica que el agente tenga los roles correctos
- Verifica que el Vault tenga fondos suficientes

### Error: "campaign not initialized"
- El agente creará campañas dinámicamente
- Para la campaña demo, asegúrate de que esté inicializada en el script de deployment

