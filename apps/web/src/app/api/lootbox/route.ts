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
      const errorBody = await response.text();
      console.error(`Error del backend: ${response.status} - ${errorBody}`);
      return NextResponse.json(
        { error: errorBody || `Agente respondió con error ${response.status}` },
        { status: response.status }
      );
    }

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

