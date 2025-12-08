import { NextResponse } from "next/server";

const AGENT_SERVICE_URL = process.env.AGENT_SERVICE_URL ?? process.env.NEXT_PUBLIC_AGENT_SERVICE_URL;

export async function GET(request: Request) {
  // Log para debugging
  console.log("[TRENDS] AGENT_SERVICE_URL:", AGENT_SERVICE_URL ? `✅ ${AGENT_SERVICE_URL}` : "❌ No configurado");
  
  // Si no hay AGENT_SERVICE_URL, retornar lista vacía en lugar de error
  if (!AGENT_SERVICE_URL) {
    console.warn("AGENT_SERVICE_URL no configurado, retornando trends vacío");
    return NextResponse.json({ items: [] });
  }

  const url = new URL(request.url);
  const limit = url.searchParams.get("limit") ?? "10";

  try {
    const backendUrl = `${AGENT_SERVICE_URL}/api/lootbox/trends?limit=${limit}`;
    console.log("[TRENDS] Llamando al backend:", backendUrl);
    
    const response = await fetch(backendUrl, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
      cache: "no-store",
    });

    console.log("[TRENDS] Respuesta del backend:", response.status, response.statusText);

    if (!response.ok) {
      // Leer el error una sola vez
      const errorText = await response.text();
      console.error(`[TRENDS] Error del backend: ${response.status} - ${errorText}`);
      // Retornar lista vacía en lugar de error
      return NextResponse.json({ items: [] });
    }

    // Leer el body una sola vez
    const data = await response.json();
    console.log("[TRENDS] Datos recibidos:", data.items?.length || 0, "tendencias");
    return NextResponse.json(data);
  } catch (error) {
    console.error("[TRENDS] Error conectando al backend:", error);
    // Retornar lista vacía en lugar de error
    return NextResponse.json({ items: [] });
  }
}


