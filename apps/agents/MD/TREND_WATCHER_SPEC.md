# 📊 TrendWatcherAgent - Especificación Completa

## 🎯 Responsabilidades del TrendWatcherAgent

El `TrendWatcherAgent` es el **primer agente** en el pipeline y tiene las siguientes responsabilidades:

### 1. **Escanear Tendencias Activas en Farcaster** ✅

**Qué hace:**
- Consulta la API de Neynar para obtener casts recientes
- Busca en canales específicos o globalmente
- Obtiene hasta `MAX_RECENT_CASTS` (por defecto: 8) casts recientes

**Cómo funciona:**
```python
casts = await self.farcaster.fetch_recent_casts(
    channel_id=channel_id,  # "global" por defecto
    limit=self.settings.max_recent_casts  # 8 por defecto
)
```

**Endpoint usado:**
- `/v2/farcaster/feed/user/casts` con usuarios populares conocidos
- Actualmente usa FID `2` (puede expandirse)

### 2. **Calcular Trend Score para Cada Cast** ✅

**Qué hace:**
- Calcula un score (0.0 - 1.0) para cada cast basado en:
  - **Engagement**: `(likes * 1.0 + recasts * 2.0 + replies * 0.6) / 200.0`
  - **Recencia**: Bonus por ser reciente (máximo 12 horas)
  - **Fórmula**: `engagement_score + (recency_bonus * 0.3)`

**Código:**
```python
def _score_cast(self, cast: dict[str, Any]) -> float:
    reactions = cast.get("reactions", {})
    likes = reactions.get("likes", 0)
    recasts = reactions.get("recasts", 0)
    replies = reactions.get("replies", 0)
    
    engagement_score = (likes * 1.0 + recasts * 2.0 + replies * 0.6) / 200.0
    recency_hours = self.farcaster.timestamp_age_hours(cast.get("timestamp"))
    recency_bonus = max(0.0, 12 - recency_hours) / 12.0
    combined = engagement_score + recency_bonus * 0.3
    return min(combined, 1.0)
```

### 3. **Seleccionar el Cast Más Viral** ✅

**Qué hace:**
- Ordena todos los casts por `trend_score` (descendente)
- Selecciona el cast con el score más alto
- Verifica que el score sea >= `MIN_TREND_SCORE` (por defecto: 0.35)

**Si el score es muy bajo:**
- Retorna `status: "trend_below_threshold"`
- No continúa con el pipeline

### 4. **Generar Análisis con IA (Gemini)** ✅

**Qué hace:**
- Intenta usar Gemini para generar un análisis contextual del cast
- Si Gemini no está disponible o la cuota está agotada, usa análisis básico

**Análisis con IA:**
```python
prompt = "Eres un estratega de growth para comunidades Web3. 
         Resume en 1 frase por qué este cast es relevante para 
         la comunidad de Celo/MiniPay y qué acción recomienda tomar."
```

**Análisis básico (fallback):**
- Detecta keywords: `["celo", "minipay", "web3", "defi", "crypto", "blockchain", "nft", "rewards"]`
- Genera mensaje basado en engagement y keywords encontradas

### 5. **Extraer Topic Tags** ✅

**Qué hace:**
- Extrae hashtags del texto del cast usando regex
- Limita a 4 tags máximo
- Normaliza a lowercase

**Código:**
```python
@staticmethod
def _extract_tags(text: str) -> list[str]:
    tags = set(tag.lower() for tag in re.findall(r"#(\w+)", text))
    return sorted(tags)[:4]
```

### 6. **Generar Frame Identifier** ✅

**Qué hace:**
- Crea un identificador único basado en el hash del cast
- Formato: `cast-{primeros_8_chars_del_hash}`
- Ejemplo: Si hash es `0x812abc123def456...`, el frame_id será `cast-0x812abc`

### 7. **Retornar Contexto Completo** ✅

