# 🔧 Solución: Push no se refleja en Vercel

## 🔍 Diagnóstico

Si los pushes a GitHub no se reflejan automáticamente en Vercel, puede ser por:

1. **Vercel no está conectado al repositorio**
2. **El proyecto no está configurado para monitorear el branch correcto**
3. **El webhook de GitHub está deshabilitado o roto**
4. **El Root Directory está mal configurado**

## ✅ Solución Paso a Paso

### Paso 1: Verificar Conexión del Repositorio

1. Ve a tu proyecto en Vercel: https://vercel.com/dashboard
2. Ve a **Settings** → **Git**
3. Verifica que:
   - ✅ El repositorio esté conectado
   - ✅ El branch monitoreado sea `main` (o el que uses)
   - ✅ El webhook esté activo

### Paso 2: Verificar Root Directory

Para el **Backend** (`apps/agents`):

1. Ve a **Settings** → **General**
2. Verifica que **Root Directory** sea: `lootbox-minipay/apps/agents`
3. Si está vacío o incorrecto, cámbialo y guarda

Para el **Frontend** (`apps/web`):

1. Ve a **Settings** → **General**
2. Verifica que **Root Directory** sea: `lootbox-minipay/apps/web`
3. Si está vacío o incorrecto, cámbialo y guarda

### Paso 3: Forzar un Nuevo Deployment

Si el push no se refleja automáticamente:

#### Opción A: Desde Vercel Dashboard

1. Ve a **Deployments**
2. Haz clic en los tres puntos (⋯) del último deployment
3. Selecciona **Redeploy**
4. O haz clic en **"Redeploy"** directamente

#### Opción B: Desde la CLI

```bash
# Instalar Vercel CLI si no lo tienes
npm i -g vercel

# En el directorio del backend
cd lootbox-minipay/apps/agents
vercel --prod

# O en el directorio del frontend
cd lootbox-minipay/apps/web
vercel --prod
```

#### Opción C: Hacer un Commit Vacío

```bash
git commit --allow-empty -m "trigger vercel deployment"
git push
```

### Paso 4: Verificar Webhook de GitHub

1. Ve a tu repositorio en GitHub
2. Ve a **Settings** → **Webhooks**
3. Busca un webhook de Vercel
4. Verifica que:
   - ✅ Esté activo (green checkmark)
   - ✅ Los eventos estén configurados (push, etc.)
   - ✅ No haya errores recientes

Si no hay webhook o está roto:

1. Ve a Vercel → Settings → Git
2. Desconecta y vuelve a conectar el repositorio
3. Esto recreará el webhook

### Paso 5: Verificar Configuración del Proyecto

#### Backend (apps/agents)

En Vercel, verifica:

- **Framework Preset**: Other (Python)
- **Build Command**: (puede estar vacío, Vercel detecta automáticamente)
- **Output Directory**: (vacío)
- **Install Command**: (puede estar vacío)

**NOTA**: Para Python en Vercel, normalmente no necesitas build command. Vercel detecta automáticamente `requirements.txt` y `api/index.py`.

#### Frontend (apps/web)

En Vercel, verifica:

- **Framework Preset**: Next.js
- **Build Command**: `cd ../.. && pnpm build --filter=web`
- **Output Directory**: `.next`
- **Install Command**: `cd ../.. && pnpm install`

### Paso 6: Verificar que el Proyecto Existe

Si el backend no está desplegado:

1. Ve a https://vercel.com/new
2. Importa el repositorio `CeloBuild-`
3. Configura:
   - **Project Name**: `lootbox-agents` (o el nombre que prefieras)
   - **Root Directory**: `lootbox-minipay/apps/agents`
   - **Framework**: Other
4. Agrega todas las variables de entorno
5. Haz clic en **Deploy**

## 🐛 Troubleshooting

### El webhook no funciona

**Solución**: 
1. Desconecta el repositorio en Vercel
2. Vuelve a conectarlo
3. Esto recreará el webhook

### Vercel no detecta cambios

**Solución**:
1. Verifica que estés haciendo push al branch correcto (`main`)
2. Verifica que el Root Directory sea correcto
3. Haz un redeploy manual

### El deployment falla

**Solución**:
1. Revisa los logs en Vercel (Deployments → Logs)
2. Verifica que todas las variables de entorno estén configuradas
3. Verifica que el código compile correctamente

## 📝 Checklist Rápido

- [ ] Repositorio conectado en Vercel
- [ ] Root Directory configurado correctamente
- [ ] Webhook de GitHub activo
- [ ] Branch monitoreado es `main`
- [ ] Variables de entorno configuradas
- [ ] Último push fue al branch correcto

## 🚀 Forzar Deployment Manual

Si nada funciona, puedes forzar un deployment:

```bash
# Opción 1: Commit vacío
git commit --allow-empty -m "force vercel deploy"
git push

# Opción 2: Desde Vercel CLI
cd lootbox-minipay/apps/agents
vercel --prod

# Opción 3: Desde Vercel Dashboard
# Ve a Deployments → Redeploy
```

## 💡 Tip: Verificar Último Commit

Para verificar que Vercel ve el último commit:

1. Ve a Vercel → Deployments
2. Compara el commit SHA del último deployment con el de GitHub
3. Si no coinciden, el webhook no está funcionando

