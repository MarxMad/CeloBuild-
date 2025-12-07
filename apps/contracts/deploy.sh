#!/bin/bash

# Script para desplegar y configurar los contratos de Premio.xyz
# IMPORTANTE: El usuario NO necesita firmar transacciones. El backend distribuye automáticamente.

set -e

echo "🚀 Desplegando contratos de Premio.xyz..."

# Verificar que las variables de entorno estén configuradas
if [ -z "$DEPLOYER_PRIVATE_KEY" ]; then
    echo "❌ Error: DEPLOYER_PRIVATE_KEY no está configurada"
    echo "   Configúrala en tu .env o exporta: export DEPLOYER_PRIVATE_KEY=0x..."
    exit 1
fi

if [ -z "$AGENT_ADDRESS" ]; then
    echo "❌ Error: AGENT_ADDRESS no está configurada"
    echo "   Esta es la dirección de la cuenta que usará el backend (debe coincidir con CELO_PRIVATE_KEY)"
    echo "   Puedes obtenerla ejecutando: cast wallet address --private-key \$CELO_PRIVATE_KEY"
    exit 1
fi

# Verificar que estamos en la red correcta (Celo Sepolia)
CHAIN_ID=$(cast chain-id)
if [ "$CHAIN_ID" != "11142220" ]; then
    echo "⚠️  Advertencia: No estás en Celo Sepolia (chain ID: 11142220)"
    echo "   Chain ID actual: $CHAIN_ID"
    read -p "¿Continuar de todas formas? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Ejecutar el script de deployment
echo "📝 Ejecutando script de deployment..."
forge script script/DeployAndSetup.s.sol:DeployAndSetup \
    --rpc-url $CELO_RPC_URL \
    --broadcast \
    --verify \
    -vvv

# Extraer direcciones del broadcast
echo ""
echo "📋 Extrayendo direcciones del deployment..."

BROADCAST_FILE="broadcast/DeployAndSetup.s.sol/$(cast chain-id)/run-latest.json"

if [ ! -f "$BROADCAST_FILE" ]; then
    echo "❌ No se encontró el archivo de broadcast. Verifica que el deployment fue exitoso."
    exit 1
fi

# Extraer direcciones usando jq (si está disponible) o manualmente
if command -v jq &> /dev/null; then
    VAULT=$(jq -r '.transactions[] | select(.contractName=="LootBoxVault") | .contractAddress' "$BROADCAST_FILE")
    REGISTRY=$(jq -r '.transactions[] | select(.contractName=="LootAccessRegistry") | .contractAddress' "$BROADCAST_FILE")
    MINTER=$(jq -r '.transactions[] | select(.contractName=="LootBoxMinter") | .contractAddress' "$BROADCAST_FILE")
else
    echo "⚠️  jq no está instalado. Necesitarás extraer las direcciones manualmente del archivo:"
    echo "   $BROADCAST_FILE"
    echo ""
    echo "Busca 'contractAddress' en cada transacción CREATE"
    exit 0
fi

echo ""
echo "✅ Deployment completado!"
echo ""
echo "📝 Agrega estas direcciones a apps/agents/.env:"
echo ""
echo "LOOTBOX_VAULT_ADDRESS=\"$VAULT\""
echo "REGISTRY_ADDRESS=\"$REGISTRY\""
echo "MINTER_ADDRESS=\"$MINTER\""
echo ""
echo "💡 IMPORTANTE:"
echo "   - El usuario NO necesita firmar transacciones"
echo "   - El backend distribuye recompensas automáticamente"
echo "   - Los roles ya están configurados para el agente"
echo "   - La campaña 'demo-campaign' ya está configurada"
echo ""