**Output esperado:**
```python
{
    "frame_id": "cast-0x812abc",
    "cast_hash": "0x812abc123def456...",
    "trend_score": 0.85,
    "status": "trend_detected",
    "source_text": "¡MiniPay está cambiando el juego! 🚀",
    "ai_analysis": "Post relevante sobre adopción de MiniPay...",
    "topic_tags": ["minipay", "celo", "web3"],
    "channel_id": "global",
    "target_address": None,  # Si se proporciona
    "reward_type": "nft"  # Por defecto o el especificado
}
```

## 🔍 Verificación de Funcionamiento

### Test Manual

```bash
# Desde el directorio del proyecto
cd apps/agents

# Activar entorno virtual
source .venv/bin/activate

# Ejecutar test del agente
python -c "
import asyncio
from src.config import Settings
from src.graph.trend_watcher import TrendWatcherAgent

async def test():
    settings = Settings()
    agent = TrendWatcherAgent(settings)
    result = await agent.handle({
        'channel_id': 'global',
        'trend_score': 0.0
    })
    print('Status:', result.get('status'))
    print('Trend Score:', result.get('trend_score'))
    print('Source Text:', result.get('source_text', 'N/A')[:50])
    print('AI Analysis:', result.get('ai_analysis', 'N/A')[:50])
    print('Topic Tags:', result.get('topic_tags', []))

asyncio.run(test())
"
```

### Verificar Logs del Backend

Cuando el backend está corriendo, busca en los logs:

```
INFO: Analizando conversaciones recientes en Farcaster (canal=global)...
INFO: Trend detectado: 'cast-0x812abc' con score 0.85
```

### Verificar API Endpoint

```bash
# Llamar al endpoint de scan
curl -X POST http://localhost:8001/api/lootbox/scan

# O llamar directamente al endpoint de run
curl -X POST http://localhost:8001/api/lootbox/run \
  -H "Content-Type: application/json" \
  -d '{
    "frame_id": "",
    "channel_id": "global",
    "trend_score": 0.0
  }'
```

## ⚠️ Problemas Comunes y Soluciones

### 1. **No encuentra tendencias (`status: "no_trends_found"`)**

**Causas:**
- Neynar API key inválida o sin créditos
- No hay casts recientes en los usuarios monitoreados
- Error de conexión con Neynar API

**Solución:**
- Verificar `NEYNAR_API_KEY` en `.env`
- Verificar que la API key tenga créditos disponibles
- Revisar logs para errores específicos

### 2. **Trend score muy bajo (`status: "trend_below_threshold"`)**

**Causa:**
- Los casts encontrados no tienen suficiente engagement
- Son muy antiguos (más de 12 horas)

**Solución:**
- Ajustar `MIN_TREND_SCORE` en `.env` (por defecto: 0.35)
- O esperar a que haya casts más virales

### 3. **Análisis de IA no funciona**

**Causa:**
- `GOOGLE_API_KEY` no configurada o inválida
- Cuota de Gemini agotada
- Modelo no disponible

**Solución:**
- El sistema automáticamente usa análisis básico como fallback
- Verificar `GOOGLE_API_KEY` en `.env`
- El sistema funcionará sin IA, solo con análisis básico

### 4. **Error 402 (Payment Required) de Neynar**

**Causa:**
- API key sin créditos o inválida

**Solución:**
- Obtener nueva API key en https://neynar.com
- Verificar que tenga créditos disponibles
- Actualizar `NEYNAR_API_KEY` en `.env`

## 📋 Checklist de Funcionamiento

- [ ] `NEYNAR_API_KEY` configurada y válida
- [ ] `GOOGLE_API_KEY` configurada (opcional, para IA)
- [ ] Backend corriendo en `http://localhost:8001`
- [ ] Endpoint `/api/lootbox/scan` responde correctamente
- [ ] Logs muestran "Analizando conversaciones recientes en Farcaster"
- [ ] Retorna `status: "trend_detected"` cuando hay tendencias
- [ ] Incluye `trend_score`, `source_text`, `ai_analysis`, `topic_tags`

## 🚀 Próximos Pasos

Una vez que el `TrendWatcherAgent` funciona correctamente, el contexto se pasa automáticamente al `EligibilityAgent` que:
1. Identifica usuarios que participaron en el cast
2. Calcula scores individuales
3. Filtra por elegibilidad on-chain


