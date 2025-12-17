# ✅ Verificar que el precio sea 0.1 CELO

## Estado del Código (Confirmado ✅)

### Frontend
- `cast-generator.tsx` línea 130: `parseEther("0.1")`
- `cast-generator.tsx` línea 219: `parseEther("0.1")`
- `dictionary.ts` línea 114 (ES): `"Vas a pagar 0.1 CELO para generar este cast con IA."`
- `dictionary.ts` línea 299 (EN): `"You are about to pay 0.1 CELO to generate this cast with AI."`

### Backend
- `main.py` línea 1016: `PRICE_WEI = int(0.1 * 10**18)`
- `main.py` línea 1329: `PRICE_WEI = int(0.1 * 10**18)`

---

## 🔧 Pasos para Verificar en tu App

### 1. Espera a que Vercel termine el deployment
- Ve a: https://vercel.com/tu-proyecto
- Espera a que el status sea "Ready" (2-3 minutos)
- El último commit debe ser: `fix: Forzar actualización de caché para precio 0.1 CELO`

### 2. Limpia el caché de tu navegador

**En Chrome/Brave/Opera:**
```
1. Abre DevTools: F12 o Cmd+Option+I (Mac)
2. Clic derecho en el botón de recargar (⟳)
3. Selecciona "Vaciar caché y recargar de forma forzada"
```

**En Safari:**
```
1. Cmd + Option + E (Vaciar caché)
2. Cmd + R (Recargar)
```

**En Minipay/MiniApp:**
```
1. Cierra completamente la app
2. Borra el caché de la app desde Configuración del sistema
3. Vuelve a abrir la app
```

### 3. Verifica en la consola del navegador

Cuando hagas clic en "Generar Cast", deberías ver en la consola:

```
💰 [CastGenerator] Iniciando pago de 0.1 CELO para generar cast...
📝 [CastGenerator] Enviando transacción: {to: '0x...', value: '100000000000000000'}
```

**IMPORTANTE**: El `value` debe ser `100000000000000000` (0.1 CELO en wei).

Si ves `500000000000000000`, entonces tu navegador aún tiene la versión antigua en caché.

### 4. Verifica en el modal de confirmación de Minipay

El modal de tu wallet Minipay/Valora debe mostrar:
- **Cantidad**: `0.1 CELO`
- **No** `0.5 CELO`

---

## 🐛 Si aún ves 0.5 CELO

1. **Borra completamente los datos de la app**
2. **Desinstala y reinstala Minipay** (si es una app nativa)
3. **Usa el modo incógnito del navegador** para probar sin caché
4. **Verifica la URL**: Debe ser la correcta (no una versión antigua guardada)

---

## 📊 Cómo convertir WEI a CELO

- **0.1 CELO** = `100000000000000000` wei
- **0.5 CELO** = `500000000000000000` wei

Si ves `500000000000000000` en los logs, entonces hay caché.
Si ves `100000000000000000`, entonces está correcto ✅

---

## 🆘 Última Opción: Hard Refresh

Abre la app con estos parámetros en la URL:
```
https://tu-app.vercel.app/?v=2.0&cache=bust&timestamp=1734470400
```

Esto forzará al navegador a ignorar el caché.

