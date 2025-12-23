# 🎯 EligibilityAgent - Especificación Completa

## 🎯 Responsabilidades del EligibilityAgent

El `EligibilityAgent` es el **segundo agente** en el pipeline y tiene las siguientes responsabilidades:

### 1. **Obtener Participantes del Cast** ✅

**Qué hace:**
- Consulta la API de Neynar para obtener usuarios que interactuaron con el cast detectado
- Identifica: autor, likes, recasts, replies
- Limita a 100 participantes máximo

**Cómo funciona:**
```python
participants = await self.farcaster.fetch_cast_engagement(
    cast_hash=cast_hash,
    limit=100
)
```

**Endpoint usado:**
- `/v2/farcaster/cast` con `identifier=cast_hash` y `type=hash`
- Extrae participantes de las reacciones del cast

**Pesos de engagement:**
- **Autor**: 2.0 puntos
- **Recast**: 1.5 puntos
- **Like**: 1.0 punto

### 2. **Analizar Participación Detallada de Cada Usuario** ✅

**Qué hace:**
- Para cada participante, analiza su participación en la tendencia
- Verifica si participó directamente (like/recast/reply)
- Busca casts relacionados del usuario sobre el tema
- Calcula engagement total

**Código:**
```python
participation_data = await self.farcaster.analyze_user_participation_in_trend(
    user_fid=user_fid,
    cast_hash=cast_hash,
    topic_tags=topic_tags,
)
```

**Datos retornados:**
```python
{
    "directly_participated": True/False,
    "related_casts": [...],
    "total_engagement": 15.5,
    "engagement_breakdown": {
        "likes_received": 10,
        "recasts_received": 5,
        "replies_received": 2,
    }
}
```

### 3. **Calcular User Score Avanzado** ✅

**Qué hace:**
- Calcula un score (0-100) para cada usuario usando ponderaciones configurables
- Combina múltiples factores:
  - **Trend Score** (40% por defecto): Score de la tendencia detectada
  - **Follower Count** (20% por defecto): Reputación social del usuario
  - **Power Badge** (15% por defecto): Bonus por tener power badge
  - **Engagement** (25% por defecto): Participación en la tendencia

**Fórmula:**
```python
# 1. Trend Component (40%)
trend_component = trend_score * 100 * weight_trend_score  # 0.40

# 2. Follower Component (20%)
follower_score_raw = min(follower_count / 50, 20)  # 1000 followers = 20 puntos
follower_component = follower_score_raw * weight_follower_count * 5  # 0.20

# 3. Power Badge Component (15%)
badge_component = 15.0 * weight_power_badge if power_badge else 0.0  # 0.15

# 4. Engagement Component (25%)
engagement_normalized = min(total_engagement / 10, 25)  # 10 engagement = 25 puntos
engagement_component = engagement_normalized * weight_engagement  # 0.25

# Total
total_score = trend_component + follower_component + badge_component + engagement_component
```

**Ponderaciones por defecto (configurables en Settings):**
- `weight_trend_score = 0.40` (40%)
- `weight_follower_count = 0.20` (20%)
- `weight_power_badge = 0.15` (15%)
- `weight_engagement = 0.25` (25%)

### 4. **Validar Elegibilidad On-Chain** ✅

**Qué hace:**
- Verifica si el usuario puede reclamar usando `LootAccessRegistry`
- Consulta el contrato para verificar cooldown
- Filtra usuarios que ya reclamaron recientemente

**Código:**
```python
can_claim = self.celo_tool.can_claim(
    registry_address=self.settings.registry_address,
    campaign_id=campaign_id,
    participant=candidate["address"],
)
```

**Campaign ID:**
- Formato: `{frame_id}-loot`
- Ejemplo: `cast-0x812abc-loot`
- Fallback: `demo-campaign` si la campaña no está configurada

**Manejo de errores:**
- Si la campaña no está configurada (error `0x050aad92`), intenta con `demo-campaign`
- Si hay error de conexión, asume que puede reclamar (no bloquea el flujo)

### 5. **Seleccionar Top N Usuarios Elegibles** ✅

**Qué hace:**
- Ordena usuarios por score descendente
- Filtra solo los que pueden reclamar (on-chain check)
- Selecciona hasta `MAX_REWARD_RECIPIENTS` (5 por defecto)

**Proceso:**
1. Ordenar rankings por score (descendente)
2. Para cada candidato:
   - Verificar elegibilidad on-chain
   - Si puede reclamar, agregar a shortlist
   - Si no, saltar al siguiente
3. Detener cuando se alcanza el límite

### 6. **Soporte para Target Manual (Opcional)** ✅

**Qué hace:**
- Permite agregar una dirección manual si está habilitado
- Útil para demos y testing
- Solo se usa si no hay rankings o si está explícitamente permitido

**Configuración:**
- `ALLOW_MANUAL_TARGET=true` en `.env`
- `target_address` en el payload

### 7. **Retornar Contexto Completo** ✅

