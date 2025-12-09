#!/bin/bash

# Script para actualizar el backend con las direcciones de mainnet

ENV_FILE="../agents/.env"

echo "🔄 Actualizando $ENV_FILE con direcciones de Celo Mainnet..."

# Backup del .env actual
cp "$ENV_FILE" "$ENV_FILE.backup-$(date +%Y%m%d)"

# Actualizar las variables
sed -i '' 's|CELO_RPC_URL=.*|CELO_RPC_URL="https://rpc.ankr.com/celo"|' "$ENV_FILE"
sed -i '' 's|LOOTBOX_VAULT_ADDRESS=.*|LOOTBOX_VAULT_ADDRESS="0x2c8c787af0d123a7bedf20064f3ad45aaafd6020"|' "$ENV_FILE"
sed -i '' 's|REGISTRY_ADDRESS=.*|REGISTRY_ADDRESS="0x4a948a06422116fcd8dcd9eacac32e5c40b0e400"|' "$ENV_FILE"
sed -i '' 's|MINTER_ADDRESS=.*|MINTER_ADDRESS="0x455fa0b0de62fead3032f8485cddd9e606cc7c7d"|' "$ENV_FILE"
sed -i '' 's|CUSD_ADDRESS=.*|CUSD_ADDRESS="0x765DE816845861e75A25fCA122bb6898B8B1282a"|' "$ENV_FILE"

echo "✅ Archivo $ENV_FILE actualizado!"
echo ""
echo "📋 Nuevas direcciones (Celo Mainnet):"
echo "   CELO_RPC_URL: https://rpc.ankr.com/celo"
echo "   LOOTBOX_VAULT_ADDRESS: 0x2c8c787af0d123a7bedf20064f3ad45aaafd6020"
echo "   REGISTRY_ADDRESS: 0x4a948a06422116fcd8dcd9eacac32e5c40b0e400"
echo "   MINTER_ADDRESS: 0x455fa0b0de62fead3032f8485cddd9e606cc7c7d"
echo "   CUSD_ADDRESS: 0x765DE816845861e75A25fCA122bb6898B8B1282a"
echo ""
echo "⚠️  IMPORTANTE: Actualiza estas variables también en Vercel:"
echo "   1. Ve a tu proyecto backend en Vercel Dashboard"
echo "   2. Settings → Environment Variables"
echo "   3. Actualiza cada variable con los valores de mainnet"
echo "   4. Redeploy el backend"
