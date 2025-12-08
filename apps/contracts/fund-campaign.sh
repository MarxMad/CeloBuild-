#!/bin/bash
# Script para depositar fondos cUSD en una campaña del LootBoxVault

set -e

# Cargar variables de entorno
# Buscar en múltiples ubicaciones
load_env() {
    local env_file="$1"
    if [ -f "$env_file" ]; then
        # Cargar solo líneas válidas (KEY=VALUE, sin comentarios, sin espacios especiales)
        while IFS= read -r line || [ -n "$line" ]; do
            # Ignorar comentarios y líneas vacías
            if [[ "$line" =~ ^[[:space:]]*# ]] || [[ -z "${line// }" ]]; then
                continue
            fi
            # Solo exportar líneas que tengan formato KEY=VALUE válido
            if [[ "$line" =~ ^[[:space:]]*[A-Za-z_][A-Za-z0-9_]*= ]]; then
                # Quitar espacios y comillas alrededor del valor
                key=$(echo "$line" | cut -d'=' -f1 | tr -d '[:space:]')
                value=$(echo "$line" | cut -d'=' -f2- | sed 's/^[[:space:]]*["'\'']*//; s/["'\'']*[[:space:]]*$//')
                export "$key=$value"
            fi
        done < "$env_file"
    fi
}

if [ -f .env ]; then
    load_env .env
elif [ -f ../agents/.env ]; then
    load_env ../agents/.env
fi

# Variables requeridas
# Usar CELO_PRIVATE_KEY (del agente) o DEPLOYER_PRIVATE_KEY como fallback
PRIVATE_KEY="${CELO_PRIVATE_KEY:-$DEPLOYER_PRIVATE_KEY}"

if [ -z "$PRIVATE_KEY" ] || [ -z "$CELO_RPC_URL" ] || [ -z "$LOOTBOX_VAULT_ADDRESS" ] || [ -z "$CUSD_ADDRESS" ]; then
    echo "❌ Error: Faltan variables de entorno requeridas"
    echo "Necesitas: CELO_PRIVATE_KEY (o DEPLOYER_PRIVATE_KEY), CELO_RPC_URL, LOOTBOX_VAULT_ADDRESS, CUSD_ADDRESS"
    exit 1
fi

# Configuración
CAMPAIGN_NAME="${CAMPAIGN_ID:-demo-campaign}"
AMOUNT_CUSD="${FUND_AMOUNT_CUSD:-100}"  # Por defecto 100 cUSD
AMOUNT_WEI=$(cast --to-wei "$AMOUNT_CUSD" ether)

echo "💰 Depositando fondos en LootBoxVault"
echo "========================================"
echo "Vault: $LOOTBOX_VAULT_ADDRESS"
echo "cUSD Token: $CUSD_ADDRESS"
echo "Campaña: $CAMPAIGN_NAME"
echo "Cantidad: $AMOUNT_CUSD cUSD"
echo ""

# Paso 1: Aprobar el vault
echo "📝 Paso 1: Aprobando vault para transferir cUSD..."
cast send "$CUSD_ADDRESS" \
    "approve(address,uint256)" \
    "$LOOTBOX_VAULT_ADDRESS" \
    "$AMOUNT_WEI" \
    --private-key "$PRIVATE_KEY" \
    --rpc-url "$CELO_RPC_URL" \
    --chain celo-sepolia

echo "✅ Aprobación completada"
echo ""

# Paso 2: Calcular campaign_id
CAMPAIGN_ID=$(cast keccak "$CAMPAIGN_NAME")
echo "📋 Campaign ID: $CAMPAIGN_ID"
echo ""

# Paso 3: Depositar fondos
echo "💰 Paso 2: Depositando fondos en la campaña..."
cast send "$LOOTBOX_VAULT_ADDRESS" \
    "fundCampaign(bytes32,uint256)" \
    "$CAMPAIGN_ID" \
    "$AMOUNT_WEI" \
    --private-key "$PRIVATE_KEY" \
    --rpc-url "$CELO_RPC_URL" \
    --chain celo-sepolia

echo ""
echo "✅ ¡Fondos depositados exitosamente!"
echo ""
echo "La campaña '$CAMPAIGN_NAME' ahora tiene $AMOUNT_CUSD cUSD disponibles"
echo "para distribuir recompensas."

