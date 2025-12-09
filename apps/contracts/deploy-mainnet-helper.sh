#!/bin/bash

# 🚀 Script para desplegar LootBox en Celo Mainnet
# Este script configura las variables necesarias y ejecuta el deployment

echo "🚀 Configurando deployment para Celo Mainnet"
echo ""

# Cargar variables desde apps/agents/.env
ENV_FILE="../agents/.env"
if [ -f "$ENV_FILE" ]; then
    echo "📄 Cargando variables desde $ENV_FILE"
    # Usar Python para filtrar y exportar variables de forma robusta (soporta espacios y comillas)
    eval $(python3 -c "import sys, re; [print(f'export {m.group(1)}=\"{m.group(2).strip().strip(chr(39)).strip(chr(34))}\"') for l in open('$ENV_FILE') for m in [re.match(r'^\s*([A-Z0-9_]+)\s*=\s*(.*)', l)] if m]")
else
    echo "⚠️  No se encontró $ENV_FILE, usando variables de entorno actuales"
fi

# AGENT_ADDRESS y DEPLOYER_PRIVATE_KEY deben venir del .env
if [ -z "$AGENT_ADDRESS" ]; then
    echo "❌ ERROR: AGENT_ADDRESS no encontrado en .env"
    exit 1
fi

if [ -z "$DEPLOYER_PRIVATE_KEY" ]; then
    echo "❌ ERROR: DEPLOYER_PRIVATE_KEY no encontrado en .env"
    exit 1
fi

# RPC y cUSD de Celo Mainnet
export CELO_RPC_URL="https://rpc.ankr.com/celo"
export CUSD_ADDRESS="0x765DE816845861e75A25fCA122bb6898B8B1282a"

echo "📋 Configuración:"
echo "   AGENT_ADDRESS: $AGENT_ADDRESS"
echo "   CELO_RPC_URL: $CELO_RPC_URL"
echo "   CUSD_ADDRESS: $CUSD_ADDRESS"
echo ""

# Verificar que DEPLOYER_PRIVATE_KEY está configurada
if [ "$DEPLOYER_PRIVATE_KEY" = "0x..." ]; then
    echo "❌ ERROR: Debes configurar DEPLOYER_PRIVATE_KEY en este script"
    echo "   Edita la línea 11 con tu private key"
    exit 1
fi

echo "✅ Variables configuradas correctamente"
echo ""
echo "🚀 Ejecutando deployment..."
echo ""

# Ejecutar el script de deployment
cd "$(dirname "$0")"
./deploy-mainnet.sh
