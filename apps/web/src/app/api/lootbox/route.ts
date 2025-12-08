import { NextResponse } from "next/server";
import type { LootboxEventPayload } from "@/lib/lootbox";

const AGENT_SERVICE_URL = process.env.AGENT_SERVICE_URL ?? process.env.NEXT_PUBLIC_AGENT_SERVICE_URL;

export async function POST(request: Request) {
  if (!AGENT_SERVICE_URL) {
    console.error("AGENT_SERVICE_URL no configurado");
    return NextResponse.json(
      { error: "Backend no configurado. Verifica AGENT_SERVICE_URL en variables de entorno." },
      { status: 500 }
    );
  }

  const payload = (await request.json()) as LootboxEventPayload;

  try {
    console.log(`Llamando al backend: ${AGENT_SERVICE_URL}/api/lootbox/run`);
    const response = await fetch(`${AGENT_SERVICE_URL}/api/lootbox/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        frame_id: payload.frameId,
        channel_id: payload.channelId,
        trend_score: payload.trendScore,
        thread_id: payload.threadId,
        target_address: payload.targetAddress,
        target_fid: payload.targetFid,
        reward_type: payload.rewardType,
      }),
    });

    if (!response.ok) {
      // Leer el error una sola vez
      let errorBody: any;
      const responseText = await response.text();
      try {
        errorBody = JSON.parse(responseText);
      } catch {
        errorBody = responseText;
      }
      
      console.error(`Error del backend: ${response.status} - ${JSON.stringify(errorBody)}`);
      
      // Si el error contiene "detail", extraerlo
      const errorMessage = errorBody?.detail || errorBody?.error || errorBody || `Error ${response.status}`;
      
      return NextResponse.json(
        { 
          error: typeof errorMessage === 'string' ? errorMessage : JSON.stringify(errorMessage),
          status: response.status,
          detail: errorBody
        },
        { status: response.status }
      );
    }

    // Leer el body una sola vez
    const result = await response.json();
    console.log("Respuesta del backend:", result);
    return NextResponse.json(result);
  } catch (error) {
    console.error("Error conectando al backend:", error);
    return NextResponse.json(
      { error: `Error de conexión: ${(error as Error).message}. Verifica que el backend esté corriendo en ${AGENT_SERVICE_URL}` },
      { status: 500 }
    );
  }
}

