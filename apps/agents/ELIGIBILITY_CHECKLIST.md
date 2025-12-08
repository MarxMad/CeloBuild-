# ✅ EligibilityAgent - Checklist de Funcionamiento

## 📋 Resumen de Responsabilidades

El **EligibilityAgent** es el segundo agente y debe:

### 1. ✅ **Obtener Participantes del Cast**
- **Acción**: Consulta Neynar API para obtener usuarios que interactuaron
- **Endpoint**: `/v2/farcaster/cast` con `identifier=cast_hash`
- **Límite**: 100 participantes máximo
- **Pesos**: Autor (2.0), Recast (1.5), Like (1.0)

### 2. ✅ **Analizar Participación Detallada**
- Verifica participación directa (like/recast/reply)
- Busca casts relacionados del usuario sobre el tema
- Calcula engagement total y breakdown

### 3. ✅ **Calcular User Score**
- **Fórmula con ponderaciones**:
  - Trend Score: 40% (weight_trend_score)
  - Follower Count: 20% (weight_follower_count)
  - Power Badge: 15% (weight_power_badge)
  - Engagement: 25% (weight_engagement)
- **Rango**: 0-100 puntos

### 4. ✅ **Validar Elegibilidad On-Chain**
- Consulta `LootAccessRegistry.canClaim()`
- Verifica cooldown del usuario
- Filtra usuarios que ya reclamaron

### 5. ✅ **Seleccionar Top N Usuarios**
- Ordena por score descendente
- Filtra solo elegibles (on-chain check)
- Selecciona hasta `MAX_REWARD_RECIPIENTS` (5 por defecto)

### 6. ✅ **Soporte para Target Manual**
- Permite dirección manual si `ALLOW_MANUAL_TARGET=true`
- Útil para demos y testing

### 7. ✅ **Retornar Contexto Completo**
- Incluye: `recipients`, `rankings`, `metadata`
- Cada ranking tiene: `fid`, `username`, `address`, `score`, `reasons`, `participation`

## 🔍 Verificación Rápida

### Opción 1: Ver Logs del Backend

Cuando el backend está corriendo, busca:

```
INFO: Elegibilidad: 25 candidatos -> 5 seleccionados (score trend=0.85)
```

### Opción 2: Llamar al Endpoint

```bash
curl -X POST http://localhost:8001/api/lootbox/run \
  -H "Content-Type: application/json" \
  -d '{
    "frame_id": "",
    "channel_id": "global",
    "trend_score": 0.0
  }'
```

### Opción 3: Revisar Respuesta

La respuesta debe incluir:
```json
{
  "recipients": ["0x1234...", "0x5678..."],
  "rankings": [
    {
      "username": "alice",
      "address": "0x1234...",
      "score": 85.5,
      "follower_count": 500,
      "power_badge": true
    }
  ]
}
```

## ⚠️ Problemas Comunes

### ❌ `recipients: []` (sin usuarios elegibles)
- **Causa**: No hay participantes o todos están en cooldown
- **Solución**: Verificar que el cast tenga engagement y que la campaña esté configurada

### ❌ Scores muy bajos
- **Causa**: Usuarios con pocos followers o bajo engagement
- **Solución**: Ajustar ponderaciones en `.env` o normal, el sistema prioriza reputación

### ❌ Error consultando LootAccessRegistry
- **Causa**: Contrato no configurado o error de conexión
- **Solución**: El sistema usa `demo-campaign` como fallback automáticamente

## 📊 Estado Actual del Código

✅ **Implementado correctamente:**
- Obtención de participantes del cast
- Análisis de participación detallada
- Cálculo de score con ponderaciones
- Validación on-chain de elegibilidad
- Selección de top N usuarios
- Soporte para target manual
- Retorno de contexto completo

✅ **Manejo de errores:**
- Fallback a `demo-campaign` si la campaña no está configurada
- Manejo de errores de conexión con contratos
- Validación de direcciones Ethereum
- Filtrado de usuarios sin `custody_address`

## 🚀 Próximo Paso

Una vez que `EligibilityAgent` funciona, el contexto se pasa automáticamente a `RewardDistributorAgent`.

