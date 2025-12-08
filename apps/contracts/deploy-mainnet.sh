#!/bin/bash

# Script de deployment para CELO MAINNET
# Despliega contratos con mejoras de seguridad y configura ownership del agente

set -e

echo "🚀 Deployment para CELO MAINNET - Premio.xyz"
echo ""

# Verificar que las variables de entorno estén configuradas
if [ -z "$DEPLOYER_PRIVATE_KEY" ]; then
    echo "❌ Error: DEPLOYER_PRIVATE_KEY no está configurada"
    echo "   Configúrala: export DEPLOYER_PRIVATE_KEY=0x..."
    exit 1
fi

if [ -z "$AGENT_ADDRESS" ]; then
    echo "❌ Error: AGENT_ADDRESS no está configurada"
    echo "   Esta es la dirección de la cuenta que usará el backend (debe coincidir con CELO_PRIVATE_KEY)"
    echo "   Puedes obtenerla ejecutando: cast wallet address --private-key \$CELO_PRIVATE_KEY"
    exit 1
fi

# Configurar RPC de Celo Mainnet (Ankr)
CELO_RPC_URL="${CELO_RPC_URL:-https://rpc.ankr.com/celo}"
CUSD_ADDRESS="${CUSD_ADDRESS:-0x765DE816845861e75A25fCA122bb6898B8B1282a}"

echo "📡 Configuración de red:"
echo "   RPC URL: $CELO_RPC_URL"
echo "   cUSD Address: $CUSD_ADDRESS"
echo ""

# Verificar que estamos en Celo Mainnet
echo "📡 Verificando red..."
CHAIN_ID=$(cast chain-id --rpc-url "$CELO_RPC_URL" 2>/dev/null || echo "unknown")
if [ "$CHAIN_ID" != "42220" ]; then
    echo "❌ Error: No estás en Celo Mainnet (chain ID: 42220)"
    echo "   Chain ID actual: $CHAIN_ID"
    echo "   Verifica que CELO_RPC_URL apunte a Celo Mainnet"
    exit 1
fi

echo "✅ Red verificada: Celo Mainnet (Chain ID: 42220)"
echo ""

# Verificar balance de CELO para gas
echo "💰 Verificando balance de CELO..."
DEPLOYER_ADDRESS=$(cast wallet address --private-key "$DEPLOYER_PRIVATE_KEY")
BALANCE=$(cast balance "$DEPLOYER_ADDRESS" --rpc-url "$CELO_RPC_URL" 2>/dev/null || echo "0")
BALANCE_CELO=$(echo "scale=4; $BALANCE / 1000000000000000000" | bc 2>/dev/null || echo "unknown")

echo "   Deployer address: $DEPLOYER_ADDRESS"
echo "   Balance: $BALANCE_CELO CELO"
echo ""

if [ "$BALANCE" = "0" ] || [ -z "$BALANCE" ]; then
    echo "⚠️  Advertencia: Balance de CELO es 0 o no se pudo verificar"
    echo "   Necesitas CELO para pagar gas fees en Mainnet"
    echo "   Puedes obtener CELO en: https://celo.org/developers/faucet"
    read -p "¿Continuar de todas formas? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Confirmar deployment
echo "⚠️  IMPORTANTE: Este script:"
echo "   1. Desplegará los contratos en CELO MAINNET (red principal)"
echo "   2. Configurará roles para el agente"
echo "   3. TRANSFERIRÁ OWNERSHIP al agente (para campañas dinámicas)"
echo "   4. Usará cUSD real de Mainnet"
echo ""
echo "   ⚠️  ESTO ES PRODUCCIÓN - Las transacciones costarán CELO real"
echo ""
read -p "¿Continuar con el deployment en MAINNET? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelado"
    exit 1
fi

# Ejecutar el script de deployment
echo ""
echo "📝 Ejecutando script de deployment..."
forge script script/DeployMainnet.s.sol:DeployMainnet \
    --rpc-url "$CELO_RPC_URL" \
    --broadcast \
    --verify \
    -vvv

# Extraer direcciones del broadcast
echo ""
echo "📋 Extrayendo direcciones del deployment..."

CHAIN_ID=$(cast chain-id --rpc-url "$CELO_RPC_URL")
BROADCAST_FILE="broadcast/DeployMainnet.s.sol/$CHAIN_ID/run-latest.json"

if [ ! -f "$BROADCAST_FILE" ]; then
    echo "❌ No se encontró el archivo de broadcast. Verifica que el deployment fue exitoso."
    exit 1
fi

# Extraer direcciones usando jq (si está disponible) o manualmente
if command -v jq &> /dev/null; then
    VAULT=$(jq -r '.transactions[] | select(.contractName=="LootBoxVault") | .contractAddress' "$BROADCAST_FILE" | head -1)
    REGISTRY=$(jq -r '.transactions[] | select(.contractName=="LootAccessRegistry") | .contractAddress' "$BROADCAST_FILE" | head -1)
    MINTER=$(jq -r '.transactions[] | select(.contractName=="LootBoxMinter") | .contractAddress' "$BROADCAST_FILE" | head -1)
else
    echo "⚠️  jq no está instalado. Extrae las direcciones manualmente del output anterior."
    VAULT=""
    REGISTRY=""
    MINTER=""
fi

# Mostrar resumen
echo ""
echo "========================================"
echo "✅ DEPLOYMENT COMPLETADO EN MAINNET"
echo "========================================"
if [ -n "$VAULT" ]; then
    echo ""
    echo "Agrega estas direcciones a tu archivo apps/agents/.env:"
    echo ""
    echo "CELO_RPC_URL=\"$CELO_RPC_URL\""
    echo "CUSD_ADDRESS=\"$CUSD_ADDRESS\""
    echo "LOOTBOX_VAULT_ADDRESS=\"$VAULT\""
    echo "REGISTRY_ADDRESS=\"$REGISTRY\""
    echo "MINTER_ADDRESS=\"$MINTER\""
    echo ""
    echo "Explorer links (Celo Mainnet):"
    echo "  Vault: https://celoscan.io/address/$VAULT"
    echo "  Registry: https://celoscan.io/address/$REGISTRY"
    echo "  Minter: https://celoscan.io/address/$MINTER"
    echo ""
    echo "⚠️  IMPORTANTE:"
    echo "   - Estas son direcciones en MAINNET (red principal)"
    echo "   - Actualiza CELO_RPC_URL en tu backend a: $CELO_RPC_URL"
    echo "   - Asegúrate de tener CELO en tu wallet para gas fees"
fi
echo ""
echo "🎉 El agente ahora puede crear campañas dinámicas automáticamente en MAINNET!"

