# 🔍 Análisis: ¿Por qué las Tendencias Tardan en Cargar?

## 📂 Archivos Clave de la Lógica de Tendencias

### 1. **Frontend - Componente que Muestra Tendencias**
**Archivo:** `apps/web/src/components/leaderboard.tsx`
- **Líneas 108-159:** Función `fetchAllData()` que hace el request
- **Línea 114:** `fetch("/api/lootbox/trends?limit=10")` - Request al endpoint

### 2. **Next.js API Route (Proxy)**
**Archivo:** `apps/web/src/app/api/lootbox/trends/route.ts`
- **Líneas 7-33:** Proxea la request al backend de Python
- **Línea 16:** `fetch(backendUrl)` - Llama al backend FastAPI

### 3. **Backend FastAPI - Endpoint de Tendencias**
**Archivo:** `apps/agents/src/main.py`
- **Líneas 473-486:** Endpoint `/api/lootbox/trends`
- **Línea 482:** `trends = active_supervisor.trends_store.recent(limit)` - Solo lee del store

### 4. **Store de Tendencias (Almacenamiento)**
**Archivo:** `apps/agents/src/stores/trends.py`
- **Líneas 46-50:** Método `recent()` que lee del archivo JSON
- **Línea 70-74:** En Vercel usa `/tmp/lootbox/trends.json` (archivo local)

### 5. **Agente que Detecta Tendencias**
**Archivo:** `apps/agents/src/graph/trend_watcher.py`
- **Líneas 55-98:** Lógica principal de detección
- **Líneas 64-68:** Llama a `fetch_trending_feed()` (API Neynar)
- **Líneas 76-82:** Llama a `fetch_casts_from_users()` (API Neynar)
- **Líneas 88-92:** Llama a `fetch_recent_casts()` (API Neynar)

### 6. **Cliente de Neynar API**
**Archivo:** `apps/agents/src/tools/farcaster.py`
- **Líneas 636-701:** `fetch_trending_feed()` - Hace request a Neynar
- **Línea 666:** Timeout de 10 segundos por request
- **Líneas 64-68 en trend_watcher.py:** Hace 3 llamadas diferentes a Neynar

### 7. **Scheduler Automático (Generación de Tendencias)**
**Archivo:** `apps/agents/src/scheduler.py`
- **Líneas 23-45:** `run_automatic_scan()` - Ejecuta detección automática
- **Líneas 66-72:** Se ejecuta cada 30 minutos (solo si NO es serverless)
- **Línea 58:** En Vercel (serverless), el scheduler está **DESHABILITADO**

### 8. **Vercel Cron Jobs (Alternativa al Scheduler)**
**Archivo:** `apps/agents/vercel.json`
- **Líneas 9-13:** Cron job cada 6 horas (`0 */6 * * *`)
- **Línea 11:** Llama a `/api/lootbox/scan` (que no existe, debería ser `/api/lootbox/trigger`)

---

## ⚠️ Problemas Identificados que Causan Lentitud

### **Problema 1: El Endpoint Solo LEE, No GENERA Tendencias**
```python
# apps/agents/src/main.py línea 482
trends = active_supervisor.trends_store.recent(limit)
```
- El endpoint `/api/lootbox/trends` solo lee del archivo JSON
- **NO genera nuevas tendencias** si el archivo está vacío o desactualizado
- Si no hay tendencias en el store, retorna lista vacía `[]`

### **Problema 2: Scheduler Deshabilitado en Vercel**
```python
# apps/agents/src/scheduler.py línea 58-62
is_serverless = os.getenv("VERCEL") is not None
if is_serverless:
    logger.info("⚠️ Entorno serverless detectado - scheduler deshabilitado")
```
- En Vercel, el scheduler automático **NO funciona**
- Las funciones serverless son efímeras y no pueden mantener procesos en background
- Las tendencias solo se generan cuando alguien llama a `/api/lootbox/trigger` manualmente

### **Problema 3: Cron Job Mal Configurado**
```json
// apps/agents/vercel.json línea 11
"path": "/api/lootbox/scan"  // ❌ Este endpoint NO existe
```
- El cron job apunta a `/api/lootbox/scan` que **no existe**
- Debería apuntar a `/api/lootbox/trigger` (línea 558 en main.py)
- O mejor aún, crear un endpoint específico `/api/lootbox/scan`

### **Problema 4: Múltiples Llamadas a Neynar API (Lentitud)**
```python
# apps/agents/src/graph/trend_watcher.py
viral_casts = await fetch_trending_feed(limit=15)      # ~2-3 segundos
community_casts = await fetch_casts_from_users(...)    # ~3-5 segundos
recent_casts = await fetch_recent_casts(limit=10)      # ~2-3 segundos
```
- Se hacen **3 llamadas secuenciales** a la API de Neynar
- Cada llamada tiene timeout de 10 segundos
- **Total: 6-11 segundos** solo en llamadas a API
- Además, cada llamada consume créditos de Neynar

