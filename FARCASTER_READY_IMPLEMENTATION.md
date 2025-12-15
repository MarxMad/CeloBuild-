# Implementación de `sdk.actions.ready()` en Farcaster Mini Apps

Este documento explica cómo implementar correctamente `sdk.actions.ready()` para evitar la pantalla de carga infinita en Farcaster Mini Apps.

## 📚 Documentación Oficial

- [SDK Actions - ready()](https://miniapps.farcaster.xyz/docs/sdk/actions/ready)
- [Loading your app - Best Practices](https://miniapps.farcaster.xyz/docs/guides/loading-your-app)

## ⚠️ ¿Por qué es importante?

Si no llamas `sdk.actions.ready()`, los usuarios verán una **pantalla de carga infinita** en Warpcast. Esta función le dice a Farcaster que tu app ya está lista para mostrarse.

## 🚀 Implementación Básica

### 1. Instalar el SDK

```bash
npm install @farcaster/miniapp-sdk
# o
pnpm add @farcaster/miniapp-sdk
```

### 2. Importar el SDK

```typescript
import { sdk } from '@farcaster/miniapp-sdk'
```

### 3. Llamar `ready()` en un `useEffect`

**Opción A: En el componente raíz (recomendado)**

```typescript
"use client";

import { useEffect } from 'react';
import { sdk } from '@farcaster/miniapp-sdk';

export default function Home() {
  useEffect(() => {
    const init = async () => {
      try {
        // Llamar ready() lo antes posible
        await sdk.actions.ready();
        console.log("✅ App ready");
      } catch (error) {
        // Ignorar errores si no estamos en contexto de Farcaster
        console.log("ℹ️ Not in Farcaster context");
      }
    };

    init();
  }, []);

  return (
    <div>
      {/* Tu contenido aquí */}
    </div>
  );
}
```

**Opción B: En un Provider (mejor para apps complejas)**

```typescript
"use client";

import { useEffect } from 'react';
import { sdk } from '@farcaster/miniapp-sdk';

export function FarcasterProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    const init = async () => {
      try {
        // 1. Notificar que la app está lista inmediatamente
        await sdk.actions.ready();
        console.log("✅ Farcaster MiniApp ready() called successfully");

        // 2. Opcional: Obtener contexto del usuario
        const context = await sdk.context;
        if (context?.user) {
          console.log("Usuario:", context.user);
        }
      } catch (error) {
        // Ignorar errores si no estamos en Farcaster
        console.log("ℹ️ Farcaster SDK init skipped (not in frame context)");
      }
    };

    init();
  }, []);

  return <>{children}</>;
}
```

Luego en tu `layout.tsx`:

```typescript
import { FarcasterProvider } from '@/components/farcaster-provider';

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        <FarcasterProvider>
          {children}
        </FarcasterProvider>
      </body>
    </html>
  );
}
```

## ✅ Ejemplo Completo (Como lo tenemos en Premio.xyz)

### `farcaster-provider.tsx`

```typescript
"use client";

import { useEffect, useState, createContext, useContext } from "react";
import { sdk } from "@farcaster/miniapp-sdk";

// Contexto para compartir información del usuario
interface FarcasterUserContextType {
  fid: number | null;
  username: string | null;
}

const FarcasterUserContext = createContext<FarcasterUserContextType>({
  fid: null,
  username: null,
});

export const useFarcasterUser = () => useContext(FarcasterUserContext);

/**
 * FarcasterProvider - Inicializa el SDK de Farcaster MiniApp
 * 
 * IMPORTANTE: Debe llamarse sdk.actions.ready() después de que la app esté
 * completamente cargada, o los usuarios verán una pantalla de carga infinita.
 */
export function FarcasterProvider({ children }: { children: React.ReactNode }) {
  const [userContext, setUserContext] = useState<FarcasterUserContextType>({
    fid: null,
    username: null,
  });

  useEffect(() => {
    const init = async () => {
      try {
        // 1. Notificar que la app está lista inmediatamente
        // Esto es crítico para quitar el spinner de carga de Farcaster
        await sdk.actions.ready();
        console.log("✅ Farcaster MiniApp ready() called successfully");

        // 2. Obtener contexto del usuario (opcional)
        const context = await sdk.context;
        if (context?.user) {
          setUserContext({
            fid: context.user.fid || null,
            username: context.user.username || null,
          });
          console.log("✅ Usuario de Farcaster obtenido:", context.user);
        }
      } catch (error) {
        // Ignorar errores si no estamos en Farcaster
        // Esto permite que la app funcione también en navegadores normales
        console.log("ℹ️ Farcaster SDK init skipped (not in frame context)");
      }
    };

    init();
  }, []);

  return (
    <FarcasterUserContext.Provider value={userContext}>
      {children}
    </FarcasterUserContext.Provider>
  );
}
```

### `layout.tsx`

```typescript
import { FarcasterProvider } from "@/components/farcaster-provider";

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        <FarcasterProvider>
          {children}
        </FarcasterProvider>
      </body>
    </html>
  );
}
```

## 🔍 Errores Comunes y Soluciones

### ❌ Error 1: Pantalla de carga infinita

**Problema:** No estás llamando `ready()` o lo llamas muy tarde.

**Solución:** Llama `ready()` lo antes posible, idealmente en un `useEffect` del componente raíz o Provider.

```typescript
// ✅ CORRECTO
useEffect(() => {
  sdk.actions.ready();
}, []);

// ❌ INCORRECTO - Muy tarde
useEffect(() => {
  // ... cargar datos ...
  // ... esperar respuestas de API ...
  sdk.actions.ready(); // ❌ Demasiado tarde
}, []);
```

### ❌ Error 2: Error en navegadores normales

**Problema:** El SDK solo funciona en contexto de Farcaster, puede fallar en navegadores normales.

**Solución:** Siempre usa `try/catch`:

```typescript
// ✅ CORRECTO
try {
  await sdk.actions.ready();
} catch (error) {
  // Ignorar si no estamos en Farcaster
  console.log("Not in Farcaster context");
}

// ❌ INCORRECTO
await sdk.actions.ready(); // Puede fallar en navegadores normales
```

### ❌ Error 3: Llamar `ready()` múltiples veces

**Problema:** Llamar `ready()` en varios componentes puede causar problemas.

**Solución:** Llámalo solo una vez, en el componente raíz o Provider.

```typescript
// ✅ CORRECTO - Una sola vez en el Provider
<FarcasterProvider>
  <App />
</FarcasterProvider>

// ❌ INCORRECTO - Múltiples llamadas
<Home /> // Llama ready()
<Dashboard /> // Llama ready() otra vez
```

## 📋 Checklist de Implementación

- [ ] Instalar `@farcaster/miniapp-sdk`
- [ ] Importar `sdk` desde `@farcaster/miniapp-sdk`
- [ ] Llamar `sdk.actions.ready()` en un `useEffect`
- [ ] Usar `try/catch` para manejar errores
- [ ] Llamar `ready()` lo antes posible (no esperar a cargar datos)
- [ ] Llamar `ready()` solo una vez (en el componente raíz o Provider)

## 🎯 Mejores Prácticas

1. **Llamar `ready()` inmediatamente**: No esperes a que carguen datos o imágenes. Llámalo tan pronto como el componente se monte.

2. **Usar un Provider**: Si tu app es compleja, crea un `FarcasterProvider` que envuelva toda la app.

3. **Manejar errores gracefully**: Siempre usa `try/catch` para que la app funcione también fuera de Farcaster.

4. **No llamar múltiples veces**: Asegúrate de llamar `ready()` solo una vez.

5. **Opcional: Esperar un pequeño delay**: Si tienes problemas, puedes esperar 100ms antes de llamar `ready()`:

```typescript
useEffect(() => {
  const init = async () => {
    // Pequeño delay para asegurar que todo está renderizado
    await new Promise((resolve) => setTimeout(resolve, 100));
    try {
      await sdk.actions.ready();
    } catch (error) {
      // Ignorar errores
    }
  };
  init();
}, []);
```

## 🔗 Referencias

- [Documentación oficial de ready()](https://miniapps.farcaster.xyz/docs/sdk/actions/ready)
- [Guía de carga de apps](https://miniapps.farcaster.xyz/docs/guides/loading-your-app)
- [SDK de Farcaster Mini Apps](https://miniapps.farcaster.xyz/docs)

## 💡 Ejemplo Mínimo Funcional

```typescript
"use client";

import { useEffect } from 'react';
import { sdk } from '@farcaster/miniapp-sdk';

export default function App() {
  useEffect(() => {
    const init = async () => {
      try {
        await sdk.actions.ready();
      } catch (error) {
        // Ignorar si no está en Farcaster
      }
    };
    init();
  }, []);

  return <div>Tu app aquí</div>;
}
```

¡Eso es todo! Con esto deberías poder resolver el problema de la pantalla de carga infinita. 🚀

