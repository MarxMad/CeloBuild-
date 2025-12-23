# 🧪 Probar Endpoints en Vercel

## 🚀 Pruebas Rápidas

### **Opción 1: Script Automático**

```bash
cd lootbox-minipay/apps/agents

# Usar URL por defecto (celo-build-backend-agents.vercel.app)
./test_vercel_endpoints.sh

# O especificar tu URL personalizada
BACKEND_URL="https://tu-backend.vercel.app" ./test_vercel_endpoints.sh
```

### **Opción 2: Comandos Manuales**

Reemplaza `https://celo-build-backend-agents.vercel.app` con tu URL real del backend en Vercel.

#### **1. Health Check**
```bash
curl https://celo-build-backend-agents.vercel.app/healthz
```

#### **2. Obtener Temas Disponibles**
```bash
curl https://celo-build-backend-agents.vercel.app/api/casts/topics
```

#### **3. Obtener Dirección del Agente**
```bash
curl https://celo-build-backend-agents.vercel.app/api/casts/agent-address
```

#### **4. Generar Cast (Preview)**
```bash
curl -X POST https://celo-build-backend-agents.vercel.app/api/casts/generate \
  -H "Content-Type: application/json" \
  -d '{"topic":"tech"}'
```

#### **5. Generar Cast con Otro Tema**
```bash
curl -X POST https://celo-build-backend-agents.vercel.app/api/casts/generate \
  -H "Content-Type: application/json" \
  -d '{"topic":"motivacion"}'
```

---

## 🔍 Verificar que el Backend Está Desplegado

### **1. Verificar Health Check**
```bash
curl https://celo-build-backend-agents.vercel.app/healthz
```

**Respuesta esperada:**
```json
{
  "status": "ok",
  "supervisor_initialized": true
}
```

### **2. Verificar que los Nuevos Endpoints Existen**

Si los endpoints no existen, puede ser que:
- El código no se haya desplegado aún
- Hay un error en el deployment
- Necesitas hacer un redeploy

**Solución:**
1. Ve a Vercel → Tu proyecto → Deployments
2. Verifica que el último deployment sea exitoso
3. Si hay errores, revisa los logs
4. Si todo está bien pero los endpoints no aparecen, haz un **Redeploy**

---

## ⚠️ Errores Comunes

### **Error 404: Not Found**
- Los endpoints no están desplegados
- **Solución**: Verifica que el código esté en el repositorio y haz redeploy

### **Error 500: Internal Server Error**
- Hay un error en el código del backend
- **Solución**: Revisa los logs en Vercel (Deployments → Logs)

### **Error: Module not found**
- Faltan dependencias en `requirements.txt`
- **Solución**: Verifica que todas las dependencias estén en `requirements.txt`

### **Error: Settings not configured**
- Faltan variables de entorno
- **Solución**: Verifica que todas las variables estén configuradas en Vercel

---

## 📝 Próximos Pasos

Una vez que los endpoints básicos funcionen:

1. **Probar generación de casts** con diferentes temas
2. **Obtener dirección del agente** para pagos
3. **Probar publicación** (requiere pago real de cUSD)
4. **Probar programación** de casts

---

## 🔗 URLs Útiles

- **Vercel Dashboard**: https://vercel.com/dashboard
- **Logs del Backend**: Vercel → Tu proyecto → Deployments → Logs
- **Variables de Entorno**: Vercel → Tu proyecto → Settings → Environment Variables

