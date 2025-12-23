# 🧪 Guía de Pruebas: Endpoints de Generación de Casts

## 📋 Prerrequisitos

1. **Backend corriendo**: El servidor FastAPI debe estar ejecutándose
   ```bash
   cd apps/agents
   uvicorn src.main:app --reload --port 8001
   ```

2. **Variables de entorno configuradas**:
   - `GOOGLE_API_KEY` (para Gemini)
   - `CELO_PRIVATE_KEY` (para obtener dirección del agente)
   - `CELO_RPC_URL`
   - `CUSD_ADDRESS`
   - `REGISTRY_ADDRESS`

---

## 🧪 Pruebas de Endpoints

### **1. Obtener Temas Disponibles**

```bash
curl http://localhost:8001/api/casts/topics
```

**Respuesta esperada:**
```json
{
  "topics": {
    "tech": {
      "name": "Tech",
      "description": "Tecnología, blockchain, Web3, IA, innovación",
      "emoji": "💻"
    },
    "musica": { ... },
    "motivacion": { ... },
    "chistes": { ... },
    "frases_celebres": { ... }
  }
}
```

---

### **2. Obtener Dirección del Agente**

```bash
curl http://localhost:8001/api/casts/agent-address
```

**Respuesta esperada:**
```json
{
  "agent_address": "0x...",
  "message": "Envía cUSD a esta dirección para pagar por publicar casts"
}
```

---

### **3. Generar Cast (Preview)**

```bash
curl -X POST http://localhost:8001/api/casts/generate \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "tech"
  }'
```

**Con contexto del usuario:**
```bash
curl -X POST http://localhost:8001/api/casts/generate \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "tech",
    "user_address": "0x...",
    "user_fid": 12345
  }'
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

---

### **4. Publicar Cast (Requiere Pago)**

**IMPORTANTE**: Antes de publicar, el usuario debe:
1. Obtener la dirección del agente (`/api/casts/agent-address`)
2. Transferir 0.5 cUSD a esa dirección
3. Obtener el hash de la transacción

**Publicar ahora:**
```bash
curl -X POST http://localhost:8001/api/casts/publish \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "tech",
    "cast_text": "¡La tecnología blockchain está cambiando el mundo! 🌍",
    "user_address": "0x...",
    "user_fid": 12345,
    "payment_tx_hash": "0x...",
    "scheduled_time": null
  }'
```

**Programar para después:**
```bash
curl -X POST http://localhost:8001/api/casts/publish \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "tech",
    "cast_text": "¡La tecnología blockchain está cambiando el mundo! 🌍",
    "user_address": "0x...",
    "user_fid": 12345,
    "payment_tx_hash": "0x...",
    "scheduled_time": "2025-01-14T10:00:00Z"
  }'
```

**Respuesta esperada (publicar ahora):**
```json
{
  "status": "success",
  "cast_id": "uuid",
  "status": "publishing",
  "xp_granted": 100,
  "message": "Cast publicado/programado exitosamente"
}
```

**Respuesta esperada (programar):**
```json
{
  "status": "success",
  "cast_id": "uuid",
  "status": "scheduled",
  "scheduled_time": "2025-01-14T10:00:00Z",
  "xp_granted": 100,
  "message": "Cast publicado/programado exitosamente"
}
```

---

### **5. Obtener Casts Programados**

```bash
curl "http://localhost:8001/api/casts/scheduled?user_address=0x..."
```

**Respuesta esperada:**
```json
{
  "casts": [
    {
      "cast_id": "uuid",
      "user_address": "0x...",
      "user_fid": 12345,
      "topic": "tech",
      "cast_text": "...",
      "scheduled_time": "2025-01-14T10:00:00Z",
      "payment_tx_hash": "0x...",
      "status": "scheduled",
      "published_cast_hash": null,
      "xp_granted": 0,
      "created_at": "2025-01-13T15:00:00Z",
      "error_message": null
    }
  ]
}
```

---

### **6. Cancelar Cast Programado**

```bash
curl -X POST http://localhost:8001/api/casts/cancel \
  -H "Content-Type: application/json" \
  -d '{
    "cast_id": "uuid",
    "user_address": "0x..."
  }'
```

**Respuesta esperada:**
```json
{
  "status": "success",
  "message": "Cast cancelado exitosamente"
}
```

---

## 🔍 Verificación de Errores

### **Error: Pago Inválido**
```json
{
  "detail": "Pago inválido: Transacción no encontrada"
}
```

### **Error: Cantidad Incorrecta**
```json
{
  "detail": "Pago inválido: Cantidad insuficiente. Esperado: 500000000000000000, Recibido: 100000000000000000"
}
```

### **Error: Usuario Incorrecto**
```json
{
  "detail": "El pago no proviene de la dirección del usuario"
}
```

---

## 📝 Notas

1. **Precio**: 0.5 cUSD = 500000000000000000 wei (18 decimales)
2. **XP**: 100 XP se otorga cuando el cast se publica (no cuando se programa)
3. **Publicación Real**: Actualmente `publish_cast()` es un placeholder. Los casts se "publican" pero no se envían realmente a Farcaster hasta que implementemos la API de publicación.

---

## 🚀 Próximos Pasos

1. Implementar publicación real de casts en Farcaster
2. Agregar límites diarios (3 programados, 10 publicados)
3. Crear frontend para interactuar con estos endpoints

