# ✅ Checklist de Producción - Premio.xyz

## 🔒 Seguridad

- [x] Límites de seguridad en contratos (max recipients, max amounts)
- [x] Validación de duplicados en contratos
- [x] Protección contra overflow/underflow
- [x] Validación de direcciones en backend
- [x] Rate limiting en API
- [x] Validación de inputs en endpoints
- [x] Documentación de seguridad (SECURITY.md)

## 📝 Contratos

- [ ] **Compilar contratos con mejoras de seguridad**
  ```bash
  cd apps/contracts
  forge build
  ```

- [ ] **Desplegar contratos en Celo Sepolia**
  ```bash
  export DEPLOYER_PRIVATE_KEY=0x...
  export AGENT_ADDRESS=0x...  # Dirección del agente (derivada de CELO_PRIVATE_KEY)
  export CELO_RPC_URL=https://...
  export CUSD_ADDRESS=0x874069Fa1Eb16D44d622F2e0Ca25eeA172369bC1  # Opcional
  
  chmod +x deploy-production.sh
  ./deploy-production.sh
  ```

- [ ] **Verificar ownership del agente**
  ```bash
  cast call $LOOTBOX_VAULT_ADDRESS "owner()(address)" --rpc-url $CELO_RPC_URL
  cast call $REGISTRY_ADDRESS "owner()(address)" --rpc-url $CELO_RPC_URL
  cast call $MINTER_ADDRESS "owner()(address)" --rpc-url $CELO_RPC_URL
  # Deben retornar: $AGENT_ADDRESS
  ```

- [ ] **Actualizar direcciones en `.env`**
  - `apps/agents/.env`: Agregar `LOOTBOX_VAULT_ADDRESS`, `REGISTRY_ADDRESS`, `MINTER_ADDRESS`
  - `apps/agents/.env`: Agregar `CUSD_ADDRESS`

## 🔧 Backend (Agents)

- [ ] **Verificar variables de entorno**
  ```bash
  cd apps/agents
  # Verificar que todas las variables estén configuradas
  cat .env | grep -E "(CELO_PRIVATE_KEY|LOOTBOX_VAULT_ADDRESS|REGISTRY_ADDRESS|MINTER_ADDRESS|NEYNAR_API_KEY|GOOGLE_API_KEY)"
  ```

- [ ] **Verificar que el agente puede crear campañas**
  - El agente debe ser owner de los contratos (verificado arriba)
  - `CELO_PRIVATE_KEY` debe corresponder a `AGENT_ADDRESS`

- [ ] **Probar conexión a contratos**
  ```bash
  # Desde Python
  python3 -c "
  from web3 import Web3
  from eth_account import Account
  w3 = Web3(Web3.HTTPProvider('$CELO_RPC_URL'))
  account = Account.from_key('$CELO_PRIVATE_KEY')
  print(f'Agent address: {account.address}')
  print(f'Balance: {w3.eth.get_balance(account.address) / 1e18} CELO')
  "
  ```

- [ ] **Verificar APIs externas**
  - [ ] Neynar API key válida y con créditos
  - [ ] Google API key válida (Gemini)
  - [ ] MiniPay Tool API (opcional, solo si usas PROJECT_SECRET)

## 🎨 Frontend (Web)

- [ ] **Verificar variables de entorno**
  ```bash
  cd apps/web
  # Verificar que estén configuradas:
  # - NEXT_PUBLIC_WC_PROJECT_ID
  # - NEXT_PUBLIC_AGENT_SERVICE_URL
  ```

- [ ] **Build del frontend**
  ```bash
  cd apps/web
  pnpm build
  # Verificar que no haya errores
  ```

- [ ] **Probar localmente**
  ```bash
  pnpm dev
  # Abrir http://localhost:3000 y verificar que funciona
  ```

## 🚀 Deployment

### Backend (Railway/Render/Vercel)

