# ✅ TrendWatcherAgent - Checklist de Funcionamiento

## 📋 Resumen de Responsabilidades

El **TrendWatcherAgent** es el primer agente y debe:

### 1. ✅ **Escanear Tendencias Activas en Farcaster**
- **Acción**: Consulta Neynar API para obtener casts recientes
- **Endpoint**: `/v2/farcaster/feed/user/casts` con FID `2` (dwr.eth)
- **Límite**: `MAX_RECENT_CASTS` (8 por defecto)
- **Canal**: `"global"` por defecto o el especificado

### 2. ✅ **Calcular Trend Score para Cada Cast**
- **Fórmula**: 
  - Engagement: `(likes * 1.0 + recasts * 2.0 + replies * 0.6) / 200.0`
  - Recencia: Bonus si tiene menos de 12 horas
  - Score final: `engagement_score + (recency_bonus * 0.3)`
- **Rango**: 0.0 - 1.0

### 3. ✅ **Seleccionar el Cast Más Viral**
- Ordena todos los casts por `trend_score` (descendente)
- Selecciona el top cast
- Verifica que `trend_score >= MIN_TREND_SCORE` (0.35 por defecto)

### 4. ✅ **Generar Análisis con IA (Gemini)**
- **Intenta usar Gemini** para análisis contextual
- **Si falla**: Usa análisis básico basado en keywords
- **Keywords detectadas**: `["celo", "minipay", "web3", "defi", "crypto", "blockchain", "nft", "rewards"]`

### 5. ✅ **Extraer Topic Tags**
- Extrae hashtags del texto usando regex `#(\w+)`
- Limita a 4 tags máximo
- Normaliza a lowercase

### 6. ✅ **Generar Frame Identifier**
- Crea `frame_id` basado en el hash del cast
- Formato: `cast-{primeros_8_chars_del_hash}`
- Ejemplo: `cast-0x812abc`

### 7. ✅ **Retornar Contexto Completo**
- Incluye: `frame_id`, `cast_hash`, `trend_score`, `source_text`, `ai_analysis`, `topic_tags`, `channel_id`

## 🔍 Verificación Rápida

### Opción 1: Ver Logs del Backend

Cuando el backend está corriendo, busca:

```
INFO: Analizando conversaciones recientes en Farcaster (canal=global)...
INFO: Trend detectado: 'cast-0x812abc' con score 0.85
```

### Opción 2: Llamar al Endpoint

```bash
curl -X POST http://localhost:8001/api/lootbox/scan
```

O:

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
  "status": "trend_detected",
  "trend_score": 0.85,
  "frame_id": "cast-0x812abc",
  "cast_hash": "0x...",
  "source_text": "...",
  "ai_analysis": "...",
  "topic_tags": ["minipay", "celo"]
}
```

## ⚠️ Problemas Comunes

### ❌ `status: "no_trends_found"`
- **Causa**: No hay casts recientes o error de API
- **Solución**: Verificar `NEYNAR_API_KEY` y que tenga créditos

### ❌ `status: "trend_below_threshold"`
- **Causa**: Score muy bajo (< 0.35)
- **Solución**: Normal, esperar casts más virales o bajar `MIN_TREND_SCORE`

### ❌ Error 402 (Payment Required)
- **Causa**: API key sin créditos
- **Solución**: Obtener nueva API key en https://neynar.com

## 📊 Estado Actual del Código

✅ **Implementado correctamente:**
- Escaneo de casts recientes
- Cálculo de trend_score
- Selección del cast más viral
- Análisis con IA (con fallback)
- Extracción de topic tags
- Generación de frame_id
- Retorno de contexto completo

✅ **Manejo de errores:**
- Rate limiting (429)
- Payment required (402)
- Fallback a análisis básico si IA falla
- Validación de umbral mínimo

## 🚀 Próximo Paso

Una vez que `TrendWatcherAgent` funciona, el contexto se pasa automáticamente a `EligibilityAgent`.


