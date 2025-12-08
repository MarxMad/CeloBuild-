# 🚂 Deployment en Railway - Backend Python

## ⚠️ Problema: Railpack Detecta Node.js

Railway ahora usa **Railpack** por defecto (Nixpacks está deprecado). Railpack está detectando Node.js del monorepo y está intentando instalar pnpm, lo cual falla.

## ✅ Solución: Usar Dockerfile Personalizado

He creado un `Dockerfile` que fuerza solo Python, evitando la detección automática de Node.js. Esta es la solución más confiable para monorepos.

### Paso 1: Verificar Root Directory

1. En Railway, ve a **Settings → General**
2. **Root Directory**: Debe ser exactamente `lootbox-minipay/apps/agents` ⚠️ **CRÍTICO**
3. Si está vacío o incorrecto:
   - Cámbialo a: `lootbox-minipay/apps/agents`
   - **Guarda**

### Paso 2: Configurar Builder a Dockerfile

1. En **Settings → Build**
2. **Builder**: Cambia a **"Dockerfile"** (no "Railpack" ni "Nixpacks")
3. **Dockerfile Path**: `Dockerfile` (debería detectarlo automáticamente)
4. Guarda

**Nota:** El archivo `railway.json` ya está configurado para usar Dockerfile, pero puedes verificarlo en Settings.

### Paso 3: Configurar Start Command

1. En **Settings → Deploy**
2. **Start Command**: `uvicorn api.index:app --host 0.0.0.0 --port $PORT`
3. Guarda

### Paso 4: Redeploy

1. Ve a **Deployments**
2. Haz clic en **"Redeploy"**
3. Ahora debería usar el Dockerfile personalizado (solo Python, sin Node.js)

## 🔍 Verificar que Funciona

Después del redeploy, en los logs deberías ver:
- ✅ **Builder**: "Dockerfile" (no "Railpack" ni "Nixpacks")
- ✅ **Base Image**: `python:3.11-slim`
- ✅ **Build**: `pip install -r requirements.txt`
- ✅ **Start**: `uvicorn api.index:app --host 0.0.0.0 --port $PORT`
- ❌ **NO** debería intentar `pnpm install` ni `npm install`

## 📋 Setup en Railway

### Paso 1: Crear Proyecto

1. Ve a https://railway.app
2. Crea un nuevo proyecto
3. Selecciona "Deploy from GitHub repo"
4. Conecta tu repositorio `CeloBuild-`

### Paso 2: Configurar el Servicio

1. **Root Directory**: `lootbox-minipay/apps/agents` ⚠️ **CRÍTICO**
2. **Builder**: "Dockerfile" (no Railpack ni Nixpacks)
3. **Dockerfile Path**: `Dockerfile` (debería detectarlo automáticamente)
4. El Dockerfile usa `python:3.11-slim` como base image

### Paso 3: Variables de Entorno

En Railway, ve a **Variables** y agrega:

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

### Paso 4: Verificar Deployment

1. Railway debería detectar automáticamente Python
2. El comando de inicio será: `uvicorn api.index:app --host 0.0.0.0 --port $PORT`
3. Verifica los logs para confirmar que arrancó correctamente

## 🔧 Si Railway Sigue Detectando Node.js

Si Railway sigue detectando Node.js después de configurar Dockerfile:

1. **Verificar Root Directory:**
   - Asegúrate de que el Root Directory sea exactamente `lootbox-minipay/apps/agents`
   - El Root Directory debe apuntar al directorio donde está el `Dockerfile`

2. **Verificar Builder en Settings:**
   - Ve a **Settings → Build**
   - **Builder**: Debe ser "Dockerfile" (no "Railpack" ni "Nixpacks")
   - Si está en "Railpack", cámbialo manualmente a "Dockerfile"

3. **Forzar Redeploy:**
   - Ve a **Deployments**
   - Haz clic en **"Redeploy"** del último deployment
   - O crea un nuevo deployment desde el commit más reciente

4. **Alternativa: Usar Railpack con Variables de Entorno:**
   Si prefieres usar Railpack en lugar de Dockerfile, agrega estas variables de entorno en Railway:
   - `RAILPACK_INSTALL_COMMAND`: `pip install -r requirements.txt`
   - `RAILPACK_BUILD_COMMAND`: (dejar vacío o `pip install -r requirements.txt`)
   - Y configura el Builder como "Railpack" en Settings

## ✅ Verificación

1. **Health check:**
   ```bash
   curl https://tu-proyecto.railway.app/healthz
   ```
   Debe retornar: `{"status":"ok","supervisor_initialized":true}`

2. **Debug endpoint:**
   ```bash
   curl https://tu-proyecto.railway.app/debug
   ```

## 📝 Notas

- **Railway ahora usa Railpack por defecto** (Nixpacks está deprecado)
- **Usar Dockerfile es la solución más confiable** para monorepos con múltiples lenguajes
- El `Dockerfile` copia solo archivos de Python, evitando la detección de Node.js
- El `railway.json` y `railway.toml` están configurados para usar Dockerfile
- El Root Directory **debe** apuntar a `lootbox-minipay/apps/agents` donde está el Dockerfile

## 🆘 Troubleshooting

### Error: "Cannot install with frozen-lockfile because pnpm-lock.yaml is absent"

**Causa:** Railway está usando Railpack y detectando Node.js.

**Solución:**
1. Cambia el Builder a "Dockerfile" en Settings → Build
2. Verifica que el Root Directory sea `lootbox-minipay/apps/agents`
3. Haz un Redeploy

### Error: "The specified Root Directory does not exist"

**Causa:** El Root Directory está mal configurado o Railway está usando un commit antiguo.

**Solución:**
1. Verifica que el Root Directory sea exactamente `lootbox-minipay/apps/agents` (sin trailing slash)
2. Haz un nuevo deployment desde el commit más reciente
3. O desconecta y vuelve a conectar el repositorio en Railway

