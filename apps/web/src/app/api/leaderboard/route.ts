import { NextResponse } from "next/server";

const AGENT_SERVICE_URL = process.env.AGENT_SERVICE_URL ?? process.env.NEXT_PUBLIC_AGENT_SERVICE_URL;

export async function GET(request: Request) {
  if (!AGENT_SERVICE_URL) {
    return NextResponse.json({ error: "AGENT_SERVICE_URL no configurado" }, { status: 500 });
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
      const body = await response.text();
      return NextResponse.json({ error: body || "Error en leaderboard" }, { status: response.status });
    }

    return NextResponse.json(await response.json());
  } catch (error) {
    return NextResponse.json({ error: (error as Error).message }, { status: 500 });
  }
}