**Output esperado:**
```python
{
    "campaign_id": "cast-0x812abc-loot",
    "recipients": [
        "0x1234...",
        "0x5678...",
        ...
    ],
    "rankings": [
        {
            "fid": 1234,
            "username": "alice",
            "address": "0x1234...",
            "score": 85.5,
            "reasons": ["like", "recast"],
            "follower_count": 500,
            "power_badge": True,
            "participation": {
                "directly_participated": True,
                "total_engagement": 15.5,
                ...
            }
        },
        ...
    ],
    "metadata": {
        "channel_id": "global",
        "trend_score": 0.85,
        "ai_analysis": "...",
        "topic_tags": ["minipay", "celo"],
        "cast_hash": "0x...",
        "reward_type": "nft"
    }
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
from src.graph.eligibility import EligibilityAgent

async def test():
    settings = Settings()
    agent = EligibilityAgent(settings)
    context = {
        'frame_id': 'cast-0x812abc',
        'cast_hash': '0x812abc123...',
        'trend_score': 0.85,
        'topic_tags': ['minipay', 'celo'],
        'channel_id': 'global',
    }
    result = await agent.handle(context)
    print('Recipients:', len(result.get('recipients', [])))
    print('Rankings:', len(result.get('rankings', [])))
    for ranking in result.get('rankings', [])[:3]:
        print(f\"  - {ranking.get('username')}: {ranking.get('score')} pts\")

asyncio.run(test())
"
```

### Verificar Logs del Backend

Cuando el backend está corriendo, busca en los logs:

```
INFO: Elegibilidad: 25 candidatos -> 5 seleccionados (score trend=0.85)
```

### Verificar API Endpoint

```bash
# Llamar al endpoint de run (ejecuta todo el pipeline)
curl -X POST http://localhost:8001/api/lootbox/run \
  -H "Content-Type: application/json" \
  -d '{
    "frame_id": "",
    "channel_id": "global",
    "trend_score": 0.0
  }'
```

## ⚠️ Problemas Comunes y Soluciones

### 1. **No encuentra participantes (`recipients: []`)**

**Causas:**
- El cast no tiene engagement (sin likes/recasts/replies)
- Los participantes no tienen `custody_address` válida
- Error de conexión con Neynar API

**Solución:**
- Verificar que el cast tenga engagement
- Verificar `NEYNAR_API_KEY` en `.env`
- Revisar logs para errores específicos

### 2. **Usuarios no pueden reclamar (todos filtrados)**

**Causa:**
- Todos los usuarios están en cooldown
- La campaña no está configurada en `LootAccessRegistry`
- Error de conexión con el contrato

**Solución:**
- Verificar que la campaña esté configurada en el contrato
- Verificar `REGISTRY_ADDRESS` en `.env`
- Revisar logs para errores de contrato
- El sistema intenta usar `demo-campaign` como fallback

### 3. **Scores muy bajos**

**Causa:**
- Usuarios con pocos followers
- Bajo engagement en la tendencia
- Sin power badge

**Solución:**
- Ajustar ponderaciones en `.env`:
  - `WEIGHT_TREND_SCORE`
  - `WEIGHT_FOLLOWER_COUNT`
  - `WEIGHT_POWER_BADGE`
  - `WEIGHT_ENGAGEMENT`
- Normal, el sistema prioriza usuarios con más reputación

### 4. **Error 402 (Payment Required) de Neynar**

**Causa:**
- API key sin créditos o inválida

**Solución:**
- Obtener nueva API key en https://neynar.com
- Verificar que tenga créditos disponibles
- Actualizar `NEYNAR_API_KEY` en `.env`

## 📋 Checklist de Funcionamiento

- [ ] `NEYNAR_API_KEY` configurada y válida
- [ ] `REGISTRY_ADDRESS` configurada (contrato LootAccessRegistry)
- [ ] `CELO_RPC_URL` configurada y accesible
- [ ] Backend corriendo en `http://localhost:8001`
- [ ] Endpoint `/api/lootbox/run` responde correctamente
- [ ] Logs muestran "Elegibilidad: X candidatos -> Y seleccionados"
- [ ] Retorna `recipients` con direcciones válidas
- [ ] Incluye `rankings` con scores y metadata

## 🚀 Próximos Pasos

Una vez que el `EligibilityAgent` funciona correctamente, el contexto se pasa automáticamente al `RewardDistributorAgent` que:
1. Determina el tipo de recompensa según el score
2. Distribuye NFTs, cUSD o XP según corresponda
3. Registra todo on-chain

## 📊 Fórmula de Score Detallada

### Ejemplo de Cálculo

**Usuario:**
- Trend Score: 0.85
- Followers: 500
- Power Badge: Sí
- Engagement: 15.5

**Cálculo:**
```
1. Trend Component: 0.85 * 100 * 0.40 = 34.0 puntos
2. Follower Component: (500/50) * 0.20 * 5 = 10.0 puntos
3. Badge Component: 15.0 * 0.15 = 2.25 puntos
4. Engagement Component: (15.5/10) * 0.25 = 0.39 puntos

Total: 34.0 + 10.0 + 2.25 + 0.39 = 46.64 puntos
```

**Normalización:**
- El score final se limita entre 0-100
- Se redondea a 2 decimales

