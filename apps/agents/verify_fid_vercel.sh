#!/bin/bash
# Script para verificar el FID desde el backend en Vercel

# Reemplaza con tu URL de Vercel
BACKEND_URL="${BACKEND_URL:-https://tu-backend.vercel.app}"

echo "🔍 Verificando FID desde el backend en Vercel..."
echo "📍 URL: $BACKEND_URL"
echo ""

# Llamar al endpoint que obtiene el FID desde el mnemonic
curl -X GET "$BACKEND_URL/api/casts/app-fid" \
  -H "accept: application/json" \
  | jq '.'

echo ""
echo "💡 Compara el 'custody_address' retornado con:"
echo "   0xb539ca2b444a07b1295fe5e2cf60b509ba5b1a54"
echo ""
echo "✅ Si coinciden, entonces FID 744296 es correcto"

