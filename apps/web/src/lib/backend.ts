/**
 * Helper para obtener la URL del backend de forma consistente
 */

export function getBackendUrl(): string | null {
  if (typeof window === "undefined") {
    // Server-side: usar ambas variables
    return process.env.AGENT_SERVICE_URL ?? process.env.NEXT_PUBLIC_AGENT_SERVICE_URL ?? null;
  }
  // Client-side: solo NEXT_PUBLIC_ está disponible
  return process.env.NEXT_PUBLIC_AGENT_SERVICE_URL ?? null;
}

export function getBackendUrlOrThrow(): string {
  const url = getBackendUrl();
  if (!url) {
    throw new Error("Backend no configurado. Verifica NEXT_PUBLIC_AGENT_SERVICE_URL en variables de entorno.");
  }
  return url;
}

