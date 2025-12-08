# 🚀 Deployment Inmediato - Premio.xyz

## ✅ Estado: LISTO PARA PRODUCCIÓN

Todos los componentes están listos:
- ✅ Contratos compilados con mejoras de seguridad
- ✅ Scripts de deployment optimizados
- ✅ Validaciones de seguridad implementadas
- ✅ Documentación completa

## 📋 Pasos para Desplegar

### 1. Configurar Variables de Entorno

```bash
cd apps/contracts

# Variables REQUERIDAS
export DEPLOYER_PRIVATE_KEY=0x...  # Tu private key para desplegar
export AGENT_ADDRESS=0x...          # Dirección del agente (derivada de CELO_PRIVATE_KEY)
export CELO_RPC_URL=https://...    # RPC de Celo Sepolia

# Variables OPCIONALES
export CUSD_ADDRESS=0x874069Fa1Eb16D44d622F2e0Ca25eeA172369bC1  # cUSD en Sepolia
```

### 2. Obtener AGENT_ADDRESS

Si tienes `CELO_PRIVATE_KEY` configurada en `apps/agents/.env`:

```bash
# Opción 1: Usando cast
cast wallet address --private-key $CELO_PRIVATE_KEY

# Opción 2: Desde Python
cd apps/agents
python3 -c "
from web3 import Web3
from eth_account import Account
import os
from dotenv import load_dotenv
load_dotenv('.env')
key = os.getenv('CELO_PRIVATE_KEY')
if key:
    account = Account.from_key(key)
    print(account.address)
"
```

### 3. Ejecutar Deployment

```bash
cd apps/contracts
chmod +x deploy-production.sh
./deploy-production.sh
```

El script:
- ✅ Desplegará los 3 contratos
- ✅ Configurará roles para el agente
- ✅ Transferirá ownership al agente (para campañas dinámicas)
- ✅ Configurará campaña demo (opcional)

### 4. Guardar Direcciones en .env

Después del deployment, copia las direcciones mostradas y agrégalas a `apps/agents/.env`:

```bash
LOOTBOX_VAULT_ADDRESS="0x..."
REGISTRY_ADDRESS="0x..."
MINTER_ADDRESS="0x..."
CUSD_ADDRESS="0x874069Fa1Eb16D44d622F2e0Ca25eeA172369bC1"
```

### 5. Verificar Deployment

```bash
# Verificar ownership del agente
cast call $LOOTBOX_VAULT_ADDRESS "owner()(address)" --rpc-url $CELO_RPC_URL
cast call $REGISTRY_ADDRESS "owner()(address)" --rpc-url $CELO_RPC_URL
cast call $MINTER_ADDRESS "owner()(address)" --rpc-url $CELO_RPC_URL

# Todos deben retornar: $AGENT_ADDRESS
```

## 🎯 Siguiente Paso

Una vez desplegado, el sistema está listo para:
- ✅ Detectar tendencias automáticamente (cada 30 minutos)
- ✅ Crear campañas dinámicas cuando se detecten tendencias
- ✅ Distribuir recompensas (NFT, cUSD, XP) automáticamente

¡Todo está listo para producción! 🚀

