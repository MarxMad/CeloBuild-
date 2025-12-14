# 🎯 Plan de Implementación: Generación y Programación de Casts con IA

## 📋 Resumen de la Funcionalidad

Permitir a los usuarios:
1. **Generar Casts usando IA (Gemini API)** con diferentes temas
2. **Pagar con cUSD** para publicar el cast
3. **Recibir XP como recompensa** después de publicar
4. **Programar hasta 3 Casts al día** con hora y fecha específica
5. **Temas disponibles**: Tech, Música, Motivación, Chistes, Frases Célebres

---

## 🔍 Análisis de Contratos Desplegados

### Contratos Actuales:

#### 1. **LootBoxVault** (`0x4f7aa310c1f90e435f292f5d9ba07cb102409990`)
- ✅ `fundCampaign()`: Solo el owner puede depositar fondos
- ❌ **NO tiene función `payable` para recibir pagos de usuarios**
- ✅ `distributeERC20()`: Solo agents pueden distribuir recompensas

#### 2. **LootAccessRegistry** (`0x28a499be43d2e9720e129725e052781746e59d1d`)
- ✅ `grantXp()`: Solo reporters pueden otorgar XP
- ❌ **NO recibe pagos de usuarios**

#### 3. **LootBoxMinter** (`0x39b93bac43ed50df42ea9e0dde38bcd072f0a771`)
- ✅ `mintBatch()`: Solo agents pueden mintear NFTs
- ❌ **NO recibe pagos de usuarios**

### ⚠️ Conclusión:

**Los contratos actuales NO tienen funciones para recibir pagos directamente de usuarios.**

---

## 💡 Soluciones Propuestas

### **Opción 1: Pagos Off-Chain + XP On-Chain** (Recomendada)

**Ventajas:**
- ✅ No requiere modificar contratos desplegados
- ✅ Más rápido y barato (menos gas)
- ✅ Mejor UX (transacciones instantáneas)
- ✅ Podemos usar el contrato `LootAccessRegistry.grantXp()` que ya existe

**Flujo:**
1. Usuario paga cUSD directamente al backend (wallet del agente) vía transferencia ERC20
2. Backend valida el pago
3. Backend genera el cast con IA
4. Backend publica el cast en Farcaster (si está programado, lo guarda)
5. Backend otorga XP on-chain usando `LootAccessRegistry.grantXp()`

**Implementación:**
```typescript
// Frontend: Transferir cUSD al backend
const cusdContract = new ethers.Contract(CUSD_ADDRESS, ERC20_ABI, signer);
await cusdContract.transfer(BACKEND_WALLET_ADDRESS, amount);

// Backend: Validar pago y otorgar XP
await celo_tool.grant_xp(
    registry_address=REGISTRY_ADDRESS,
    campaign_id="cast-generation",
    participant=user_address,
    amount=100  // XP por publicar
)
```

---

### **Opción 2: Nuevo Contrato Simple para Pagos** (Más complejo)

Crear un nuevo contrato `CastPaymentVault` que:
- Recibe pagos de usuarios (`payable` o `transferFrom` de cUSD)
- Emite eventos cuando se recibe un pago
- El backend escucha eventos y procesa

**Desventajas:**
- Requiere deployment de nuevo contrato
- Más gas para usuarios
- Más complejidad

---

## 🏗️ Arquitectura Propuesta (Opción 1)

### **Backend (Python/FastAPI)**

#### 1. **Nuevo Endpoint: `/api/casts/generate`**
```python
POST /api/casts/generate
{
    "topic": "tech" | "musica" | "motivacion" | "chistes" | "frases_celebres",
    "user_address": "0x...",
    "fid": 12345,
    "scheduled_time": "2025-01-14T10:00:00Z" | null,  # null = publicar ahora
    "payment_tx_hash": "0x..."  # Hash de la transacción de pago
}
```

#### 2. **Nuevo Servicio: `CastGeneratorService`**
```python
class CastGeneratorService:
    def __init__(self, gemini_api_key: str):
        self.llm = ChatGoogleGenerativeAI(model="gemini-pro", ...)
    
    async def generate_cast(self, topic: str) -> str:
        """Genera un cast usando Gemini basado en el tema."""
        prompt = f"""
        Genera un cast para Farcaster sobre el tema: {topic}
        - Máximo 280 caracteres
        - Debe ser engaging y auténtico
        - Incluye emojis relevantes
        - No uses hashtags a menos que sea necesario
        """
        # ... generar con Gemini
```

#### 3. **Nuevo Servicio: `CastSchedulerService`**
```python
class CastSchedulerService:
    """Maneja la programación de casts usando APScheduler."""
    
    def schedule_cast(
        self,
        cast_text: str,
        user_fid: int,
        scheduled_time: datetime,
        cast_id: str
    ):
        """Programa un cast para publicarse en el futuro."""
        # Usar APScheduler para programar
        scheduler.add_job(
            self._publish_scheduled_cast,
            'date',
            run_date=scheduled_time,
            args=[cast_text, user_fid, cast_id]
        )
```

