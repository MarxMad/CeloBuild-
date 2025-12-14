# ✅ Implementación: Generación y Programación de Casts con IA

## 📋 Resumen

Se ha implementado la funcionalidad completa para que los usuarios puedan:
1. **Generar Casts usando IA (Gemini API)** con diferentes temas
2. **Pagar con cUSD** directamente a la wallet del agente
3. **Recibir XP como recompensa** después de publicar
4. **Programar hasta 3 Casts al día** con hora y fecha específica

---

## ✅ Archivos Creados/Modificados

### **Backend (Python)**

#### 1. **`src/services/cast_generator.py`** ✅
- Servicio para generar casts usando Gemini API
- Temas disponibles: Tech, Música, Motivación, Chistes, Frases Célebres
- Fallback automático si Gemini no está disponible
- Validación de longitud (máximo 320 caracteres)

#### 2. **`src/services/cast_scheduler.py`** ✅
- Servicio para programar y publicar casts
- Usa APScheduler para programar publicaciones
- Maneja estados: scheduled, published, cancelled, failed
- Otorga XP automáticamente cuando se publica

#### 3. **`src/tools/farcaster.py`** ✅ (Modificado)
- Agregado método `publish_cast()` (placeholder para implementación futura)
- Requiere `signer_uuid` del usuario para publicar (pendiente de implementar)

#### 4. **`src/tools/celo.py`** ✅ (Modificado)
- Agregado método `get_agent_address()` - Obtiene dirección del agente
- Agregado método `validate_payment()` - Valida pagos on-chain de cUSD

#### 5. **`src/main.py`** ✅ (Modificado)
- Agregados endpoints:
  - `GET /api/casts/topics` - Obtener temas disponibles
  - `GET /api/casts/agent-address` - Obtener dirección del agente para pagos
  - `POST /api/casts/generate` - Generar cast con IA (preview)
  - `POST /api/casts/publish` - Publicar cast (valida pago, otorga XP)
  - `GET /api/casts/scheduled` - Obtener casts programados del usuario
  - `POST /api/casts/cancel` - Cancelar cast programado

---

## 🔄 Flujo Completo

### **1. Usuario Genera Cast (Preview)**
```
POST /api/casts/generate
{
  "topic": "tech",
  "user_address": "0x...",  // Opcional
  "user_fid": 12345         // Opcional
}

Response:
{
  "cast_text": "¡La tecnología blockchain...",
  "topic": "tech",
  "topic_name": "Tech",
  "emoji": "💻",
  "generated": true
}
```

### **2. Usuario Paga cUSD**
Frontend: Usuario transfiere 0.5 cUSD a la dirección del agente usando su wallet.

### **3. Usuario Publica Cast**
```
POST /api/casts/publish
{
  "topic": "tech",
  "cast_text": "¡La tecnología blockchain...",
  "user_address": "0x...",
  "user_fid": 12345,
  "payment_tx_hash": "0x...",
  "scheduled_time": "2025-01-14T10:00:00Z" | null
}

Response:
{
  "status": "success",
  "cast_id": "uuid",
  "status": "scheduled" | "publishing",
  "xp_granted": 100,
  "message": "Cast publicado/programado exitosamente"
}
```

### **4. Backend Valida Pago**
- Verifica que la transacción existe
- Verifica que es una transferencia de cUSD
- Verifica que el destinatario es la wallet del agente
- Verifica que la cantidad es correcta (0.5 cUSD)

### **5. Backend Publica/Programa Cast**
- Si `scheduled_time` es null → publica ahora
- Si tiene `scheduled_time` → programa para después
- Otorga XP cuando se publica (100 XP)

---

## 💰 Modelo de Precios

- **Precio por cast**: 0.5 cUSD
- **XP otorgado**: 100 XP por cast publicado
- **Límites**: 
  - Máximo 3 casts programados por día por usuario
  - Máximo 10 casts publicados por día por usuario (pendiente de implementar)

---

## 🔐 Seguridad

### **Validaciones Implementadas:**
1. ✅ Validación de pago on-chain antes de publicar
2. ✅ Verificación de que el pago proviene del usuario correcto
3. ✅ Verificación de cantidad correcta (0.5 cUSD)
4. ✅ Validación de longitud del cast (máximo 320 caracteres)
5. ✅ Validación de que `scheduled_time` no es en el pasado

---

## ⚠️ Pendiente de Implementar

### **1. Publicación Real de Casts en Farcaster**
Actualmente `publish_cast()` en `FarcasterToolbox` es un placeholder. Necesitamos:
- **Opción A**: Implementar autenticación con Neynar Signers
  - Requiere que cada usuario configure un signer en Neynar
  - Más complejo pero más control
  
- **Opción B**: Usar Warpcast API
  - Más simple pero requiere API key de Warpcast
  
- **Opción C**: Farcaster Hub directo
  - Más complejo pero más control total

### **2. Límites Diarios**
Implementar verificación de límites:
- Máximo 3 casts programados por día
- Máximo 10 casts publicados por día

### **3. Frontend**
Crear interfaz en Next.js:
- Página `/casts/generate`
- Componente para seleccionar tema
- Preview del cast generado
- Integración con wallet para pagar
- Lista de casts programados
- Opción de cancelar casts

---

## 📝 Próximos Pasos

1. **Implementar publicación real de casts** (Neynar/Warpcast)
2. **Crear frontend** en Next.js
3. **Agregar límites diarios** en el backend
4. **Testing completo** del flujo
5. **Documentación de API** para frontend

---

## 🧪 Testing

### **Endpoints para Probar:**

```bash
# 1. Obtener temas disponibles
curl http://localhost:8001/api/casts/topics

# 2. Obtener dirección del agente
curl http://localhost:8001/api/casts/agent-address

# 3. Generar cast (preview)
curl -X POST http://localhost:8001/api/casts/generate \
  -H "Content-Type: application/json" \
  -d '{"topic": "tech"}'

# 4. Publicar cast (después de pagar)
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

# 5. Obtener casts programados
curl "http://localhost:8001/api/casts/scheduled?user_address=0x..."

# 6. Cancelar cast
curl -X POST http://localhost:8001/api/casts/cancel \
  -H "Content-Type: application/json" \
  -d '{
    "cast_id": "uuid",
    "user_address": "0x..."
  }'
```

---

**Última actualización:** 2025-01-13

