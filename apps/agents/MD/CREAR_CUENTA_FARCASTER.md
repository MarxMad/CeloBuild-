# 🚀 Guía: Crear Cuenta Farcaster Nueva para tu App

## 📱 Método 1: Crear cuenta a través de Warpcast (RECOMENDADO)

### Paso 1: Descargar Warpcast
1. **Móvil (Recomendado):**
   - iOS: [App Store](https://apps.apple.com/app/warpcast/id6444901002)
   - Android: [Google Play](https://play.google.com/store/apps/details?id=com.farcaster.mobile)

2. **Web (Alternativa):**
   - Ve a [warpcast.com](https://warpcast.com)

### Paso 2: Crear cuenta nueva
1. Abre Warpcast
2. Toca "Sign up" o "Crear cuenta"
3. **IMPORTANTE:** Usa un nombre relacionado con tu app:
   - Ejemplo: `@premio_xyz` o `@premio_app`
   - Este nombre aparecerá cuando los usuarios aprueben signers

### Paso 3: Conectar wallet
1. Warpcast te pedirá conectar una wallet
2. **Crea una wallet nueva** (recomendado) o usa una existente
3. **Si creas wallet nueva:**
   - Warpcast generará un mnemonic de 12 palabras
   - **¡GUARDA ESTE MNEMONIC!** Este será tu `NEYNAR_APP_MNEMONIC`
   - Escríbelo en un lugar seguro (nunca lo compartas)

### Paso 4: Completar registro
1. Completa tu perfil:
   - Nombre de usuario (ej: `premio_xyz`)
   - Foto de perfil (opcional, pero recomendado)
   - Bio (opcional)
2. Acepta los términos y condiciones

### Paso 5: Obtener el mnemonic
1. Ve a **Settings** (Configuración) en Warpcast
2. Busca **"Wallet"** o **"Custody Address"**
3. Si usaste una wallet nueva, el mnemonic debería estar disponible
4. **Si no puedes ver el mnemonic:**
   - Puede que Warpcast use custodia gestionada
   - En ese caso, necesitas exportar la wallet desde donde la creaste

### Paso 6: Verificar tu FID
1. En Warpcast, ve a tu perfil
2. Tu FID aparece en la URL o en "About"
3. Ejemplo: `warpcast.com/premio_xyz` → FID está en el perfil
4. O usa la API de Neynar para buscarlo (ver abajo)

---

## 🔧 Método 2: Obtener FID desde el mnemonic (si ya tienes cuenta)

Si ya creaste la cuenta pero no sabes tu FID, puedes obtenerlo así:

```python
# Script para obtener FID desde mnemonic
from eth_account import Account
from web3 import Web3

# Tu mnemonic
mnemonic = "tu mnemonic de 12 palabras aquí"

# Crear cuenta desde mnemonic
account = Account.from_mnemonic(mnemonic)
custody_address = account.address

# Buscar FID usando Neynar API
import httpx

async def get_fid_from_address(custody_address: str, neynar_api_key: str):
    url = f"https://api.neynar.com/v2/farcaster/user/by_custody_address"
    params = {"custody_address": custody_address}
    headers = {"x-api-key": neynar_api_key}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return data.get("result", {}).get("fid")
    return None
```

---

## ✅ Checklist Final

Después de crear la cuenta, verifica que tienes:

- [ ] ✅ Cuenta Farcaster creada con nombre de app (ej: `@premio_xyz`)
- [ ] ✅ Mnemonic de 12 palabras guardado de forma segura
- [ ] ✅ FID de la cuenta (se obtiene automáticamente o manualmente)
- [ ] ✅ Wallet con algo de ETH en Optimism (para aprobar signers, ~$2)

---

## 🔐 Configuración en Vercel

Una vez que tengas todo, configura en Vercel:

```bash
# Opción 1: Solo mnemonic (FID se obtiene automáticamente)
NEYNAR_APP_MNEMONIC="palabra1 palabra2 palabra3 ... palabra12"

# Opción 2: Mnemonic + FID (más rápido)
NEYNAR_APP_MNEMONIC="palabra1 palabra2 palabra3 ... palabra12"
NEYNAR_APP_FID="12345"  # Tu FID
```

---

## 💡 Tips Importantes

1. **Seguridad del Mnemonic:**
   - NUNCA lo compartas con nadie
   - NUNCA lo subas a GitHub
   - Guárdalo en un gestor de contraseñas (1Password, LastPass, etc.)
   - O escríbelo en papel y guárdalo en un lugar seguro

2. **Wallet Dedicada:**
   - Usa una wallet SOLO para esta cuenta de app
   - No uses tu wallet personal principal
   - Mantén algo de ETH en Optimism para transacciones

3. **Nombre de Usuario:**
   - Elige un nombre profesional relacionado con tu app
   - Este nombre aparecerá cuando los usuarios aprueben signers
   - Ejemplos: `@premio_xyz`, `@premio_app`, `@premio_ai`

---

## 🆘 Si tienes problemas

1. **No puedo ver el mnemonic en Warpcast:**
   - Warpcast puede usar custodia gestionada
   - Crea una wallet nueva con MetaMask o similar
   - Luego conecta esa wallet a Warpcast

2. **No sé mi FID:**
   - Ve a tu perfil en Warpcast
   - O usa el script de arriba para obtenerlo desde el custody address

3. **¿Necesito ETH en Optimism?**
   - Sí, necesitas ~$2 en OP ETH para aprobar signers
   - Puedes obtener OP ETH en exchanges o usando un bridge

---

## 🎯 Siguiente Paso

Una vez que tengas la cuenta creada y el mnemonic guardado:

1. Configura `NEYNAR_APP_MNEMONIC` en Vercel
2. El sistema obtendrá el FID automáticamente
3. ¡Ya puedes crear signers para tus usuarios!

