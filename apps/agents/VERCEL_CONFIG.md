# ⚙️ Configuración del Backend en Vercel

## 🔧 Configuración Requerida en Vercel Dashboard

### 1. Root Directory (CRÍTICO)

**Settings → General → Root Directory:**
```
lootbox-minipay/apps/agents
```

⚠️ **Si está vacío o incorrecto, los deployments NO funcionarán.**

### 2. Build Settings

**Settings → General → Build & Development Settings:**

- **Framework Preset**: `Other` o `Python`
- **Build Command**: (dejar vacío o `pip install -r requirements.txt`)
- **Output Directory**: (dejar vacío)
- **Install Command**: (dejar vacío)

### 3. Git Integration

**Settings → Git:**

- **Repository**: `MarxMad/CeloBuild-`
- **Production Branch**: `main`
- **Webhook Status**: Debe estar activo

Si el webhook no está activo:
1. Desconecta el repositorio
2. Reconecta el repositorio
3. Verifica que el branch sea `main`

### 4. Environment Variables

**Settings → Environment Variables:**

Todas las variables de `env.sample` deben estar configuradas.

Variables críticas:
- `GOOGLE_API_KEY`
- `TAVILY_API_KEY`
- `NEYNAR_API_KEY`
- `CELO_RPC_URL`
- `CELO_PRIVATE_KEY`
- `LOOTBOX_VAULT_ADDRESS`
- `REGISTRY_ADDRESS`
- `MINTER_ADDRESS`

## 🔄 Forzar Actualización

Si los pushes no se reflejan:

### Opción 1: Verificar y Corregir Root Directory

1. Ve a **Settings → General**
2. Verifica que **Root Directory** sea: `lootbox-minipay/apps/agents`
3. Si está vacío o incorrecto:
   - Cámbialo a: `lootbox-minipay/apps/agents`
   - Guarda
   - Esto activará un nuevo deployment automáticamente

### Opción 2: Redeploy Manual

1. Ve a **Deployments**
2. Haz clic en los tres puntos (⋯) del último deployment
3. Selecciona **"Redeploy"**

### Opción 3: Reconectar Repositorio

1. Ve a **Settings → Git**
2. Haz clic en **"Disconnect"**
3. Vuelve a conectar el repositorio
4. Selecciona el branch `main`
5. Esto recreará el webhook

## ✅ Verificación Post-Configuración

1. **Verifica el último deployment:**
   - Deployments → Compara el commit SHA con tu último push
   - Debe coincidir

2. **Prueba el health check:**
   ```bash
   curl https://tu-backend.vercel.app/healthz
   ```
   Debe retornar: `{"status":"ok","supervisor_initialized":true}`

3. **Verifica que el deployment se actualiza:**
   - Haz un push nuevo
   - Espera 1-2 minutos
   - Verifica que aparezca un nuevo deployment en Vercel

## 🐛 Troubleshooting

### El deployment no se actualiza con los pushes

**Causa más común**: Root Directory incorrecto o vacío

**Solución**:
1. Ve a Settings → General
2. Verifica Root Directory: `lootbox-minipay/apps/agents`
3. Si está vacío, cámbialo y guarda

### El webhook no funciona

**Solución**:
1. Ve a Settings → Git
2. Desconecta y reconecta el repositorio
3. Verifica que el branch sea `main`

### El deployment falla

**Revisa los Build Logs:**
1. Ve a Deployments → Selecciona el deployment fallido
2. Revisa los Build Logs
3. Busca errores de:
   - Variables de entorno faltantes
   - Errores de importación
   - Errores de dependencias

