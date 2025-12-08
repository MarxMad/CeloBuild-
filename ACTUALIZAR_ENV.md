# ⚠️ IMPORTANTE: Actualizar Direcciones en .env

## 🔄 Direcciones Nuevas Desplegadas

Acabamos de desplegar nuevos contratos con mejoras de seguridad. **Debes actualizar las direcciones en tu `apps/agents/.env`:**

```bash
# Reemplaza estas líneas en apps/agents/.env:

LOOTBOX_VAULT_ADDRESS="0x3808D0C3525C4F85F1f8c9a881E3949327FB9cF7"
REGISTRY_ADDRESS="0x86C878108798e2Ce39B783127955B8F8A18ae2BE"
MINTER_ADDRESS="0x0d7370f79f77Ee701C5F40443F8C8969C28b3412"
CUSD_ADDRESS="0x874069Fa1Eb16D44d622F2e0Ca25eeA172369bC1"
```

## ✅ Verificación

Después de actualizar, verifica que todo funciona:

```bash
cd apps/agents
python3 -c "
from web3 import Web3
import os
from dotenv import load_dotenv
load_dotenv('.env')

w3 = Web3(Web3.HTTPProvider(os.getenv('CELO_RPC_URL')))
vault = os.getenv('LOOTBOX_VAULT_ADDRESS')
code = w3.eth.get_code(vault)
print('✅ Contrato verificado' if len(code) > 2 else '❌ Contrato no encontrado')
"
```

## 🎯 Estado Actual

- ✅ **Variables de entorno**: Todas configuradas
- ✅ **Conexión a Celo**: OK (Chain ID: 11142220)
- ✅ **Cuenta del agente**: `0xC6080a5871Dd8aa694a4Cc3aACEEBC2292e54f02`
- ✅ **Balance**: 0.73 CELO (suficiente para transacciones)
- ⚠️ **Direcciones de contratos**: Necesitan actualización

## 🚀 Después de Actualizar

Una vez actualizadas las direcciones, el sistema estará completamente funcional:

1. ✅ El agente puede crear campañas dinámicamente
2. ✅ El scheduler ejecutará cada 30 minutos
3. ✅ Las recompensas se distribuirán automáticamente
4. ✅ Todo está listo para producción

