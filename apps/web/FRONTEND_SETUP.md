# 🎨 Configuración del Frontend

## ⚠️ Errores 404 Comunes

Si ves errores 404 en las rutas `/api/leaderboard` o `/api/lootbox`, verifica:

### 1. Variables de Entorno

Crea un archivo `.env.local` en `apps/web/`:

```bash
# URL del backend (agentes)
AGENT_SERVICE_URL="http://localhost:8001"
NEXT_PUBLIC_AGENT_SERVICE_URL="http://localhost:8001"

# Si el backend está en Vercel, usa:
# AGENT_SERVICE_URL="https://tu-backend.vercel.app"
# NEXT_PUBLIC_AGENT_SERVICE_URL="https://tu-backend.vercel.app"
```

### 2. Servidor Next.js Debe Estar Corriendo

```bash
cd apps/web
npm run dev
```

El servidor debe estar en `http://localhost:3000`

### 3. Backend Debe Estar Corriendo

El backend debe estar disponible en la URL configurada en `AGENT_SERVICE_URL`.

**Para desarrollo local:**
```bash
cd apps/agents
python -m uvicorn src.main:app --reload --port 8001
```

**Para producción (Vercel):**
- El backend debe estar desplegado en Vercel
- Usa la URL de Vercel en `AGENT_SERVICE_URL`

### 4. Verificar que las Rutas API Funcionen

**Leaderboard:**
```bash
curl http://localhost:3000/api/leaderboard?limit=5
```

**Lootbox:**
```bash
curl -X POST http://localhost:3000/api/lootbox \
  -H "Content-Type: application/json" \
  -d '{"frameId":"","channelId":"global","trendScore":0.5,"rewardType":"nft"}'
```

## 🔍 Debugging

### Ver Logs del Frontend

Abre la consola del navegador (F12) y busca:
- Errores de conexión al backend
- Variables de entorno no configuradas
- Errores 404 en las rutas API

### Ver Logs del Backend

Si el backend está corriendo localmente:
```bash
# Los logs aparecerán en la terminal donde corre uvicorn
```

Si está en Vercel:
- Ve a tu proyecto en Vercel
- Deployments → Logs

## ✅ Checklist

- [ ] Archivo `.env.local` creado en `apps/web/`
- [ ] `AGENT_SERVICE_URL` configurado correctamente
- [ ] Servidor Next.js corriendo (`npm run dev`)
- [ ] Backend corriendo y accesible
- [ ] Rutas API responden correctamente
- [ ] No hay errores en la consola del navegador

## 🚀 Para Producción (Vercel)

1. **Configura variables de entorno en Vercel:**
   - Ve a tu proyecto → Settings → Environment Variables
   - Agrega `AGENT_SERVICE_URL` con la URL de tu backend en Vercel

2. **Redeploy:**
   - Vercel redeployará automáticamente cuando hagas push
   - O manualmente: Deployments → Redeploy

---

**Nota:** Si las rutas API retornan 404, el frontend ahora retornará datos vacíos en lugar de errores, para que la UI no se rompa.

