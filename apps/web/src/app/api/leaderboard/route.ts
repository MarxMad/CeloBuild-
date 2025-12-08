import { NextResponse } from "next/server";

const AGENT_SERVICE_URL = process.env.AGENT_SERVICE_URL ?? process.env.NEXT_PUBLIC_AGENT_SERVICE_URL;

export async function GET(request: Request) {
  // Si no hay AGENT_SERVICE_URL, retornar lista vacía en lugar de error
  if (!AGENT_SERVICE_URL) {
    console.warn("AGENT_SERVICE_URL no configurado, retornando leaderboard vacío");
    return NextResponse.json({ items: [] });
  }

  const url = new URL(request.url);
  const limit = url.searchParams.get("limit") ?? "5";

  try {
    const response = await fetch(`${AGENT_SERVICE_URL}/api/lootbox/leaderboard?limit=${limit}`, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
      cache: "no-store",
    });

    if (!response.ok) {
      // Leer el error una sola vez
      const errorText = await response.text();
      console.error(`Error del backend: ${response.status} - ${errorText}`);
      // Retornar lista vacía en lugar de error para que el frontend no se rompa
      return NextResponse.json({ items: [] });
    }

    // Leer el body una sola vez
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Error conectando al backend:", error);
    // Retornar lista vacía en lugar de error
    return NextResponse.json({ items: [] });
  }
}


