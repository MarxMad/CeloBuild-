# 🔍 Verificación: Backend no Identificado

## ❓ ¿El Backend Está Desplegado?

### Paso 1: Verificar si Existe un Proyecto del Backend en Vercel

1. Ve a tu dashboard de Vercel: https://vercel.com/dashboard
2. Busca un proyecto llamado:
   - `lootbox-agents`
   - `lootbox-minipay-agents`
   - `celo-build-agents`
   - O cualquier proyecto relacionado con "agents" o "backend"

**Si NO encuentras ningún proyecto del backend:**
→ El backend NO está desplegado. Necesitas desplegarlo primero (ver abajo).

**Si encuentras un proyecto del backend:**
→ Copia la URL del deployment (ej: `https://lootbox-agents.vercel.app`)

### Paso 2: Probar el Health Check del Backend

Si tienes la URL del backend, prueba:

```bash
curl https://tu-backend.vercel.app/healthz
```

**Respuestas esperadas:**

✅ **Si funciona:**
```json
{"status":"ok","supervisor_initialized":true}
```

❌ **Si no funciona:**
- `404 Not Found` → El backend no está desplegado o la URL es incorrecta
- `500 Internal Server Error` → El backend está desplegado pero tiene errores
- `Connection refused` → El backend no está accesible

## 🚀 Desplegar el Backend (Si No Está Desplegado)

### Opción A: Desde el Dashboard de Vercel (Recomendado)

1. Ve a https://vercel.com/new
2. Haz clic en **"Import Git Repository"**
3. Selecciona tu repositorio `CeloBuild-`
4. En la configuración del proyecto:

   **Configuración Básica:**
   - **Project Name**: `lootbox-agents` (o el nombre que prefieras)
   - **Framework Preset**: **Other** (Vercel detectará Python automáticamente)
   - **Root Directory**: `lootbox-minipay/apps/agents` ⚠️ **MUY IMPORTANTE**
   - **Build Command**: (dejar vacío - Vercel detecta automáticamente)
   - **Output Directory**: (dejar vacío)
   - **Install Command**: (dejar vacío - Vercel detecta automáticamente)

5. Haz clic en **"Environment Variables"** y agrega TODAS estas variables:

   **Variables Requeridas:**
   ```
   GOOGLE_API_KEY=tu_google_api_key
   TAVILY_API_KEY=tu_tavily_api_key
   NEYNAR_API_KEY=tu_neynar_api_key
   CELO_RPC_URL=https://alfajores-forno.celo-testnet.org
   CELO_PRIVATE_KEY=tu_private_key
   LOOTBOX_VAULT_ADDRESS=0x3808D0C3525C4F85F1f8c9a881E3949327FB9cF7
   REGISTRY_ADDRESS=0x86C878108798e2Ce39B783127955B8F8A18ae2BE
   MINTER_ADDRESS=0x0d7370f79f77Ee701C5F40443F8C8969C28b3412
   ```

   **Variables Opcionales (pero recomendadas):**
   ```
   CUSD_ADDRESS=0x874069Fa1Eb16D44d622F2e0Ca25eeA172369bC1
   ALLOW_MANUAL_TARGET=true
   ```

6. Haz clic en **"Deploy"**

### Opción B: Desde la CLI de Vercel

```bash
# Instalar Vercel CLI si no lo tienes
npm i -g vercel

# Ir al directorio del backend
cd lootbox-minipay/apps/agents

# Iniciar deployment
vercel

# Seguir las instrucciones:
# - ¿Set up and deploy? Y
# - ¿Which scope? (selecciona tu cuenta)
# - ¿Link to existing project? N
# - ¿What's your project's name? lootbox-agents
# - ¿In which directory is your code located? ./
# - ¿Override settings? N

# Después, agregar variables de entorno:
vercel env add GOOGLE_API_KEY
vercel env add TAVILY_API_KEY
vercel env add NEYNAR_API_KEY
# ... (repetir para cada variable)
```

