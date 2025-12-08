# 🔍 Diagnóstico: "Internal Server Error" en Vercel

## ⚠️ El Problema

El frontend muestra "Internal Server Error" aunque el build fue exitoso. Esto significa que hay un error en **runtime**, no en el build.

## 🔎 Pasos para Diagnosticar

### Paso 1: Verificar Logs de Runtime (NO Build Logs)

1. En Vercel, ve a tu proyecto del frontend
2. Ve a **Deployments** → selecciona el último deployment
3. Haz clic en la pestaña **"Logs"** (no "Build Logs")
4. Busca errores en tiempo de ejecución

Los errores comunes son:
- `AGENT_SERVICE_URL no configurado`
- `Error conectando al backend`
- Errores de importación de módulos
- Errores de variables de entorno

### Paso 2: Verificar Variables de Entorno

1. Ve a **Settings** → **Environment Variables**
2. Verifica que estas variables estén configuradas:
   - `NEXT_PUBLIC_AGENT_SERVICE_URL` (URL del backend)
   - `AGENT_SERVICE_URL` (URL del backend)
   - `NEXT_PUBLIC_WC_PROJECT_ID` (WalletConnect)

**⚠️ IMPORTANTE**: 
- `NEXT_PUBLIC_*` variables son accesibles en el cliente
- Variables sin `NEXT_PUBLIC_` solo son accesibles en el servidor (API routes)

### Paso 3: Verificar que el Backend Esté Funcionando

1. Verifica que el backend esté desplegado en Vercel
2. Prueba el health check:
   ```bash
   curl https://tu-backend.vercel.app/healthz
   ```
3. Si el backend no responde, ese es el problema

### Paso 4: Verificar la URL del Backend

En las variables de entorno del frontend, verifica que:
- La URL del backend sea correcta
- No tenga trailing slash (`/`)
- Use `https://` (no `http://`)

## 🐛 Errores Comunes y Soluciones

### Error: "AGENT_SERVICE_URL no configurado"

**Causa**: La variable de entorno no está configurada en Vercel.

**Solución**:
1. Ve a Settings → Environment Variables
2. Agrega `NEXT_PUBLIC_AGENT_SERVICE_URL` con la URL del backend
3. Agrega `AGENT_SERVICE_URL` con la misma URL
4. Redesplega el frontend

### Error: "Error conectando al backend"

**Causa**: El backend no está desplegado o no es accesible.

**Solución**:
1. Verifica que el backend esté desplegado en Vercel
2. Prueba el health check del backend
3. Verifica que la URL en las variables de entorno sea correcta
4. Verifica que no haya problemas de CORS

### Error: "Failed to fetch" o "Network error"

**Causa**: El backend no responde o hay un problema de red.

**Solución**:
1. Verifica que el backend esté funcionando
2. Revisa los logs del backend en Vercel
3. Verifica que el backend tenga todas las variables de entorno configuradas

## 📋 Checklist de Verificación

### Frontend
- [ ] Build exitoso (verde)
- [ ] Variables de entorno configuradas:
  - [ ] `NEXT_PUBLIC_AGENT_SERVICE_URL`
  - [ ] `AGENT_SERVICE_URL`
  - [ ] `NEXT_PUBLIC_WC_PROJECT_ID`
- [ ] Logs de runtime revisados
- [ ] No hay errores en los logs de runtime

### Backend
- [ ] Backend desplegado en Vercel
- [ ] Health check funciona: `/healthz`
- [ ] Todas las variables de entorno configuradas
- [ ] Logs del backend no muestran errores críticos

## 🚀 Solución Rápida

Si el problema es que `AGENT_SERVICE_URL` no está configurada:

1. Ve a Vercel → tu proyecto del frontend
2. Settings → Environment Variables
3. Agrega:
   ```
   NEXT_PUBLIC_AGENT_SERVICE_URL=https://tu-backend.vercel.app
   AGENT_SERVICE_URL=https://tu-backend.vercel.app
   ```
4. Reemplaza `https://tu-backend.vercel.app` con la URL real de tu backend
5. Redesplega el frontend

## 💡 Tip: Ver Logs en Tiempo Real

Para ver los logs en tiempo real:

1. Ve a Vercel → tu proyecto
2. Deployments → selecciona el deployment
3. Haz clic en **"Logs"** (no "Build Logs")
4. Los logs se actualizan en tiempo real cuando hay requests

## 🔧 Debugging Avanzado

Si el problema persiste:

1. **Habilita modo debug en Next.js**:
   - Agrega `NODE_ENV=development` temporalmente
   - Esto mostrará más información en los logs

2. **Verifica que las rutas API funcionen**:
   ```bash
   curl https://tu-frontend.vercel.app/api/leaderboard
   curl https://tu-frontend.vercel.app/api/trends
   ```

3. **Revisa la consola del navegador**:
   - Abre la app en el navegador
   - Abre DevTools (F12)
   - Ve a la pestaña "Console"
   - Busca errores relacionados con el backend

