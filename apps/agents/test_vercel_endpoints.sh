#!/bin/bash
# Script para probar los endpoints de generación de casts en Vercel

# ⚠️ IMPORTANTE: Reemplaza esta URL con la URL real de tu backend en Vercel
BACKEND_URL="${BACKEND_URL:-https://celo-build-backend-agents.vercel.app}"

echo "🧪 Probando endpoints de generación de casts en Vercel"
echo "📍 Backend URL: $BACKEND_URL"
echo ""

# Colores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para hacer requests
test_endpoint() {
    local method=$1
    local endpoint=$2
    local data=$3
    local description=$4
    
    echo -e "${YELLOW}📡 Probando: $description${NC}"
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$BACKEND_URL$endpoint")
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" \
            -H "Content-Type: application/json" \
            -d "$data" \
            "$BACKEND_URL$endpoint")
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" -ge 200 ] && [ "$http_code" -lt 300 ]; then
        echo -e "${GREEN}✅ Status: $http_code${NC}"
        echo "Response:"
        echo "$body" | jq '.' 2>/dev/null || echo "$body"
    else
        echo -e "${RED}❌ Status: $http_code${NC}"
        echo "Response:"
        echo "$body"
    fi
    echo ""
}

# 1. Health check
echo "=" | head -c 60
echo ""
test_endpoint "GET" "/healthz" "" "Health Check"

# 2. Obtener temas disponibles
test_endpoint "GET" "/api/casts/topics" "" "Obtener Temas Disponibles"

# 3. Obtener dirección del agente
test_endpoint "GET" "/api/casts/agent-address" "" "Obtener Dirección del Agente"

# 4. Generar cast (preview)
test_endpoint "POST" "/api/casts/generate" '{"topic":"tech"}' "Generar Cast (Tech)"

# 5. Generar cast con otro tema
test_endpoint "POST" "/api/casts/generate" '{"topic":"motivacion"}' "Generar Cast (Motivación)"

echo -e "${GREEN}✅ Pruebas completadas${NC}"
echo ""
echo "📝 Nota: Para probar /api/casts/publish necesitas:"
echo "   1. Obtener la dirección del agente"
echo "   2. Transferir 0.5 cUSD a esa dirección"
echo "   3. Usar el hash de la transacción en el endpoint"

