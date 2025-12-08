#!/bin/bash
# Script para listar y verificar campañas activas en los contratos

set -e

# Cargar variables de entorno
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Variables requeridas
PRIVATE_KEY="${CELO_PRIVATE_KEY:-$DEPLOYER_PRIVATE_KEY}"

if [ -z "$CELO_RPC_URL" ] || [ -z "$LOOTBOX_VAULT_ADDRESS" ] || [ -z "$REGISTRY_ADDRESS" ] || [ -z "$MINTER_ADDRESS" ]; then
    echo "❌ Error: Faltan variables de entorno requeridas"
    echo "Necesitas: CELO_RPC_URL, LOOTBOX_VAULT_ADDRESS, REGISTRY_ADDRESS, MINTER_ADDRESS"
    exit 1
fi

echo "📋 CAMPAÑAS ACTIVAS EN LOS CONTRATOS"
echo "========================================"
echo ""

# Función para calcular campaign_id
calculate_campaign_id() {
    local name="$1"
    cast keccak "$name"
}

# Función para verificar campaña en Registry
check_registry() {
    local campaign_id="$1"
    cast call "$REGISTRY_ADDRESS" \
        "campaignRules(bytes32)(uint64,bool)" \
        "$campaign_id" \
        --rpc-url "$CELO_RPC_URL" 2>/dev/null || echo "ERROR"
}

# Función para verificar campaña en Vault
check_vault() {
    local campaign_id="$1"
    cast call "$LOOTBOX_VAULT_ADDRESS" \
        "getCampaign(bytes32)(address,uint96,uint256,bool)" \
        "$campaign_id" \
        --rpc-url "$CELO_RPC_URL" 2>/dev/null || echo "ERROR"
}

# Lista de campañas conocidas para verificar
CAMPAIGNS=(
    "demo-campaign"
    # Agrega más campañas aquí si las conoces
    # "cast-0x812abc-loot"
    # "cast-0x123def-loot"
)

echo "🔍 Verificando campañas conocidas..."
echo ""

for campaign_name in "${CAMPAIGNS[@]}"; do
    campaign_id=$(calculate_campaign_id "$campaign_name")
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📦 Campaña: $campaign_name"
    echo "   ID (bytes32): $campaign_id"
    echo ""
    
    # Verificar en Registry
    echo "   📝 LootAccessRegistry:"
    registry_result=$(check_registry "$campaign_id")
    if [ "$registry_result" != "ERROR" ]; then
        echo "      ✅ Configurada: $registry_result"
    else
        echo "      ❌ No configurada o error"
    fi
    
    # Verificar en Vault
    echo "   💰 LootBoxVault:"
    vault_result=$(check_vault "$campaign_id")
    if [ "$vault_result" != "ERROR" ]; then
        # Parsear resultado: (token, rewardPerRecipient, remainingBudget, active)
        echo "      ✅ Inicializada: $vault_result"
    else
        echo "      ❌ No inicializada o error"
    fi
    
    echo ""
done

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "💡 CÓMO GENERAR CAMPAIGN IDs:"
echo ""
echo "1. Para una campaña basada en un cast de Farcaster:"
echo "   CAMPAIGN_ID=\$(cast keccak \"cast-0xHASH-loot\")"
echo ""
echo "2. Para una campaña personalizada:"
echo "   CAMPAIGN_ID=\$(cast keccak \"mi-campana-nombre\")"
echo ""
echo "3. El formato típico es:"
echo "   - demo-campaign (fallback)"
echo "   - cast-{hash}-loot (dinámica desde Farcaster)"
echo "   - {frame_id}-loot (desde frame específico)"
echo ""
echo "📊 Para ver campañas dinámicas creadas por el agente:"
echo "   - Revisa los logs del backend cuando se ejecuta un scan"
echo "   - Busca mensajes como: 'Configurando campaña real automáticamente: cast-...'"
echo "   - O revisa el leaderboard en: /api/lootbox/leaderboard"

