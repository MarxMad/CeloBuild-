# 🚀 Deployment en Vercel - Guía Rápida

## ✅ Push Completado

Todos los cambios han sido pusheados al repositorio:
- ✅ Mejoras de seguridad en contratos
- ✅ Sistema de campañas dinámicas
- ✅ Validaciones y rate limiting
- ✅ Scripts de deployment optimizados
- ✅ Documentación completa

## 📋 Verificación Post-Deployment

### Backend (Vercel - apps/agents)

Después de que Vercel despliegue el backend, verifica:

1. **Variables de Entorno en Vercel:**
   - `CELO_PRIVATE_KEY` ✅
   - `LOOTBOX_VAULT_ADDRESS=0x3808D0C3525C4F85F1f8c9a881E3949327FB9cF7` ✅
   - `REGISTRY_ADDRESS=0x86C878108798e2Ce39B783127955B8F8A18ae2BE` ✅
   - `MINTER_ADDRESS=0x0d7370f79f77Ee701C5F40443F8C8969C28b3412` ✅
   - `CELO_RPC_URL` ✅
   - `NEYNAR_API_KEY` ✅
   - `GOOGLE_API_KEY` ✅
   - Todas las demás variables de `apps/agents/env.sample`

2. **Health Check:**
   ```bash
   curl https://tu-backend.vercel.app/healthz
   # Debe retornar: {"status":"ok"}
   ```

3. **Verificar Scheduler:**
   - El scheduler debe iniciar automáticamente
   - Verifica los logs en Vercel para confirmar

### Frontend (Vercel - apps/web)

Después de que Vercel despliegue el frontend, verifica:

1. **Variables de Entorno en Vercel:**
   - `NEXT_PUBLIC_WC_PROJECT_ID` ✅
   - `NEXT_PUBLIC_AGENT_SERVICE_URL` (URL del backend desplegado) ✅

2. **Verificar que carga:**
   - Abre la URL de Vercel
   - Verifica que la app carga correctamente
   - Prueba conectar wallet

## 🧪 Pruebas Rápidas

### 1. Probar Health Check del Backend

```bash
curl https://tu-backend.vercel.app/healthz
```

### 2. Probar Leaderboard

```bash
curl https://tu-backend.vercel.app/api/lootbox/leaderboard?limit=5
```

### 3. Probar Activación Manual (desde Frontend)

1. Abre el frontend en Vercel
2. Conecta tu wallet
3. Haz clic en "Activar Recompensas"
4. Selecciona tipo de recompensa (NFT, cUSD, XP)
5. Espera la confirmación

### 4. Verificar Primera Ejecución Automática

El scheduler ejecutará automáticamente cada 30 minutos. Para verificar:

1. Revisa los logs del backend en Vercel
2. Busca mensajes como:
   - "🤖 Ejecutando scan de tendencias Farcaster..."
   - "Scan completado: ..."
   - "✅ Campaña X configurada exitosamente"

## 🔍 Monitoreo

### Logs del Backend

En Vercel, ve a:
- Tu proyecto → Deployments → Logs

Busca:
- ✅ "Scheduler iniciado: ejecutando scans cada 30 minutos"
- ✅ "Trend detectado: ..."
- ✅ "Campaña X configurada exitosamente"
- ✅ "Recompensa distribuida: ..."

### Transacciones On-Chain

Usa los links de Blockscout en el README para ver:
- Transacciones de configuración de campañas
- Transacciones de distribución de recompensas
- NFTs minteados
- XP otorgado

## ⚠️ Troubleshooting

### Backend no responde

1. Verifica que todas las variables de entorno estén configuradas
2. Revisa los logs en Vercel para errores
3. Verifica que `CELO_RPC_URL` sea accesible

### Scheduler no ejecuta

1. Verifica `AUTO_SCAN_ON_STARTUP=true` en variables de entorno
2. Verifica `AUTO_SCAN_INTERVAL_MINUTES=30`
3. Revisa logs para errores de inicialización

### Frontend no se conecta al backend

1. Verifica `NEXT_PUBLIC_AGENT_SERVICE_URL` en frontend
2. Verifica CORS en backend (debe permitir el dominio del frontend)
3. Verifica que el backend esté desplegado y accesible

### No se detectan tendencias

1. Verifica que `NEYNAR_API_KEY` sea válida y tenga créditos
2. Revisa logs para errores de API
3. Verifica que `GOOGLE_API_KEY` sea válida (para análisis IA)

## 📊 Estado Esperado

Después del deployment exitoso:

- ✅ Backend desplegado y accesible
- ✅ Frontend desplegado y accesible
- ✅ Scheduler ejecutándose cada 30 minutos
- ✅ Sistema listo para detectar tendencias
- ✅ Campañas se crearán automáticamente
- ✅ Recompensas se distribuirán automáticamente

---

**¡Todo listo para probar! 🚀**
