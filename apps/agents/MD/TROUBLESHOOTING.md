# 🔧 Troubleshooting - Problemas Comunes

## ⚠️ Errores Detectados y Soluciones

### 1. Google API Key Comprometida

**Error:**
```
403 Your API key was reported as leaked. Please use another API key.
```

**Solución:**
1. Ve a [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Crea una nueva API key
3. Actualiza `GOOGLE_API_KEY` en tu `.env` y en Vercel
4. El sistema funcionará sin IA mientras tanto (usa análisis básico)

### 2. Replacement Transaction Underpriced

**Error:**
```
replacement transaction underpriced
```

**Causa:** Hay una transacción pendiente con el mismo nonce y un gas price más bajo.

**Solución Implementada:**
- El sistema ahora detecta transacciones pendientes
- Aumenta automáticamente el gas price en 20-50%
- Reintenta la transacción con gas price más alto

**Si persiste:**
```bash
# Esperar a que se confirme la transacción pendiente
# O cancelar la transacción pendiente enviando una con nonce más alto y gas price 0
```

### 3. Error de DNS/Red

**Error:**
```
Failed to resolve 'rpc.ankr.com'
NameResolutionError
```

**Causa:** Problema temporal de red o DNS.

**Solución:**
- El sistema ya tiene manejo de errores para esto
- Si persiste, cambia `CELO_RPC_URL` a otro proveedor:
  ```bash
  # Alternativas:
  CELO_RPC_URL=https://celo-sepolia.infura.io/v3/YOUR_KEY
  CELO_RPC_URL=https://forno.celo.org
  ```

### 4. Fallback a demo-campaign

**Comportamiento:**
El sistema usa `demo-campaign` cuando no puede configurar una campaña real.

**Causas posibles:**
- Transacciones pendientes (ahora manejado)
- Error de red (temporal)
- El agente no es owner (verificar)

**Verificación:**
```bash
# Verificar ownership
cast call $LOOTBOX_VAULT_ADDRESS "owner()(address)" --rpc-url $CELO_RPC_URL
# Debe retornar la dirección del agente
```

## 🔍 Verificación de Estado

### Verificar Transacciones Pendientes

```bash
# Ver nonce actual vs pending
cast nonce $AGENT_ADDRESS --rpc-url $CELO_RPC_URL
cast nonce $AGENT_ADDRESS --rpc-url $CELO_RPC_URL --pending
```

### Verificar Balance

```bash
cast balance $AGENT_ADDRESS --rpc-url $CELO_RPC_URL
# Debe tener al menos 0.1 CELO para gas
```

### Verificar Conexión RPC

```bash
cast block-number --rpc-url $CELO_RPC_URL
# Debe retornar un número de bloque
```

## 📝 Mejoras Implementadas

1. ✅ **Manejo de Gas Price**: Detecta transacciones pendientes y aumenta gas price automáticamente
2. ✅ **Reintentos**: Reintenta con gas price más alto si falla
3. ✅ **Manejo de Errores**: No falla completamente si una parte de la configuración falla
4. ✅ **Logging Mejorado**: Más información sobre qué está pasando

## 🚀 Próximos Pasos

1. **Reemplazar Google API Key** (si quieres usar IA)
2. **Verificar que no haya transacciones pendientes** bloqueando nuevas
3. **Probar de nuevo** - el sistema debería funcionar mejor ahora

---

**Los cambios ya están aplicados. Reinicia el servidor para aplicar las mejoras.**

