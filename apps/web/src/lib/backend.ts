/**
 * Helper para obtener la URL del backend de forma consistente
 */

export function getBackendUrl(): string | null {
  let url: string | null = null;
  
  if (typeof window === "undefined") {
    // Server-side: usar ambas variables
    url = process.env.AGENT_SERVICE_URL ?? process.env.NEXT_PUBLIC_AGENT_SERVICE_URL ?? null;
  } else {
    // Client-side: solo NEXT_PUBLIC_ está disponible
    url = process.env.NEXT_PUBLIC_AGENT_SERVICE_URL ?? null;
  }
  
  // Eliminar trailing slash para evitar doble slash en URLs
  if (url) {
    url = url.replace(/\/+$/, "");
  }
  
  return url;
}

export function getBackendUrlOrThrow(): string {
  const url = getBackendUrl();
  if (!url) {
    throw new Error("Backend no configurado. Verifica NEXT_PUBLIC_AGENT_SERVICE_URL en variables de entorno.");
  }
  return url;
}