## ✅ Verificar que el Backend Funciona

Después del deployment:

1. **Espera a que termine el build** (puede tardar 2-5 minutos)
2. **Copia la URL del deployment** (ej: `https://lootbox-agents-abc123.vercel.app`)
3. **Prueba el health check:**
   ```bash
   curl https://tu-backend.vercel.app/healthz
   ```

   Debe retornar:
   ```json
   {"status":"ok","supervisor_initialized":true}
   ```

4. **Si retorna un error**, revisa los logs:
   - Ve a Vercel → tu proyecto del backend
   - Deployments → Logs
   - Busca errores relacionados con variables de entorno faltantes

## 🔗 Configurar el Frontend para Usar el Backend

Una vez que el backend esté funcionando:

1. Ve a tu proyecto del **frontend** en Vercel
2. **Settings** → **Environment Variables**
3. Agrega estas variables:
   ```
   NEXT_PUBLIC_AGENT_SERVICE_URL=https://tu-backend.vercel.app
   AGENT_SERVICE_URL=https://tu-backend.vercel.app
   ```
   ⚠️ **Reemplaza** `https://tu-backend.vercel.app` con la URL real de tu backend

4. **Redesplega el frontend**

## 🐛 Troubleshooting

### El backend muestra "Internal Server Error"

**Causa**: Faltan variables de entorno o hay un error en el código.

**Solución**:
1. Revisa los logs del backend en Vercel
2. Verifica que TODAS las variables de entorno estén configuradas
3. Prueba el health check para ver qué variables faltan

### El frontend no puede conectarse al backend

**Causa**: La URL del backend es incorrecta o el backend no está desplegado.

**Solución**:
1. Verifica que el backend esté desplegado
2. Verifica que la URL en `AGENT_SERVICE_URL` sea correcta
3. Prueba hacer curl al backend directamente
4. Verifica que no haya problemas de CORS

### El backend no se despliega

**Causa**: Root Directory incorrecto o dependencias faltantes.

**Solución**:
1. Verifica que **Root Directory** sea: `lootbox-minipay/apps/agents`
2. Verifica que `requirements.txt` exista y esté completo
3. Verifica que `api/index.py` exista
4. Revisa los logs de build para ver errores específicos

## 📋 Checklist Completo

### Backend
- [ ] Proyecto creado en Vercel
- [ ] Root Directory configurado: `lootbox-minipay/apps/agents`
- [ ] Framework: Other (Python)
- [ ] Variables de entorno configuradas:
  - [ ] `GOOGLE_API_KEY`
  - [ ] `TAVILY_API_KEY`
  - [ ] `NEYNAR_API_KEY`
  - [ ] `CELO_RPC_URL`
  - [ ] `CELO_PRIVATE_KEY`
  - [ ] `LOOTBOX_VAULT_ADDRESS`
  - [ ] `REGISTRY_ADDRESS`
  - [ ] `MINTER_ADDRESS`
- [ ] Deployment exitoso
- [ ] Health check funciona: `/healthz`
- [ ] URL del backend copiada

### Frontend
- [ ] Variables de entorno configuradas:
  - [ ] `NEXT_PUBLIC_AGENT_SERVICE_URL` (URL del backend)
  - [ ] `AGENT_SERVICE_URL` (URL del backend)
  - [ ] `NEXT_PUBLIC_WC_PROJECT_ID`
- [ ] Frontend redesplegado después de agregar variables
- [ ] No hay errores en los logs de runtime

## 💡 Tip: Verificar URLs

Para verificar que todo esté conectado correctamente:

1. **Backend Health Check:**
   ```bash
   curl https://tu-backend.vercel.app/healthz
   ```

2. **Frontend API Routes:**
   ```bash
   curl https://tu-frontend.vercel.app/api/leaderboard
   curl https://tu-frontend.vercel.app/api/trends
   ```

3. **Si las rutas del frontend retornan listas vacías**, es normal si no hay datos, pero NO deben retornar errores 500.

