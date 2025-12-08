# 🚀 Deployment en Vercel - Guía Completa

## 📋 Setup Inicial

### Backend (`apps/agents`)

1. **Crear proyecto en Vercel:**
   - Ve a https://vercel.com/new
   - Conecta repositorio `CeloBuild-`
   - **Root Directory**: `lootbox-minipay/apps/agents` ⚠️ **CRÍTICO**
   - **Framework Preset**: `Other` o `Python`
   - **Build Command**: (vacío) o `pip install -r requirements.txt`
   - **Install Command**: (vacío) o `pip install -r requirements.txt`
   - **Output Directory**: (vacío)

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
   
   **⚠️ IMPORTANTE:** 
   - Reemplaza `https://tu-backend.vercel.app` con la URL real de tu backend desplegado en Vercel
   - Puedes encontrar la URL en: **Settings → Domains** del proyecto del backend
   - Después de agregar las variables, haz un **Redeploy** del frontend para que tome efecto
   - Si ves el error "DEPLOYMENT_NOT_FOUND", verifica que `AGENT_SERVICE_URL` esté configurado correctamente

## 🔧 Troubleshooting

### Los pushes no se reflejan en Vercel

**⚠️ PROBLEMA MÁS COMÚN: Root Directory incorrecto o vacío**

1. **Verificar Root Directory:**
   - Settings → General → Root Directory
   - Backend: `lootbox-minipay/apps/agents`
   - Frontend: `lootbox-minipay/apps/web`
   - Si está vacío o incorrecto, cámbialo y guarda (esto activará un nuevo deployment)

2. **Verificar Webhook:**
   - Settings → Git
   - Repository: `MarxMad/CeloBuild-`
   - Branch: `main`
   - Si no funciona, desconecta y reconecta el repositorio

3. **Forzar redeploy:**
   - Deployments → ⋯ → Redeploy
   - O: `git commit --allow-empty -m "trigger deploy" && git push`

### Error: "Root Directory does not exist"

**Causa**: Vercel está usando un commit antiguo

**Solución**:
1. Ve a **Deployments** y verifica que use el commit más reciente
2. Si usa un commit antiguo:
   - Settings → Git → Reconecta el repositorio
   - O haz un **Redeploy** manual

### Error: Build Command incorrecto (pnpm en lugar de pip)

**Síntoma**: Build Command tiene `pnpm build` o `pnpm install`

**Solución**:
1. Settings → Build and Deployment
2. **Build Command**: (vacío) o `pip install -r requirements.txt`
3. **Install Command**: (vacío) o `pip install -r requirements.txt`
4. Guarda

### "Internal Server Error" en Backend

1. **Diagnosticar:**
   ```bash
   curl https://tu-backend.vercel.app/debug
   # Muestra el error específico y variables faltantes
   ```

2. **Verificar variables de entorno:**
   - Settings → Environment Variables
   - Todas las variables críticas deben estar configuradas

3. **Ver logs:**
   - Deployments → Logs (no Build Logs)
   - Busca errores de inicialización

4. **Health check:**
   ```bash
   curl https://tu-backend.vercel.app/healthz
   # Si retorna "degraded", revisa qué variables faltan
   ```

### "Internal Server Error" en Frontend

1. **Verificar que el backend funciona:**
   ```bash
   curl https://tu-backend.vercel.app/healthz
   ```

2. **Verificar variables de entorno:**
   - `NEXT_PUBLIC_AGENT_SERVICE_URL` debe ser la URL del backend
   - Sin trailing slash (`/`)
   - Con `https://`

3. **Ver logs de runtime:**
   - Deployments → Logs
   - Buscar errores de conexión al backend

## ✅ Checklist de Verificación

### Backend
- [ ] Root Directory: `lootbox-minipay/apps/agents`
- [ ] Framework Preset: `Other` o `Python`
- [ ] Build Command: (vacío) o `pip install -r requirements.txt`
- [ ] Variables de entorno configuradas
- [ ] Health check funciona: `/healthz` retorna `{"status":"ok"}`
- [ ] Último deployment usa el commit más reciente

### Frontend
- [ ] Root Directory: `lootbox-minipay/apps/web`
- [ ] Framework Preset: `Next.js`
- [ ] `NEXT_PUBLIC_AGENT_SERVICE_URL` apunta al backend
- [ ] La app carga sin "Internal Server Error"

## 📝 Notas Importantes

- **Root Directory es crítico**: Si está vacío o incorrecto, los deployments no funcionarán
- **Commit antiguo**: Si Vercel usa un commit antiguo, reconecta el repositorio o haz redeploy
- **Build Command**: No debe tener comandos de `pnpm` para el backend (es Python, no Node.js)
- **Variables de entorno**: `NEXT_PUBLIC_*` son accesibles en el cliente, las demás solo en servidor
- **Health check**: Siempre prueba `/healthz` después de un deployment
- **Debug endpoint**: Usa `/debug` para diagnosticar problemas específicos
