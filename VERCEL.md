# 🚀 Deployment en Vercel - Guía Completa

## 📋 Setup Inicial

### Backend (`apps/agents`)

1. **Crear proyecto en Vercel:**
   - Ve a https://vercel.com/new
   - Conecta repositorio `CeloBuild-`
   - **Root Directory**: `lootbox-minipay/apps/agents`
   - **Framework Preset**: Other
   - **Build Command**: (dejar vacío)
   - **Output Directory**: (dejar vacío)

2. **Variables de Entorno** (Settings → Environment Variables):
   ```
   GOOGLE_API_KEY=tu_api_key
   TAVILY_API_KEY=tu_api_key
   NEYNAR_API_KEY=tu_api_key
   CELO_RPC_URL=https://celo-sepolia.infura.io/v3/...
   CELO_PRIVATE_KEY=0x...
   LOOTBOX_VAULT_ADDRESS=0x...
   REGISTRY_ADDRESS=0x...
   MINTER_ADDRESS=0x...
   ```
   Ver todas las variables en `apps/agents/env.sample`

3. **Verificar deployment:**
   ```bash
   curl https://tu-backend.vercel.app/healthz
   # Debe retornar: {"status":"ok","supervisor_initialized":true}
   ```

### Frontend (`apps/web`)

1. **Crear proyecto en Vercel:**
   - Ve a https://vercel.com/new
   - Conecta repositorio `CeloBuild-`
   - **Root Directory**: `lootbox-minipay/apps/web`
   - **Framework Preset**: Next.js (auto-detectado)

2. **Variables de Entorno:**
   ```
   NEXT_PUBLIC_AGENT_SERVICE_URL=https://tu-backend.vercel.app
   AGENT_SERVICE_URL=https://tu-backend.vercel.app
   NEXT_PUBLIC_WC_PROJECT_ID=tu_walletconnect_project_id
   ```

## ✅ Verificación Post-Deployment

### Backend

- [ ] Status: "Ready" (verde) en Vercel
- [ ] Health check funciona: `/healthz` retorna `{"status":"ok"}`
- [ ] Root Directory: `lootbox-minipay/apps/agents`
- [ ] Variables de entorno configuradas

### Frontend

- [ ] Status: "Ready" (verde) en Vercel
- [ ] La app carga sin "Internal Server Error"
- [ ] Root Directory: `lootbox-minipay/apps/web`
- [ ] `NEXT_PUBLIC_AGENT_SERVICE_URL` apunta al backend

## 🔧 Troubleshooting

### Los pushes no se reflejan en Vercel

1. **Verificar Root Directory:**
   - Backend: `lootbox-minipay/apps/agents`
   - Frontend: `lootbox-minipay/apps/web`
   - Settings → General → Root Directory

2. **Verificar Webhook:**
   - Settings → Git
   - Repositorio conectado: `MarxMad/CeloBuild-`
   - Branch monitoreado: `main`

3. **Forzar redeploy:**
   - Deployments → ⋯ → Redeploy

### "Internal Server Error" en Frontend

1. **Verificar que el backend funciona:**
   ```bash
   curl https://tu-backend.vercel.app/healthz
   ```

2. **Verificar variables de entorno del frontend:**
   - `NEXT_PUBLIC_AGENT_SERVICE_URL` debe ser la URL del backend
   - Sin trailing slash (`/`)
   - Con `https://`

3. **Ver logs de runtime:**
   - Deployments → Logs (no Build Logs)
   - Buscar errores de conexión al backend

### Backend retorna error en health check

1. **Verificar variables de entorno:**
   - Todas las de `apps/agents/env.sample` deben estar configuradas

2. **Ver logs:**
   - Deployments → Logs
   - Buscar errores de inicialización

3. **Health check detallado:**
   ```bash
   curl https://tu-backend.vercel.app/healthz
   # Si retorna "degraded", revisa qué variables faltan
   ```

## 📝 Notas Importantes

- **Root Directory es crítico**: Si está vacío o incorrecto, los deployments no funcionarán
- **Variables de entorno**: `NEXT_PUBLIC_*` son accesibles en el cliente, las demás solo en servidor
- **Health check**: Siempre prueba `/healthz` después de un deployment para verificar que funciona

