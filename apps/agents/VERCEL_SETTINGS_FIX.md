# 🔧 Corrección de Configuración en Vercel

## ❌ Problemas Detectados

1. **Root Directory**: `apps/agents` ❌
   - **Debe ser**: `lootbox-minipay/apps/agents` ✅

2. **Build Command**: `cd ../.. && pnpm build --filter=web` ❌
   - **Debe ser**: (vacío) o `pip install -r requirements.txt` ✅

3. **Install Command**: `cd ../.. && pnpm install` ❌
   - **Debe ser**: (vacío) o `pip install -r requirements.txt` ✅

4. **Framework Preset**: "FastAPI" ✅ (esto está bien)

## ✅ Pasos para Corregir

### Paso 1: Cambiar Root Directory

1. En la sección **"Root Directory"**
2. Cambia de: `apps/agents`
3. A: `lootbox-minipay/apps/agents`
4. **Guarda** (esto activará un nuevo deployment)

### Paso 2: Corregir Build Command

1. En la sección **"Framework Settings"**
2. Busca **"Build Command"**
3. Haz clic en el toggle **"Override"** para activarlo (si no está activo)
4. Cambia el comando de: `cd ../.. && pnpm build --filter=web`
5. A: (dejar vacío) o `pip install -r requirements.txt`
6. **Guarda**

### Paso 3: Corregir Install Command

1. En la misma sección **"Framework Settings"**
2. Busca **"Install Command"**
3. Haz clic en el toggle **"Override"** para activarlo (si no está activo)
4. Cambia el comando de: `cd ../.. && pnpm install`
5. A: (dejar vacío) o `pip install -r requirements.txt`
6. **Guarda**

### Paso 4: Verificar Output Directory

1. **Output Directory** debe estar vacío o mostrar "N/A"
2. El toggle "Override" puede estar OFF (está bien)

### Paso 5: Esperar el Nuevo Deployment

1. Después de guardar los cambios, Vercel creará un nuevo deployment automáticamente
2. Espera 2-3 minutos
3. Ve a **Deployments** y verifica que aparezca un nuevo deployment

### Paso 6: Verificar que Funciona

1. Espera a que el deployment termine (Status: "Ready")
2. Prueba el health check:
   ```bash
   curl https://tu-backend.vercel.app/healthz
   ```
3. Debe retornar:
   ```json
   {"status":"ok","supervisor_initialized":true}
   ```
   O si hay problemas:
   ```json
   {"status":"degraded","supervisor_initialized":false,"missing_env_vars":[...]}
   ```

## 📋 Configuración Correcta Final

**Root Directory:**
```
lootbox-minipay/apps/agents
```

**Framework Preset:**
```
FastAPI
```

**Build Command:**
```
(vacío) o pip install -r requirements.txt
```

**Install Command:**
```
(vacío) o pip install -r requirements.txt
```

**Output Directory:**
```
(vacío) o N/A
```

## ⚠️ Nota Importante

Los comandos `pnpm` son para Node.js/JavaScript. El backend es Python, así que esos comandos están causando que el deployment falle o no funcione correctamente.

## 🔍 Si Aún Hay Problemas

1. Prueba el endpoint de debug:
   ```bash
   curl https://tu-backend.vercel.app/debug
   ```

2. Revisa los **Build Logs** en Vercel:
   - Deployments → Selecciona el último deployment
   - Revisa los Build Logs para ver errores

3. Revisa los **Runtime Logs**:
   - Deployments → Selecciona el último deployment
   - Revisa los Logs (no Build Logs) para ver errores en tiempo de ejecución

