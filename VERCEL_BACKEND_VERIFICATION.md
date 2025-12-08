# ✅ Verificación: ¿Cómo Saber que el Backend Está Bien Desplegado?

## 🔍 Qué Deberías Ver en Vercel para el Backend

### 1. Proyecto del Backend en el Dashboard

En tu dashboard de Vercel (https://vercel.com/dashboard), deberías ver:

- ✅ Un proyecto separado del frontend (ej: `lootbox-agents` o `celo-build-agents`)
- ✅ El proyecto debe mostrar "Ready" con un punto verde
- ✅ Debe tener deployments recientes

### 2. Página del Proyecto del Backend

Cuando entras al proyecto del backend, deberías ver:

**En la pestaña "Overview":**
- ✅ **Production Deployment**: Debe mostrar "Ready" (verde)
- ✅ **Status**: "Ready Latest" con punto verde
- ✅ **Domains**: Debe mostrar una URL como `lootbox-agents-abc123.vercel.app`
- ✅ **Source**: Debe mostrar el branch (ej: `main`) y el último commit

**En la pestaña "Deployments":**
- ✅ Debe haber deployments recientes
- ✅ El último deployment debe tener el mismo commit SHA que tu último push
- ✅ Status debe ser "Ready" (verde)

**En la pestaña "Settings" → "General":**
- ✅ **Root Directory**: Debe ser `lootbox-minipay/apps/agents`
- ✅ **Framework Preset**: Debe ser "Other" o "Python"

**En la pestaña "Settings" → "Environment Variables":**
- ✅ Debe tener todas las variables de `env.sample` configuradas
- ✅ Variables críticas:
  - `GOOGLE_API_KEY`
  - `TAVILY_API_KEY`
  - `NEYNAR_API_KEY`
  - `CELO_RPC_URL`
  - `CELO_PRIVATE_KEY`
  - `LOOTBOX_VAULT_ADDRESS`
  - `REGISTRY_ADDRESS`
  - `MINTER_ADDRESS`

### 3. Verificar que el Backend Funciona

**Prueba el Health Check:**

1. Copia la URL del backend desde Vercel (ej: `https://lootbox-agents-abc123.vercel.app`)
2. Abre en tu navegador o usa curl:
   ```
   https://tu-backend.vercel.app/healthz
   ```

**Respuestas esperadas:**

✅ **Si funciona correctamente:**
```json
{
  "status": "ok",
  "supervisor_initialized": true
}
```

⚠️ **Si faltan variables de entorno:**
```json
{
  "status": "degraded",
  "supervisor_initialized": false,
  "missing_env_vars": ["GOOGLE_API_KEY", "CELO_PRIVATE_KEY", ...],
  "message": "Faltan X variables de entorno críticas"
}
```

❌ **Si hay un error:**
```json
{
  "status": "error",
  "message": "Failed to initialize app",
  "error": "...",
  "type": "..."
}
```

## 🔄 ¿Por Qué los Pushes No Se Reflejan?

### Problema 1: Root Directory Incorrecto

**Síntoma**: Los pushes no activan nuevos deployments.

**Solución**:
1. Ve a Settings → General
2. Verifica que **Root Directory** sea: `lootbox-minipay/apps/agents`
3. Si está vacío o incorrecto, cámbialo y guarda
4. Esto debería activar un nuevo deployment

### Problema 2: Webhook de GitHub Roto

**Síntoma**: Los pushes a GitHub no activan deployments en Vercel.

**Solución**:
1. Ve a Settings → Git
2. Verifica que el repositorio esté conectado
3. Verifica que el branch monitoreado sea `main`
4. Si hay problemas, desconecta y vuelve a conectar el repositorio

### Problema 3: El Proyecto No Está Conectado al Repositorio Correcto

**Síntoma**: Los deployments no se actualizan con los pushes.

**Solución**:
1. Ve a Settings → Git
2. Verifica que el repositorio sea `MarxMad/CeloBuild-`
3. Verifica que el branch sea `main`
4. Si no coincide, reconecta el repositorio

## 📋 Checklist de Verificación Completa

### Backend en Vercel

- [ ] Proyecto existe en el dashboard
- [ ] Status: "Ready" (verde)
- [ ] Root Directory: `lootbox-minipay/apps/agents`
- [ ] Framework: Other/Python
- [ ] Variables de entorno configuradas (todas las de `env.sample`)
- [ ] Health check funciona: `/healthz` retorna `{"status":"ok"}`
- [ ] Último deployment coincide con último commit en GitHub
- [ ] Webhook de GitHub activo

### Verificación del Health Check

1. **Abre la URL del backend en tu navegador:**
   ```
   https://tu-backend.vercel.app/healthz
   ```

2. **Deberías ver:**
   ```json
   {
     "status": "ok",
     "supervisor_initialized": true
   }
   ```

3. **Si ves errores o "degraded":**
   - Revisa qué variables faltan
   - Agrega las variables faltantes en Settings → Environment Variables
   - Redesplega el backend

## 🚀 Forzar un Nuevo Deployment

Si los pushes no se reflejan automáticamente:

### Opción 1: Desde Vercel Dashboard

1. Ve a Deployments
2. Haz clic en los tres puntos (⋯) del último deployment
3. Selecciona **"Redeploy"**

### Opción 2: Commit Vacío

```bash
git commit --allow-empty -m "trigger backend redeploy"
git push
```

### Opción 3: Verificar y Corregir Root Directory

1. Ve a Settings → General
2. Si Root Directory está vacío o incorrecto:
   - Cámbialo a: `lootbox-minipay/apps/agents`
   - Guarda
   - Esto activará un nuevo deployment

## 🔍 Verificar que el Último Commit se Reflejó

1. Ve a tu proyecto del backend en Vercel
2. Ve a Deployments
3. Compara el **commit SHA** del último deployment con tu último commit en GitHub
4. Si no coinciden, el webhook no está funcionando

**Para ver tu último commit:**
```bash
git log --oneline -1
```

**En Vercel**, el commit SHA aparece en la sección "Source" del deployment.

## 💡 Señales de que el Backend Está Bien Desplegado

✅ **Señales positivas:**
- Health check retorna `{"status":"ok"}`
- Los deployments se actualizan con cada push
- No hay errores en los logs de runtime
- Las rutas API responden correctamente:
  - `/api/lootbox/leaderboard`
  - `/api/lootbox/trends`
  - `/api/lootbox/run`

❌ **Señales de problemas:**
- Health check retorna error
- "Internal Server Error" en todas las rutas
- Los deployments no se actualizan con los pushes
- Errores en los logs sobre variables de entorno faltantes

## 🐛 Troubleshooting Específico

### El backend muestra "Internal Server Error"

1. Ve a Deployments → Logs (no Build Logs)
2. Busca errores relacionados con:
   - Variables de entorno faltantes
   - Errores de importación
   - Errores de inicialización

3. Prueba el health check para ver qué variables faltan:
   ```bash
   curl https://tu-backend.vercel.app/healthz
   ```

### Los deployments no se actualizan

1. Verifica Root Directory en Settings → General
2. Verifica webhook en Settings → Git
3. Verifica que el branch monitoreado sea `main`
4. Si nada funciona, reconecta el repositorio

### El health check retorna "degraded"

Esto significa que el backend arrancó pero faltan variables de entorno.

1. Revisa la respuesta del health check para ver qué variables faltan
2. Agrega las variables faltantes en Settings → Environment Variables
3. Redesplega el backend

