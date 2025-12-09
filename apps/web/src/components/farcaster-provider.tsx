"use client";

import { useEffect, useState, createContext, useContext } from "react";
import { sdk } from "@farcaster/miniapp-sdk";

// Contexto para compartir información del usuario de Farcaster
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
 * Según la documentación oficial:
 * https://miniapps.farcaster.xyz/docs/getting-started#making-your-app-display
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

        // 2. Obtener contexto del usuario
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
