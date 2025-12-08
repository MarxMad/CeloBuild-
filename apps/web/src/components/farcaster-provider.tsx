"use client";

import { useEffect, useState, createContext, useContext } from "react";
import { sdk } from "@farcaster/miniapp-sdk";

// Contexto para compartir información del usuario de Farcaster
interface FarcasterUserContextType {
  fid: number | null;
  username: string | null;
  custodyAddress: string | null;
}

const FarcasterUserContext = createContext<FarcasterUserContextType>({
  fid: null,
  username: null,
  custodyAddress: null,
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
    custodyAddress: null,
  });

  useEffect(() => {
    // Función para obtener información del usuario de Farcaster
    const fetchUserInfo = async () => {
      try {
        // Obtener el contexto del usuario desde el SDK de Farcaster
        const context = await sdk.context;
        if (context?.user) {
          setUserContext({
            fid: context.user.fid || null,
            username: context.user.username || null,
            custodyAddress: context.user.custodyAddress || null,
          });
          console.log("✅ Usuario de Farcaster obtenido:", {
            fid: context.user.fid,
            username: context.user.username,
            custodyAddress: context.user.custodyAddress,
          });
        }
      } catch (error) {
        console.log("ℹ️ No se pudo obtener contexto de usuario (normal fuera de Farcaster)");
      }
    };

    // Función para llamar a ready() de forma segura
    const callReady = async () => {
      try {
        // Verificar que estamos en el cliente
        if (typeof window === "undefined") return;

        // Llamar a ready() - esto notifica a Farcaster que la MiniApp está lista
        // Según la documentación: "After your app is fully loaded and ready to display"
        await sdk.actions.ready();
        console.log("✅ Farcaster MiniApp ready() called successfully");
        
        // Intentar obtener información del usuario después de ready()
        await fetchUserInfo();
      } catch (error) {
        // Si no estamos en un contexto de MiniApp, esto es normal
        // No mostrar error en consola para no confundir en desarrollo
        if (process.env.NODE_ENV === "development") {
          console.log("ℹ️ Not in MiniApp context (normal in browser)");
        }
      }
    };

    // Estrategia: Llamar a ready() cuando el contenido esté completamente renderizado
    // 1. Si el DOM ya está listo, llamar inmediatamente
    if (document.readyState === "complete" || document.readyState === "interactive") {
      // Pequeño delay para asegurar que React haya renderizado todo
      setTimeout(callReady, 0);
    } else {
      // 2. Esperar a que el DOM esté completamente cargado
      const handleDOMReady = () => {
        setTimeout(callReady, 0);
      };
      document.addEventListener("DOMContentLoaded", handleDOMReady);

      // 3. También llamar cuando la ventana esté completamente cargada (recursos, imágenes, etc.)
      const handleWindowLoad = () => {
        setTimeout(callReady, 50);
      };
      window.addEventListener("load", handleWindowLoad);

      return () => {
        document.removeEventListener("DOMContentLoaded", handleDOMReady);
        window.removeEventListener("load", handleWindowLoad);
      };
    }
  }, []);

  return (
    <FarcasterUserContext.Provider value={userContext}>
      {children}
    </FarcasterUserContext.Provider>
  );
}
