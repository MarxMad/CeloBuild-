# ⏰ Configuración de Vercel Cron Jobs

## 🎯 Problema

En Vercel Serverless, el scheduler automático **NO funciona** porque las funciones son efímeras. Necesitas usar **Vercel Cron Jobs** para ejecutar scans automáticos.

## ✅ Solución Implementada

He creado:
1. **Endpoint `/api/lootbox/scan`**: Para ejecutar scans manualmente
2. **Configuración en `vercel.json`**: Cron job cada 30 minutos

## 📋 Configuración en Vercel

### Opción 1: Usar vercel.json (Ya configurado)

El archivo `vercel.json` ya tiene la configuración:

```json
{
  "crons": [
    {
      "path": "/api/lootbox/scan",
      "schedule": "*/30 * * * *"
    }
  ]
}
```

**Nota:** Vercel Cron Jobs solo están disponibles en planes **Pro** o superiores. Si estás en plan gratuito, usa la Opción 2.

### Opción 2: Configurar Manualmente en Vercel Dashboard

1. Ve a tu proyecto en Vercel
2. Settings → Cron Jobs
3. Agrega un nuevo cron job:
   - **Path:** `/api/lootbox/scan`
   - **Schedule:** `*/30 * * * *` (cada 30 minutos)
   - **Method:** POST

### Opción 3: Usar Servicio Externo (Plan Gratuito)

Si estás en plan gratuito, usa un servicio como [cron-job.org](https://cron-job.org):

1. Crea una cuenta
2. Crea un nuevo cron job
3. **URL:** `https://tu-backend.vercel.app/api/lootbox/scan`
4. **Method:** POST
5. **Schedule:** Cada 30 minutos

## 🧪 Probar el Endpoint

Puedes probar manualmente:

```bash
curl -X POST https://tu-backend.vercel.app/api/lootbox/scan
```

Debería retornar:
```json
{
  "status": "success",
  "summary": "...",
  "tx_hash": "...",
  "mode": "...",
  "reward_type": "..."
}
```

## 🔍 Verificar que Funciona

1. **Revisa los logs en Vercel** después de que se ejecute el cron
2. **Verifica el leaderboard:**
   ```bash
   curl https://tu-backend.vercel.app/api/lootbox/leaderboard?limit=5
   ```
3. **Deberías ver nuevas entradas** con `reward_type` diferente de "pending"

## ⚠️ Nota sobre Plan Gratuito

Si estás en plan gratuito de Vercel:
- Los Cron Jobs no están disponibles
- Usa un servicio externo (cron-job.org, EasyCron, etc.)
- O despliega el backend en Railway/Render (recomendado para producción)

---

**Una vez configurado, el sistema ejecutará scans automáticamente cada 30 minutos y el leaderboard se llenará con tendencias y ganadores reales.**

