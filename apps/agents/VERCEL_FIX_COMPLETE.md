# 🔧 Fix Completo: Backend en Vercel

## ✅ Cambios Aplicados

1. **`runtime.txt`**: Especifica Python 3.11 para Vercel
2. **`vercel.json`**: Agregado `buildCommand` para instalar dependencias
3. **`.vercelignore`**: Ignora archivos innecesarios

## 🚀 Pasos para Arreglar el Backend en Vercel

### Paso 1: Verificar Root Directory (CRÍTICO)

1. Ve a tu proyecto del **backend** en Vercel
2. **Settings → General → Root Directory**
3. Debe ser exactamente: `lootbox-minipay/apps/agents`
4. Si está vacío o incorrecto:
   - Cámbialo a: `lootbox-minipay/apps/agents`
   - **Guarda**

### Paso 2: Verificar Build Settings

1. **Settings → Build and Deployment**
2. Verifica:
   - **Framework Preset**: `Other` o `Python`
   - **Build Command**: Puede estar vacío (Vercel lo detecta automáticamente) o `pip install -r requirements.txt`
   - **Output Directory**: (vacío)
   - **Install Command**: (vacío)

### Paso 3: Verificar Git Integration

1. **Settings → Git**
2. Verifica:
   - **Repository**: `MarxMad/CeloBuild-`
   - **Production Branch**: `main`
   - **Webhook**: Debe estar activo

Si el webhook no funciona:
- Desconecta el repositorio
- Reconecta el repositorio
- Selecciona branch `main`

### Paso 4: Forzar Nuevo Deployment

**Opción A: Desde Vercel Dashboard**
1. Ve a **Deployments**
2. Haz clic en los tres puntos (⋯) del último deployment
3. Selecciona **"Redeploy"**

**Opción B: Commit Vacío**
```bash
git commit --allow-empty -m "trigger backend redeploy"
git push
```

**Opción C: Cambiar Root Directory**
1. Si el Root Directory estaba incorrecto, al cambiarlo y guardar, Vercel automáticamente creará un nuevo deployment

### Paso 5: Verificar que Funciona

1. **Espera 2-3 minutos** después del deployment
2. Prueba el health check:
   ```bash
   curl https://tu-backend.vercel.app/healthz
   ```
3. Debe retornar:
   ```json
   {"status":"ok","supervisor_initialized":true}
   ```

## 🔍 Verificar el Último Deployment

1. Ve a **Deployments**
2. El último deployment debe tener:
   - **Status**: "Ready" (verde)
   - **Commit SHA**: Debe coincidir con tu último push
   - **Source**: `main` branch

Si el commit SHA no coincide:
- El webhook no está funcionando
- Sigue el Paso 3 para reconectar el repositorio

## 🐛 Troubleshooting

### El deployment no aparece

**Causa**: Root Directory incorrecto o webhook roto

**Solución**:
1. Verifica Root Directory (Paso 1)
2. Reconecta el repositorio (Paso 3)
3. Haz un commit vacío y push

### El deployment falla

**Revisa Build Logs**:
1. Ve a Deployments → Selecciona el deployment fallido
2. Revisa los **Build Logs**
3. Busca errores de:
   - Variables de entorno faltantes
   - Errores de importación
   - Errores de dependencias

### Health check retorna error

**Revisa Runtime Logs**:
1. Ve a Deployments → Selecciona el último deployment
2. Revisa los **Logs** (no Build Logs)
3. Busca errores de inicialización

**Prueba el health check detallado**:
```bash
curl https://tu-backend.vercel.app/healthz
```

Si retorna `{"status":"error",...}`, revisa qué error específico muestra.

## ✅ Checklist Final

- [ ] Root Directory: `lootbox-minipay/apps/agents`
- [ ] Framework Preset: `Other` o `Python`
- [ ] Repositorio conectado: `MarxMad/CeloBuild-`
- [ ] Branch: `main`
- [ ] Webhook activo
- [ ] Último deployment tiene el commit SHA correcto
- [ ] Health check funciona: `/healthz` retorna `{"status":"ok"}`

## 📝 Notas Importantes

- **Root Directory es el problema más común**: Si está vacío, Vercel no sabe dónde está el código
- **Los cambios en `vercel.json` y `runtime.txt`** ayudan a Vercel a detectar correctamente el proyecto Python
- **Después de cambiar Root Directory**, Vercel automáticamente crea un nuevo deployment
- **Espera 2-3 minutos** después de un push para que Vercel procese el deployment

