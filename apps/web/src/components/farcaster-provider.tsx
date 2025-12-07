"use client";

import { useEffect } from "react";
import { sdk } from "@farcaster/miniapp-sdk";

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
  useEffect(() => {
    // Función para llamar a ready() de forma segura
    const callReady = async () => {
      try {
        // Verificar que estamos en el cliente
        if (typeof window === "undefined") return;

        // Llamar a ready() - esto notifica a Farcaster que la MiniApp está lista
        // Según la documentación: "After your app is fully loaded and ready to display"
        await sdk.actions.ready();
        console.log("✅ Farcaster MiniApp ready() called successfully");
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

  return <>{children}</>;
}
