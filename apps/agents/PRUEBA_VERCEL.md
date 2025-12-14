# 🧪 Probar Endpoints de Casts en Vercel

## 🚀 Pruebas Rápidas

### **1. Health Check (Verificar que el backend está vivo)**

```bash
curl https://celo-build-backend-agents.vercel.app/healthz
```

**Respuesta esperada:**
```json
{"status":"ok","supervisor_initialized":true}
```

---

### **2. Obtener Temas Disponibles**

```bash
curl https://celo-build-backend-agents.vercel.app/api/casts/topics
```

**Respuesta esperada:**
```json
{
  "topics": {
    "tech": {"name": "Tech", "description": "...", "emoji": "💻"},
    "musica": {...},
    "motivacion": {...},
    "chistes": {...},
    "frases_celebres": {...}
  }
}
```

---

### **3. Obtener Dirección del Agente (Para Pagos)**

```bash
curl https://celo-build-backend-agents.vercel.app/api/casts/agent-address
```

**Respuesta esperada:**
```json
{
  "agent_address": "0x...",
  "message": "Envía cUSD a esta dirección para pagar por publicar casts"
}
```

---

### **4. Generar Cast con IA (Preview)**

```bash
curl -X POST https://celo-build-backend-agents.vercel.app/api/casts/generate \
  -H "Content-Type: application/json" \
  -d '{"topic":"tech"}'
```

**Respuesta esperada:**
```json
{
  "cast_text": "¡La tecnología blockchain está cambiando el mundo! 🌍 ¿Cuál es tu proyecto Web3 favorito?",
  "topic": "tech",
  "topic_name": "Tech",
  "emoji": "💻",
  "generated": true
}
```

**Probar otros temas:**
```bash
# Motivación
curl -X POST https://celo-build-backend-agents.vercel.app/api/casts/generate \
  -H "Content-Type: application/json" \
  -d '{"topic":"motivacion"}'

# Música
curl -X POST https://celo-build-backend-agents.vercel.app/api/casts/generate \
  -H "Content-Type: application/json" \
  -d '{"topic":"musica"}'

# Chistes
curl -X POST https://celo-build-backend-agents.vercel.app/api/casts/generate \
  -H "Content-Type: application/json" \
  -d '{"topic":"chistes"}'

# Frases Célebres
curl -X POST https://celo-build-backend-agents.vercel.app/api/casts/generate \
  -H "Content-Type: application/json" \
  -d '{"topic":"frases_celebres"}'
```

---

## 📝 Script Automático

Si prefieres usar el script automático:

```bash
cd lootbox-minipay/apps/agents

# Ejecutar script de pruebas
./test_vercel_endpoints.sh

# O con URL personalizada
BACKEND_URL="https://tu-backend.vercel.app" ./test_vercel_endpoints.sh
```

---

## ⚠️ Si los Endpoints No Existen

Si obtienes **404 Not Found**, significa que:

1. **El código no se ha desplegado aún**
   - Verifica que hayas hecho `git push`
   - Ve a Vercel → Deployments y verifica que haya un deployment reciente

2. **Necesitas hacer Redeploy**
   - Ve a Vercel → Tu proyecto → Deployments
   - Haz clic en "..." → "Redeploy"

3. **Hay un error en el deployment**
   - Ve a Vercel → Deployments → Logs
   - Revisa los errores y corrígelos

---

## 🔍 Verificar Logs en Vercel

1. Ve a https://vercel.com/dashboard
2. Selecciona tu proyecto del backend
3. Ve a **Deployments**
4. Haz clic en el último deployment
5. Ve a **Logs** para ver errores

---

## ✅ Checklist de Pruebas

- [ ] Health check funciona (`/healthz`)
- [ ] Endpoint de temas funciona (`/api/casts/topics`)
- [ ] Endpoint de dirección del agente funciona (`/api/casts/agent-address`)
- [ ] Generación de casts funciona (`/api/casts/generate`)
- [ ] Probar todos los temas (tech, musica, motivacion, chistes, frases_celebres)

---

## 🚀 Próximos Pasos

Una vez que estos endpoints funcionen:

1. **Probar publicación** (requiere pago real de 0.5 cUSD)
2. **Probar programación** de casts
3. **Crear frontend** para interactuar con estos endpoints

---

**Nota**: Reemplaza `https://celo-build-backend-agents.vercel.app` con la URL real de tu backend en Vercel si es diferente.