### **Problema 5: Almacenamiento Efímero en Vercel**
```python
# apps/agents/src/stores/trends.py línea 70-71
if os.getenv("VERCEL"):
    base_path = Path("/tmp/lootbox")  # Se borra entre invocaciones
```
- En Vercel, `/tmp` se borra entre invocaciones de funciones serverless
- Las tendencias guardadas pueden perderse si no hay tráfico constante
- Cada "cold start" empieza con un store vacío

### **Problema 6: No Hay Cache en el Frontend**
```typescript
// apps/web/src/components/leaderboard.tsx línea 114
fetch("/api/lootbox/trends?limit=10", { cache: "no-store" })
```
- El frontend siempre hace request nuevo (sin cache)
- No hay fallback a `localStorage` si el backend tarda
- Si el backend está lento, el usuario ve loading indefinido

---

## 🚀 Soluciones Propuestas

### **Solución 1: Arreglar Cron Job de Vercel**
```json
// apps/agents/vercel.json
"crons": [
  {
    "path": "/api/lootbox/trigger",  // ✅ Cambiar a endpoint correcto
    "schedule": "*/30 * * * *"       // ✅ Cada 30 minutos (más frecuente)
  }
]
```

### **Solución 2: Crear Endpoint Dedicado para Scan**
```python
# apps/agents/src/main.py
@app.post("/api/lootbox/scan")
async def scan_trends():
    """Endpoint optimizado para Vercel Cron Jobs."""
    # Similar a trigger_scan pero sin payload requerido
```

### **Solución 3: Optimizar Llamadas a Neynar (Paralelas)**
```python
# apps/agents/src/graph/trend_watcher.py
# En lugar de secuencial:
viral_casts = await fetch_trending_feed(...)
community_casts = await fetch_casts_from_users(...)
recent_casts = await fetch_recent_casts(...)

# Hacer en paralelo:
viral_casts, community_casts, recent_casts = await asyncio.gather(
    fetch_trending_feed(...),
    fetch_casts_from_users(...),
    fetch_recent_casts(...)
)
# Reduce tiempo de ~9s a ~3s (el más lento)
```

### **Solución 4: Cache en Frontend con Fallback**
```typescript
// apps/web/src/components/leaderboard.tsx
const cachedTrends = localStorage.getItem("trends_cache");
if (cachedTrends) {
  setTrendDetails(JSON.parse(cachedTrends)); // Mostrar cache inmediatamente
}

// Luego hacer fetch en background
fetch("/api/lootbox/trends").then(...).then(data => {
  localStorage.setItem("trends_cache", JSON.stringify(data));
});
```

### **Solución 5: Endpoint Híbrido (Leer + Generar si Vacío)**
```python
# apps/agents/src/main.py
@app.get("/api/lootbox/trends")
async def get_trends(limit: int = 10):
    trends = trends_store.recent(limit)
    
    # Si no hay tendencias, generar en background
    if not trends:
        asyncio.create_task(generate_trends_async())
        # Retornar respuesta inmediata con mensaje
        return {"items": [], "generating": True}
    
    return {"items": trends}
```

### **Solución 6: Usar Upstash Redis para Persistencia**
```python
# apps/agents/src/stores/trends.py
# En lugar de archivo JSON, usar Redis
# Las tendencias persisten entre invocaciones serverless
```

---

## 📊 Flujo Actual vs Flujo Optimizado

### **Flujo Actual (Lento):**
```
Usuario carga página
  ↓
Frontend: fetch("/api/lootbox/trends")
  ↓
Next.js API: Proxea a backend
  ↓
Backend: Lee trends_store.recent() → [] (vacío)
  ↓
Usuario ve: "Sin tendencias" o loading infinito
```

### **Flujo Optimizado (Rápido):**
```
Usuario carga página
  ↓
Frontend: Muestra cache de localStorage (inmediato)
  ↓
Frontend: fetch("/api/lootbox/trends") en background
  ↓
Backend: Si vacío, genera en background y retorna cache
  ↓
Frontend: Actualiza UI cuando llegan datos nuevos
```

---

## 🎯 Prioridad de Implementación

1. **ALTA:** Arreglar cron job de Vercel (5 min)
2. **ALTA:** Agregar cache en frontend con fallback (15 min)
3. **MEDIA:** Optimizar llamadas a Neynar (paralelas) (10 min)
4. **MEDIA:** Endpoint híbrido que genere si está vacío (20 min)
5. **BAJA:** Migrar a Redis para persistencia (1 hora)

---

**Última actualización:** 2025-01-13

