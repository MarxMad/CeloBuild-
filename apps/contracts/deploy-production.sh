#!/bin/bash

# Script de deployment para PRODUCCIÓN
# Despliega contratos con mejoras de seguridad y configura ownership del agente

set -e

echo "🚀 Deployment para PRODUCCIÓN - Premio.xyz"
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

if [ -z "$CELO_RPC_URL" ]; then
    echo "❌ Error: CELO_RPC_URL no está configurada"
    echo "   Configúrala: export CELO_RPC_URL=https://..."
    exit 1
fi

# CUSD_ADDRESS es opcional (solo para inicializar campaña demo)
if [ -z "$CUSD_ADDRESS" ]; then
    echo "⚠️  Advertencia: CUSD_ADDRESS no está configurada"
    echo "   La campaña demo no se inicializará en el Vault"
    echo "   Puedes configurarla: export CUSD_ADDRESS=0x..."
    echo ""
fi

# Verificar que estamos en la red correcta (Celo Sepolia)
echo "📡 Verificando red..."
CHAIN_ID=$(cast chain-id --rpc-url "$CELO_RPC_URL" 2>/dev/null || echo "unknown")
if [ "$CHAIN_ID" != "11142220" ]; then
    echo "⚠️  Advertencia: No estás en Celo Sepolia (chain ID: 11142220)"
    echo "   Chain ID actual: $CHAIN_ID"
    read -p "¿Continuar de todas formas? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "✅ Red verificada"
echo ""

# Confirmar deployment
echo "⚠️  IMPORTANTE: Este script:"
echo "   1. Desplegará los contratos con mejoras de seguridad"
echo "   2. Configurará roles para el agente"
echo "   3. TRANSFERIRÁ OWNERSHIP al agente (para campañas dinámicas)"
echo ""
read -p "¿Continuar con el deployment? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelado"
    exit 1
fi

# Ejecutar el script de deployment
echo ""
echo "📝 Ejecutando script de deployment..."
forge script script/DeployProduction.s.sol:DeployProduction \
    --rpc-url "$CELO_RPC_URL" \
    --broadcast \
    --verify \
    -vvv

# Extraer direcciones del broadcast
echo ""
echo "📋 Extrayendo direcciones del deployment..."

BROADCAST_FILE="broadcast/DeployProduction.s.sol/$(cast chain-id --rpc-url "$CELO_RPC_URL")/run-latest.json"

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
echo "✅ DEPLOYMENT COMPLETADO"
echo "========================================"
if [ -n "$VAULT" ]; then
    echo ""
    echo "Agrega estas direcciones a tu archivo apps/agents/.env:"
    echo ""
    echo "LOOTBOX_VAULT_ADDRESS=\"$VAULT\""
    echo "REGISTRY_ADDRESS=\"$REGISTRY\""
    echo "MINTER_ADDRESS=\"$MINTER\""
    echo ""
    echo "Explorer links:"
    echo "  Vault: https://celo-sepolia.blockscout.com/address/$VAULT"
    echo "  Registry: https://celo-sepolia.blockscout.com/address/$REGISTRY"
    echo "  Minter: https://celo-sepolia.blockscout.com/address/$MINTER"
fi
echo ""
echo "🎉 El agente ahora puede crear campañas dinámicas automáticamente!"

