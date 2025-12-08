# 🚂 Deployment en Railway - Backend Python

## ⚠️ Problema: Railway Detecta Node.js

Si Railway detecta Node.js en lugar de Python, es porque encuentra el `package.json` en la raíz del monorepo.

## ✅ Solución Definitiva

### Opción 1: Configurar Root Directory ANTES del Deploy (RECOMENDADO)

1. **Elimina el servicio actual** en Railway
2. Crea un **nuevo servicio**
3. Selecciona "Deploy from GitHub repo"
4. Conecta tu repositorio `CeloBuild-`
5. **ANTES de hacer clic en "Deploy"**, ve a **Settings** (icono de engranaje)
6. **Root Directory**: `lootbox-minipay/apps/agents` ⚠️ **CRÍTICO**
7. **Builder**: Selecciona **"Nixpacks"** (no "Railpack")
8. **Start Command**: `uvicorn api.index:app --host 0.0.0.0 --port $PORT`
9. **Guarda** y luego haz clic en "Deploy"

### Opción 2: Si Ya Tienes un Servicio Creado

1. Ve a **Settings** del servicio
2. **Root Directory**: `lootbox-minipay/apps/agents`
3. **Builder**: Cambia a **"Nixpacks"**
4. **Start Command**: `uvicorn api.index:app --host 0.0.0.0 --port $PORT`
5. **Guarda**
6. Ve a **Deployments** y haz clic en **"Redeploy"**

### Verificar que Funciona

Después de configurar, Railway debería mostrar:
- ✅ **Builder**: "Nixpacks" (no "Railpack")
- ✅ **Detecta**: Python 3.11
- ✅ **Build**: `pip install -r requirements.txt`
- ✅ **Start**: `uvicorn api.index:app --host 0.0.0.0 --port $PORT`

## 📋 Setup en Railway

### Paso 1: Crear Proyecto

1. Ve a https://railway.app
2. Crea un nuevo proyecto
3. Selecciona "Deploy from GitHub repo"
4. Conecta tu repositorio `CeloBuild-`

### Paso 2: Configurar el Servicio

1. **Root Directory**: `lootbox-minipay/apps/agents` ⚠️ **CRÍTICO**
2. **Builder**: "Nixpacks" (no Railpack)
3. Railway debería detectar automáticamente que es Python por:
   - `requirements.txt`
   - `runtime.txt`
   - `nixpacks.toml`

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

## 🔧 Si Railway Detecta Node.js en Lugar de Python

Si Railway detecta Node.js (por el `package.json` en la raíz):

1. **Forzar detección de Python:**
   - Ve a **Settings** del servicio
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn api.index:app --host 0.0.0.0 --port $PORT`

2. **O usar Nixpacks explícitamente:**
   - Railway debería usar `nixpacks.toml` automáticamente
   - Si no, especifica el builder como "Nixpacks" en Settings

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

- Railway detecta automáticamente Python por `requirements.txt`
- El `nixpacks.toml` ayuda a Railway a configurar correctamente el entorno
- El `Procfile` es un fallback si Railway no detecta automáticamente
- El `railway.json` proporciona configuración explícita