- [ ] **Configurar variables de entorno en plataforma**
  - Copiar todas las variables de `apps/agents/.env`
  - **IMPORTANTE**: `CELO_PRIVATE_KEY` debe estar en secret manager

- [ ] **Desplegar backend**
  - Railway: Conectar repo, configurar root directory `apps/agents`
  - Render: Similar a Railway
  - Vercel: Serverless (puede tener timeouts)

- [ ] **Verificar health check**
  ```bash
  curl https://tu-backend.railway.app/healthz
  # Debe retornar: {"status":"ok"}
  ```

### Frontend (Vercel)

- [ ] **Configurar proyecto en Vercel**
  - Root Directory: `apps/web`
  - Framework: Next.js

- [ ] **Configurar variables de entorno**
  - `NEXT_PUBLIC_WC_PROJECT_ID`
  - `NEXT_PUBLIC_AGENT_SERVICE_URL` (URL del backend desplegado)

- [ ] **Desplegar**
  - Push a main branch o deploy manual

- [ ] **Verificar deployment**
  - Abrir URL de Vercel
  - Verificar que la app carga correctamente
  - Probar conexión de wallet

## 🧪 Testing

- [ ] **Probar detección de tendencias**
  - El scheduler debe ejecutarse cada 30 minutos
  - Verificar logs del backend para ver si detecta tendencias

- [ ] **Probar distribución de recompensas**
  - Activar manualmente desde el frontend
  - Verificar que se crean campañas automáticamente
  - Verificar que se distribuyen recompensas (NFT, cUSD, XP)

- [ ] **Verificar leaderboard**
  ```bash
  curl https://tu-backend.railway.app/api/lootbox/leaderboard?limit=10
  ```

## 📊 Monitoreo

- [ ] **Configurar alertas**
  - Alertas para errores en backend
  - Alertas para transacciones fallidas
  - Alertas para rate limiting

- [ ] **Configurar logging**
  - Verificar que los logs se están guardando
  - Configurar rotación de logs

- [ ] **Monitorear fondos**
  - Verificar balance de CELO en cuenta del agente (para gas)
  - Verificar balance de cUSD en LootBoxVault (si usas vault)
  - Configurar alertas para fondos bajos

## 💰 Fondos

- [ ] **Fondos para gas (CELO)**
  - Mínimo 1-2 CELO en cuenta del agente para transacciones
  - Monitorear y recargar cuando sea necesario

- [ ] **Fondos para recompensas (cUSD)**
  - Si usas LootBoxVault: depositar cUSD en el vault
  - Si usas MiniPay Tool API: verificar que la API esté configurada

## 📚 Documentación

- [x] README.md actualizado
- [x] SECURITY.md creado
- [x] PRODUCTION_SETUP.md creado
- [x] VISION.md actualizado
- [ ] Actualizar README con nuevas direcciones de contratos después del deployment

## 🎯 Post-Deployment

- [ ] **Verificar primera campaña**
  - Esperar a que el scheduler detecte una tendencia
  - Verificar que se crea la campaña automáticamente
  - Verificar que se distribuyen recompensas

- [ ] **Comunicar a usuarios**
  - Anunciar el lanzamiento
  - Compartir URL del frontend
  - Explicar cómo funciona el sistema

---

## 🆘 Troubleshooting

### El agente no puede crear campañas
- Verificar que el agente es owner: `cast call $CONTRACT "owner()(address)"`
- Verificar que `CELO_PRIVATE_KEY` corresponde a `AGENT_ADDRESS`

### Transacciones fallan
- Verificar balance de CELO en cuenta del agente
- Verificar que los contratos están desplegados correctamente
- Verificar logs del backend para errores específicos

### No se detectan tendencias
- Verificar que Neynar API key es válida y tiene créditos
- Verificar logs del backend para ver errores de API
- Verificar que el scheduler está corriendo

### Frontend no se conecta al backend
- Verificar que `NEXT_PUBLIC_AGENT_SERVICE_URL` está configurada correctamente
- Verificar CORS en el backend
- Verificar que el backend está desplegado y accesible

