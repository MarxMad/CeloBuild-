import { NextResponse } from "next/server";
import type { LootboxEventPayload } from "@/lib/lootbox";

const AGENT_SERVICE_URL = process.env.AGENT_SERVICE_URL ?? process.env.NEXT_PUBLIC_AGENT_SERVICE_URL;

export async function POST(request: Request) {
  if (!AGENT_SERVICE_URL) {
    return NextResponse.json({ error: "AGENT_SERVICE_URL no configurado" }, { status: 500 });
  }

  const payload = (await request.json()) as LootboxEventPayload;

  try {
    const response = await fetch(`${AGENT_SERVICE_URL}/api/lootbox/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        frame_id: payload.frameId,
        channel_id: payload.channelId,
        trend_score: payload.trendScore,
        thread_id: payload.threadId,
        target_address: payload.targetAddress,
      }),
    });

    if (!response.ok) {
      const errorBody = await response.text();
      return NextResponse.json({ error: errorBody || "Agente respondió con error" }, { status: response.status });
    }

    return NextResponse.json(await response.json());
  } catch (error) {
    return NextResponse.json({ error: (error as Error).message }, { status: 500 });
  }
}
