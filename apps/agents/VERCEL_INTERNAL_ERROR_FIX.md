# 🔧 Fix: Internal Server Error en Vercel

## 🚨 El Problema

El backend muestra "Internal Server Error" en Vercel. Esto puede ser por:
1. Variables de entorno faltantes
2. Errores en la inicialización
3. Root Directory incorrecto
4. Dependencias no instaladas

## 🔍 Paso 1: Diagnosticar el Error

### Opción A: Usar el Endpoint de Debug

Después de que se despliegue el nuevo código, prueba:

```bash
curl https://tu-backend.vercel.app/debug
```

Esto te mostrará:
- Qué error específico está ocurriendo
- Qué variables de entorno faltan
- El path de Python
- Información de debugging

### Opción B: Ver Logs en Vercel

1. Ve a tu proyecto del backend en Vercel
2. **Deployments** → Selecciona el último deployment
3. Haz clic en **"Logs"** (no Build Logs)
4. Busca errores de:
   - Importación de módulos
   - Variables de entorno faltantes
   - Errores de inicialización

### Opción C: Health Check Detallado

```bash
curl https://tu-backend.vercel.app/healthz
```

Si retorna un error, verás qué variables faltan.

## ✅ Paso 2: Verificar Root Directory (CRÍTICO)

1. Ve a tu proyecto del **backend** en Vercel
2. **Settings → General → Root Directory**
3. Debe ser exactamente: `lootbox-minipay/apps/agents`
4. Si está vacío o incorrecto:
   - Cámbialo a: `lootbox-minipay/apps/agents`
   - **Guarda**
   - Esto activará un nuevo deployment

## ✅ Paso 3: Verificar Variables de Entorno

1. **Settings → Environment Variables**
2. Verifica que estas variables estén configuradas:

**Variables CRÍTICAS (requeridas):**
- `GOOGLE_API_KEY`
- `TAVILY_API_KEY`
- `CELO_RPC_URL`
- `CELO_PRIVATE_KEY`
- `LOOTBOX_VAULT_ADDRESS`
- `REGISTRY_ADDRESS`
- `MINTER_ADDRESS`

**Variables OPCIONALES (pero recomendadas):**
- `NEYNAR_API_KEY`
- `MINIPAY_PROJECT_SECRET`
- `CUSD_ADDRESS`

3. Si falta alguna variable crítica:
   - Agrégalas
   - **Redesplega** el backend

## ✅ Paso 4: Verificar Build Settings

1. **Settings → Build and Deployment**
2. Verifica:
   - **Framework Preset**: `Other` o `Python`
   - **Build Command**: (puede estar vacío) o `pip install -r requirements.txt`
   - **Output Directory**: (vacío)
   - **Install Command**: (vacío)

## ✅ Paso 5: Forzar Nuevo Deployment

Después de hacer cambios:

### Opción A: Desde Vercel Dashboard
1. Ve a **Deployments**
2. Haz clic en los tres puntos (⋯) del último deployment
3. Selecciona **"Redeploy"**

### Opción B: Cambiar Root Directory
1. Si cambiaste el Root Directory, al guardar se crea un nuevo deployment automáticamente

### Opción C: Commit Vacío
```bash
git commit --allow-empty -m "trigger redeploy"
git push
```

## 🔍 Paso 6: Verificar que Funciona

1. **Espera 2-3 minutos** después del deployment
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

4. Si aún hay error, prueba el debug:
   ```bash
   curl https://tu-backend.vercel.app/debug
   ```

## 🐛 Troubleshooting Específico

### Error: "ModuleNotFoundError"

**Causa**: Dependencias no instaladas

**Solución**:
1. Verifica que `requirements.txt` esté en el repositorio
2. Verifica Build Logs en Vercel
3. Si hay errores de instalación, agrega `buildCommand` en `vercel.json`

### Error: "ValidationError" en Settings

**Causa**: Variables de entorno faltantes

**Solución**:
1. Usa `/debug` para ver qué variables faltan
2. Agrega las variables faltantes en Vercel
3. Redesplega

### Error: "Internal Server Error" sin detalles

**Causa**: Error en la inicialización

**Solución**:
1. Ve a **Logs** en Vercel (no Build Logs)
2. Busca el error específico
3. El nuevo código ahora muestra errores detallados en `/debug`

### El deployment no aparece

**Causa**: Root Directory incorrecto o webhook roto

**Solución**:
1. Verifica Root Directory (Paso 2)
2. **Settings → Git** → Reconecta el repositorio
3. Verifica que el branch sea `main`

## ✅ Checklist Completo

- [ ] Root Directory: `lootbox-minipay/apps/agents`
- [ ] Framework Preset: `Other` o `Python`
- [ ] Variables de entorno críticas configuradas
- [ ] Último deployment tiene el commit SHA correcto (`6ae3e37`)
- [ ] Health check funciona: `/healthz` retorna respuesta (aunque sea "degraded")
- [ ] Debug endpoint funciona: `/debug` muestra información

## 📝 Notas Importantes

- **El nuevo código** ahora siempre inicializa la app, incluso con errores
- **El health check** siempre funciona para diagnosticar problemas
- **El endpoint `/debug`** muestra información detallada sobre qué está fallando
- **Los logs en Vercel** son la mejor fuente de información sobre errores

## 🚀 Próximos Pasos

1. Verifica Root Directory
2. Verifica variables de entorno
3. Redesplega
4. Prueba `/healthz` y `/debug`
5. Revisa los logs en Vercel si aún hay problemas

