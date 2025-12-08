# 🚀 Configuración de Vercel - Guía Completa

## ⚠️ Problema: "Internal Server Error"

Si ves "Internal Server Error" en el frontend, es porque:

1. **El backend no está desplegado en Vercel**, o
2. **La variable `AGENT_SERVICE_URL` no está configurada** en el proyecto del frontend

## 📋 Pasos para Solucionar

### Paso 1: Verificar que el Backend esté Desplegado

1. Ve a tu dashboard de Vercel: https://vercel.com/dashboard
2. Busca un proyecto llamado `lootbox-minipay-agents` o similar
3. Si NO existe, necesitas desplegar el backend primero (ver Paso 2)
4. Si existe, copia la URL del deployment (ej: `https://lootbox-agents.vercel.app`)

### Paso 2: Desplegar el Backend (si no está desplegado)

#### Opción A: Desde el Dashboard de Vercel

1. Ve a https://vercel.com/new
2. Conecta tu repositorio `CeloBuild-`
3. En "Root Directory", selecciona `lootbox-minipay/apps/agents`
4. Configura:
   - **Framework Preset**: Other
   - **Build Command**: `pip install -r requirements.txt && pip install -e .`
   - **Output Directory**: (dejar vacío)
   - **Install Command**: `pip install -r requirements.txt && pip install -e .`
5. Agrega todas las variables de entorno desde `apps/agents/env.sample`
6. Haz clic en "Deploy"

#### Opción B: Desde la CLI

```bash
cd lootbox-minipay/apps/agents
vercel
# Sigue las instrucciones y configura las variables de entorno
```

### Paso 3: Configurar Variables de Entorno en el Frontend

1. Ve a tu proyecto del frontend en Vercel
2. Ve a **Settings** → **Environment Variables**
3. Agrega estas variables:

```
NEXT_PUBLIC_AGENT_SERVICE_URL=https://tu-backend.vercel.app
AGENT_SERVICE_URL=https://tu-backend.vercel.app
```

**⚠️ IMPORTANTE**: Reemplaza `https://tu-backend.vercel.app` con la URL real de tu backend desplegado.

### Paso 4: Verificar que el Backend Funciona

Abre en tu navegador o usa curl:

```bash
# Health check
curl https://tu-backend.vercel.app/healthz

# Debe retornar: {"status":"ok"}
```

Si retorna un error, revisa los logs del backend en Vercel.

### Paso 5: Redesplegar el Frontend

Después de agregar las variables de entorno:

1. Ve a tu proyecto del frontend en Vercel
2. Ve a **Deployments**
3. Haz clic en los tres puntos (⋯) del último deployment
4. Selecciona **Redeploy**

O simplemente haz un push nuevo al repositorio:

```bash
git commit --allow-empty -m "trigger redeploy"
git push
```

## 🔍 Verificar que Todo Funciona

### 1. Verificar Backend

```bash
# Health check
curl https://tu-backend.vercel.app/healthz

# Leaderboard
curl https://tu-backend.vercel.app/api/lootbox/leaderboard?limit=5

# Trends
curl https://tu-backend.vercel.app/api/lootbox/trends?limit=5
```

### 2. Verificar Frontend

1. Abre tu frontend en Vercel
2. Abre la consola del navegador (F12)
3. Busca errores relacionados con `AGENT_SERVICE_URL`
4. Verifica que las peticiones al backend se hagan correctamente

### 3. Verificar Variables de Entorno

En el frontend, puedes verificar temporalmente en la consola:

```javascript
console.log('AGENT_SERVICE_URL:', process.env.AGENT_SERVICE_URL);
console.log('NEXT_PUBLIC_AGENT_SERVICE_URL:', process.env.NEXT_PUBLIC_AGENT_SERVICE_URL);
```

**Nota**: Esto solo funciona en el servidor (no en el cliente). Para verificar en el cliente, usa `NEXT_PUBLIC_AGENT_SERVICE_URL`.

## 📝 Checklist de Configuración

### Backend (apps/agents)

- [ ] Proyecto desplegado en Vercel
- [ ] URL del backend copiada
- [ ] Variables de entorno configuradas:
  - [ ] `GOOGLE_API_KEY`
  - [ ] `TAVILY_API_KEY`
  - [ ] `NEYNAR_API_KEY`
  - [ ] `CELO_RPC_URL`
  - [ ] `CELO_PRIVATE_KEY`
  - [ ] `LOOTBOX_VAULT_ADDRESS`
  - [ ] `REGISTRY_ADDRESS`
  - [ ] `MINTER_ADDRESS`
  - [ ] Todas las demás de `env.sample`
- [ ] Health check funciona: `/healthz`
- [ ] API endpoints responden correctamente

### Frontend (apps/web)

- [ ] Proyecto desplegado en Vercel
- [ ] Variables de entorno configuradas:
  - [ ] `NEXT_PUBLIC_AGENT_SERVICE_URL` (URL del backend)
  - [ ] `AGENT_SERVICE_URL` (URL del backend)
  - [ ] `NEXT_PUBLIC_WC_PROJECT_ID` (WalletConnect)
- [ ] Frontend redesplegado después de agregar variables
- [ ] No hay errores en la consola del navegador
- [ ] Las peticiones al backend funcionan

## 🐛 Troubleshooting

### Error: "Backend no configurado"

**Causa**: `AGENT_SERVICE_URL` no está configurada en Vercel.

**Solución**: 
1. Ve a Settings → Environment Variables
2. Agrega `NEXT_PUBLIC_AGENT_SERVICE_URL` y `AGENT_SERVICE_URL`
3. Redesplega el frontend

### Error: "Failed to fetch" o "Network error"

**Causa**: El backend no está desplegado o no es accesible.

**Solución**:
1. Verifica que el backend esté desplegado
2. Verifica la URL del backend en las variables de entorno
3. Prueba hacer curl al backend directamente
4. Revisa los logs del backend en Vercel

### Error: "CORS error"

**Causa**: El backend no permite peticiones desde el dominio del frontend.

**Solución**: 
El backend ya tiene CORS configurado para permitir todos los orígenes. Si persiste, verifica los logs del backend.

### Backend retorna 500

**Causa**: Variables de entorno faltantes o incorrectas en el backend.

**Solución**:
1. Revisa los logs del backend en Vercel
2. Verifica que todas las variables de `env.sample` estén configuradas
3. Verifica que los valores sean correctos (sin espacios, sin comillas extra)

## 📞 Soporte

Si después de seguir estos pasos aún tienes problemas:

1. Revisa los logs en Vercel (Deployments → Logs)
2. Verifica que ambos proyectos (frontend y backend) estén desplegados
3. Verifica que las URLs sean correctas y accesibles
4. Revisa la consola del navegador para errores específicos

