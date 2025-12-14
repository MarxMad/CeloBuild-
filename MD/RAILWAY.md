# 🚂 Deployment en Railway - Backend Python

## ⚠️ Problema: Railway Detecta Node.js

Railway está detectando Node.js del monorepo (por el `package.json` en la raíz) y está intentando instalar pnpm, lo cual falla porque no hay `pnpm-lock.yaml` en el directorio del backend.

## ✅ Solución: Usar Dockerfile Personalizado

He creado un `Dockerfile` que fuerza solo Python, evitando la detección automática de Node.js. Esta es la solución más confiable para monorepos con múltiples lenguajes.

**IMPORTANTE:** El archivo `nixpacks.toml` ha sido eliminado para forzar a Railway a usar el Dockerfile en lugar de Nixpacks.

## 📋 Pasos para Configurar en Railway

### Paso 1: Verificar Root Directory (CRÍTICO)

1. En Railway, ve a **Settings → General**
2. **Root Directory**: Debe ser exactamente `lootbox-minipay/apps/agents` ⚠️ **CRÍTICO**
3. Si está vacío o incorrecto:
   - Cámbialo a: `lootbox-minipay/apps/agents`
   - **Guarda**

### Paso 2: Configurar Builder a Dockerfile (CRÍTICO)

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
2. Haz clic en **"Redeploy"** del último deployment
3. O crea un nuevo deployment desde el commit más reciente
4. Ahora debería usar el Dockerfile personalizado (solo Python, sin Node.js)

## 🔍 Verificar que Funciona

Después del redeploy, en los logs deberías ver:
- ✅ **Builder**: "Dockerfile" (no "Railpack" ni "Nixpacks")
- ✅ **Base Image**: `python:3.11-slim`
- ✅ **Build**: `pip install -r requirements.txt`
- ✅ **Start**: `uvicorn api.index:app --host 0.0.0.0 --port $PORT`
- ❌ **NO** debería intentar `pnpm install` ni `npm install`
- ❌ **NO** debería ver "Using Nixpacks" en los logs

## 🔧 Si Railway Sigue Detectando Node.js

Si Railway sigue detectando Node.js después de configurar Dockerfile:

1. **Verificar Root Directory:**
   - Asegúrate de que el Root Directory sea exactamente `lootbox-minipay/apps/agents`
   - El Root Directory debe apuntar al directorio donde está el `Dockerfile`

2. **Verificar Builder en Settings:**
   - Ve a **Settings → Build**
   - **Builder**: Debe ser "Dockerfile" (no "Railpack" ni "Nixpacks")
   - Si está en "Railpack" o "Nixpacks", cámbialo manualmente a "Dockerfile"

3. **Eliminar Configuración de Nixpacks:**
   - Asegúrate de que no haya un archivo `nixpacks.toml` en el directorio `apps/agents`
   - Si existe, elimínalo (ya fue eliminado en el commit más reciente)

4. **Forzar Redeploy:**
   - Ve a **Deployments**
   - Haz clic en **"Redeploy"** del último deployment
   - O crea un nuevo deployment desde el commit más reciente

5. **Verificar .dockerignore:**
   - El archivo `.dockerignore` debe excluir `package.json`, `pnpm-lock.yaml`, `node_modules`, etc.
   - Esto evita que Docker copie archivos de Node.js al contexto del build

## 📝 Setup Completo en Railway

### Paso 1: Crear Proyecto

1. Ve a https://railway.app
2. Crea un nuevo proyecto
3. Selecciona "Deploy from GitHub repo"
4. Conecta tu repositorio `CeloBuild-`

### Paso 2: Configurar el Servicio

1. **Root Directory**: `lootbox-minipay/apps/agents` ⚠️ **CRÍTICO**
2. **Builder**: "Dockerfile" (no Railpack ni Nixpacks)
3. **Dockerfile Path**: `Dockerfile` (debería detectarlo automáticamente)
4. Railway debería usar el Dockerfile que solo copia archivos de Python

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

1. Railway debería usar el Dockerfile (no Nixpacks)
2. El comando de inicio será: `uvicorn api.index:app --host 0.0.0.0 --port $PORT`
3. Verifica los logs para confirmar que arrancó correctamente

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
- El archivo `nixpacks.toml` ha sido eliminado para evitar conflictos

## 🆘 Troubleshooting

### Error: "Cannot install with frozen-lockfile because pnpm-lock.yaml is absent"

**Causa:** Railway está usando Nixpacks/Railpack y detectando Node.js.

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

### Error: "Using Nixpacks" en los logs

**Causa:** Railway está usando Nixpacks en lugar del Dockerfile.

**Solución:**
1. Ve a Settings → Build
2. Cambia el Builder a "Dockerfile"
3. Verifica que no haya un archivo `nixpacks.toml` en `apps/agents`
4. Haz un Redeploy
