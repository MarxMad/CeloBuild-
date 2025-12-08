# 🔧 Fix para Error en Vercel

## ✅ Cambios Aplicados

He corregido el problema del serverless function en Vercel:

1. **Entry Point Mejorado** (`api/index.py`):
   - Mejor manejo de errores
   - Detección automática de entorno Vercel
   - Fallback a app básica si hay errores

2. **Detección de Vercel** (`src/main.py`):
   - Detecta automáticamente si está en Vercel
   - Deshabilita `lifespan` en serverless (causa problemas)
   - El scheduler no se ejecuta en Vercel (usa Vercel Cron Jobs)

## 📋 Verificación en Vercel

### 1. Variables de Entorno

Asegúrate de que TODAS estas variables estén configuradas en Vercel:

**Requeridas:**
- `CELO_PRIVATE_KEY`
- `LOOTBOX_VAULT_ADDRESS=0x3808D0C3525C4F85F1f8c9a881E3949327FB9cF7`
- `REGISTRY_ADDRESS=0x86C878108798e2Ce39B783127955B8F8A18ae2BE`
- `MINTER_ADDRESS=0x0d7370f79f77Ee701C5F40443F8C8969C28b3412`
- `CELO_RPC_URL`
- `NEYNAR_API_KEY`
- `GOOGLE_API_KEY`
- `TAVILY_API_KEY`

**Opcionales:**
- `MINIPAY_PROJECT_SECRET` (si usas MiniPay Tool API)
- `CUSD_ADDRESS=0x874069Fa1Eb16D44d622F2e0Ca25eeA172369bC1`

### 2. Configuración del Proyecto

En Vercel, verifica:
- **Root Directory:** `apps/agents`
- **Framework Preset:** Other (Python)
- **Build Command:** (dejar vacío o `pip install -r requirements.txt`)
- **Output Directory:** (dejar vacío)

### 3. Probar Health Check

Después del deployment:

```bash
curl https://tu-backend.vercel.app/healthz
```

Debe retornar: `{"status":"ok"}`

## ⚠️ Limitaciones de Vercel Serverless

**IMPORTANTE:** Vercel Serverless Functions tienen limitaciones:

1. **Timeout:** 10 segundos (plan gratuito), 60 segundos (pro)
2. **Scheduler:** No funciona en serverless (las funciones son efímeras)
3. **Estado:** No persiste entre invocaciones

### Soluciones:

**Opción 1: Usar Vercel Cron Jobs** (Recomendado)
- Configura un cron job que llame a `/api/lootbox/run` cada 30 minutos
- Ver: https://vercel.com/docs/cron-jobs

**Opción 2: Desplegar en Railway/Render** (Mejor para producción)
- Railway o Render permiten procesos de larga duración
- El scheduler funcionará automáticamente
- Sin límites de timeout

## 🔍 Debugging

Si aún hay errores:

1. **Revisa los logs en Vercel:**
   - Ve a tu proyecto → Deployments → Logs
   - Busca errores de importación o inicialización

2. **Verifica dependencias:**
   - Asegúrate de que `requirements.txt` esté completo
   - Vercel instala automáticamente las dependencias

3. **Prueba localmente:**
   ```bash
   cd apps/agents
   export VERCEL=1
   python -m uvicorn api.index:app --reload
   ```

## 📝 Nota sobre Scheduler

El scheduler automático **NO funcionará en Vercel** porque:
- Las funciones serverless son efímeras
- No hay proceso de larga duración
- El scheduler necesita un proceso continuo

**Alternativas:**
1. Usar Vercel Cron Jobs para llamar al endpoint cada 30 min
2. Desplegar en Railway/Render para scheduler automático
3. Usar un servicio externo (cron-job.org) para hacer requests periódicos

---

**Los cambios ya están pusheados. Vercel debería redeployar automáticamente.**