#### 4. **Nuevo Método en `FarcasterToolbox`: `publish_cast`**
```python
async def publish_cast(
    self,
    user_fid: int,
    cast_text: str,
    parent_hash: str | None = None
) -> dict[str, Any]:
    """Publica un cast en Farcaster usando Neynar API.
    
    Requiere:
    - NEYNAR_SIGNER_UUID: UUID del signer del usuario
    - O usar Warpcast API si está disponible
    """
    # Verificar documentación de Neynar para publicar casts
    # Endpoint: POST /v2/farcaster/cast
    # Requiere: signer_uuid del usuario
```

#### 5. **Nuevo Endpoint: `/api/casts/scheduled`**
```python
GET /api/casts/scheduled?user_address=0x...
# Retorna lista de casts programados del usuario
```

#### 6. **Nuevo Endpoint: `/api/casts/cancel`**
```python
POST /api/casts/cancel
{
    "cast_id": "uuid",
    "user_address": "0x..."
}
# Cancela un cast programado
```

---

### **Frontend (Next.js/React)**

#### 1. **Nueva Página: `/casts/generate`**
- Formulario para seleccionar tema
- Preview del cast generado
- Opción de programar (fecha/hora)
- Botón de pago (cUSD)

#### 2. **Componente: `CastGenerator`**
```typescript
interface CastGeneratorProps {
  userAddress: string;
  fid: number;
}

const CastGenerator = ({ userAddress, fid }: CastGeneratorProps) => {
  const [topic, setTopic] = useState<Topic>("tech");
  const [generatedCast, setGeneratedCast] = useState<string>("");
  const [scheduledTime, setScheduledTime] = useState<Date | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  
  // ... lógica de generación y pago
}
```

#### 3. **Componente: `ScheduledCastsList`**
- Muestra casts programados
- Permite cancelar
- Muestra estado (pendiente, publicado, cancelado)

---

## 🔄 Flujo Completo

### **Flujo: Generar y Publicar Cast**

1. **Usuario selecciona tema** (Tech, Música, etc.)
2. **Frontend llama a `/api/casts/generate`** (solo generación, sin pago)
3. **Backend genera cast con Gemini** y retorna preview
4. **Usuario revisa preview** y decide programar o publicar ahora
5. **Usuario paga cUSD**:
   - Frontend: `cUSD.transfer(BACKEND_WALLET, PRICE)`
   - Usuario firma transacción en wallet
6. **Frontend envía pago + cast**:
   - `POST /api/casts/publish` con `payment_tx_hash`
7. **Backend valida pago**:
   - Verifica transacción on-chain
   - Confirma que el pago es correcto
8. **Backend publica cast**:
   - Si `scheduled_time` es null → publica ahora
   - Si tiene `scheduled_time` → programa para después
9. **Backend otorga XP**:
   - `LootAccessRegistry.grantXp("cast-generation", user_address, 100)`
10. **Frontend muestra confirmación** con link al cast publicado

---

## 📊 Estructura de Datos

### **Cast Programado (Backend Store)**
```python
{
    "cast_id": "uuid",
    "user_address": "0x...",
    "user_fid": 12345,
    "topic": "tech",
    "cast_text": "¡La tecnología blockchain...",
    "scheduled_time": "2025-01-14T10:00:00Z",
    "status": "scheduled" | "published" | "cancelled",
    "payment_tx_hash": "0x...",
    "published_cast_hash": "0x..." | null,
    "xp_granted": 100,
    "created_at": "2025-01-13T15:00:00Z"
}
```

---

## 💰 Modelo de Precios

### **Precios Sugeridos:**
- **Publicar ahora**: 0.5 cUSD → 100 XP
- **Programar cast**: 0.3 cUSD → 50 XP (se otorga al publicar)

### **Límites:**
- Máximo 3 casts programados por día por usuario
- Máximo 10 casts publicados por día por usuario

---

## 🔐 Seguridad

### **Validaciones:**
1. ✅ Verificar que el pago on-chain es válido antes de publicar
2. ✅ Verificar que el usuario no excede límites diarios
3. ✅ Verificar que `scheduled_time` no es en el pasado
4. ✅ Rate limiting en endpoints de generación (evitar abuso de Gemini API)
5. ✅ Validar que el usuario tiene FID válido en Farcaster

---

## 📝 Próximos Pasos

1. ✅ **Analizar contratos** (completado)
2. ⏳ **Implementar `CastGeneratorService`** en backend
3. ⏳ **Implementar `CastSchedulerService`** en backend
4. ⏳ **Agregar método `publish_cast`** en `FarcasterToolbox`
5. ⏳ **Crear endpoints** `/api/casts/*`
6. ⏳ **Crear frontend** `/casts/generate`
7. ⏳ **Integrar pagos** con cUSD
8. ⏳ **Integrar XP** con `LootAccessRegistry`
9. ⏳ **Testing** completo

---

## ❓ Preguntas Pendientes

1. **¿Neynar API permite publicar casts?**
   - Necesitamos verificar si Neynar tiene endpoint para publicar
   - Alternativa: Usar Warpcast API o Farcaster Hub directamente

2. **¿Qué precio cobrar por cast?**
   - Sugerencia: 0.5 cUSD por cast publicado ahora
   - 0.3 cUSD por cast programado

3. **¿Cuánto XP otorgar?**
   - Sugerencia: 100 XP por cast publicado
   - 50 XP por cast programado (se otorga al publicar)

4. **¿Límites diarios?**
   - Sugerencia: 3 casts programados, 10 casts publicados por día

---

**Última actualización:** 2025-01-13

