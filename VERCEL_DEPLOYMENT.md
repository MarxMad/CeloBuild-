# 🚀 Guía de Deployment en Vercel

## 📋 Configuración de Proyectos

Tienes dos proyectos en Vercel:
- **Frontend**: https://celo-build-web-8rej.vercel.app/
- **Backend**: https://celo-build-web.vercel.app/

## 🔧 Configuración del Frontend

### Variables de Entorno Requeridas

En el proyecto del **Frontend** (`celo-build-web-8rej`), configura estas variables de entorno en Vercel:

1. Ve a **Settings** → **Environment Variables**
2. Agrega las siguientes variables:

```bash
AGENT_SERVICE_URL=https://celo-build-web.vercel.app
NEXT_PUBLIC_AGENT_SERVICE_URL=https://celo-build-web.vercel.app
NEXT_PUBLIC_WC_PROJECT_ID=tu_walletconnect_project_id
```

**Importante:**
- `AGENT_SERVICE_URL` es para las API routes del servidor (server-side)
- `NEXT_PUBLIC_AGENT_SERVICE_URL` es para el cliente (client-side) - aunque no se usa directamente, es bueno tenerlo
- Asegúrate de que la URL del backend termine **sin** `/` al final

### Configuración del Proyecto

1. **Root Directory**: `apps/web`
2. **Framework Preset**: Next.js (se detecta automáticamente)
3. **Build Command**: `cd ../.. && pnpm build --filter=web` (ya configurado en `vercel.json`)
4. **Install Command**: `cd ../.. && pnpm install` (ya configurado en `vercel.json`)

## 🔧 Configuración del Backend

### ⚠️ Problema: Backend en Vercel (Serverless)

El backend Python (FastAPI) **NO es ideal para Vercel** porque:
- Vercel tiene límites de tiempo de ejecución (10s en plan gratuito, 60s en Pro)
- Los agentes pueden tardar más tiempo en procesar
- Vercel está optimizado para funciones serverless, no para servicios de larga duración

### Opciones Recomendadas para el Backend:

#### Opción 1: Railway (Recomendado) 🚂

1. Ve a [Railway.app](https://railway.app)
2. Crea un nuevo proyecto desde GitHub
3. Selecciona el repositorio `CeloBuild-`
4. **Root Directory**: `apps/agents`
5. **Start Command**: `uvicorn src.main:app --host 0.0.0.0 --port $PORT`
6. Configura todas las variables de entorno desde `apps/agents/.env`
7. Railway te dará una URL como: `https://tu-backend.railway.app`

**Luego actualiza el frontend:**
```bash
AGENT_SERVICE_URL=https://tu-backend.railway.app
```

#### Opción 2: Render 🎨

1. Ve a [Render.com](https://render.com)
2. Crea un nuevo **Web Service**
3. Conecta tu repositorio de GitHub
4. **Root Directory**: `apps/agents`
5. **Build Command**: `pip install -e ".[dev]"`
6. **Start Command**: `uvicorn src.main:app --host 0.0.0.0 --port $PORT`
7. Configura todas las variables de entorno
8. Render te dará una URL como: `https://tu-backend.onrender.com`

#### Opción 3: Mantener en Vercel (con limitaciones) ⚠️

Si quieres mantener el backend en Vercel, necesitas:

1. **Crear un proyecto separado** para el backend
2. **Root Directory**: `apps/agents`
3. **Framework Preset**: Other
4. Crear `api/index.py` o usar serverless functions

**Nota**: Esto requiere refactorizar el código para que sea compatible con serverless.

### Variables de Entorno del Backend

El backend necesita todas las variables de `apps/agents/.env`:

```bash
# APIs
GOOGLE_API_KEY=tu_google_api_key
NEYNAR_API_KEY=tu_neynar_api_key
CELO_RPC_URL=https://rpc.ankr.com/celo_sepolia
CELO_PRIVATE_KEY=tu_private_key

# Contratos (ya desplegados)
LOOTBOX_VAULT_ADDRESS=0xfE5aAb76ec266547418adBdF741e9D36D70AecAA
REGISTRY_ADDRESS=0x30a364AaA515494fc4dec5D6B2cA4aF81FE8FcA7
MINTER_ADDRESS=0x6C9553371f8c7e9afDE8D7385Ad986Eb5B661A5F

# MiniPay (opcional)
MINIPAY_PROJECT_ID=lootbox-agent
MINIPAY_PROJECT_SECRET=tu_secret_si_tienes

# Configuración
MINIPAY_REWARD_AMOUNT=0.15
XP_REWARD_AMOUNT=50
# ... (todas las demás variables)
```

## ✅ Checklist de Deployment

### Frontend (Vercel)
- [ ] Variables de entorno configuradas (`AGENT_SERVICE_URL`, `NEXT_PUBLIC_WC_PROJECT_ID`)
- [ ] Root Directory: `apps/web`
- [ ] Build Command configurado correctamente
- [ ] Deployment exitoso sin errores

### Backend (Railway/Render)
- [ ] Proyecto creado en Railway o Render
- [ ] Root Directory: `apps/agents`
- [ ] Todas las variables de entorno configuradas
- [ ] Servicio corriendo y accesible
- [ ] Health check: `GET https://tu-backend.railway.app/healthz` retorna `{"status":"ok"}`

### Verificación Final
- [ ] Frontend puede conectarse al backend
- [ ] El botón "Activar Recompensas" funciona
- [ ] El leaderboard carga datos
- [ ] Las recompensas se distribuyen correctamente

## 🔍 Troubleshooting

### Error: "AGENT_SERVICE_URL no configurado"
- Verifica que la variable esté configurada en Vercel
- Asegúrate de hacer un nuevo deployment después de agregar variables

### Error: "Failed to fetch" o CORS
- Verifica que la URL del backend sea correcta
- Asegúrate de que el backend esté corriendo y accesible
- Verifica que no haya problemas de CORS (el backend debería permitir requests del frontend)

### Error: Timeout en Vercel
- Si el backend está en Vercel y tarda mucho, considera moverlo a Railway/Render
- Los agentes pueden tardar 30-60 segundos en procesar

### Error: "Module not found" en build
- Verifica que `@celo/abis` esté actualizado a `^14.0.1` en `package.json`
- Ejecuta `pnpm install` localmente y commit los cambios

## 📝 Notas Importantes

1. **Backend en Vercel**: No es recomendado para este proyecto debido a los límites de tiempo
2. **Variables de Entorno**: Nunca commitees el archivo `.env` con valores reales
3. **CORS**: El backend debe permitir requests desde el dominio del frontend
4. **Health Check**: Siempre verifica que el backend esté funcionando con `/healthz`

