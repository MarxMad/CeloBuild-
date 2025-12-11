import { NextRequest, NextResponse } from "next/server";

const AGENT_SERVICE_URL = process.env.AGENT_SERVICE_URL ?? process.env.NEXT_PUBLIC_AGENT_SERVICE_URL;

export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
    if (!AGENT_SERVICE_URL) {
        return NextResponse.json({ items: [] });
    }

    try {
        const { searchParams } = new URL(request.url);
        const limit = searchParams.get("limit") || "5";

        const backendUrl = `${AGENT_SERVICE_URL}/api/lootbox/leaderboard?limit=${limit}`;
        const response = await fetch(backendUrl, {
            method: "GET",
            headers: { "Content-Type": "application/json" },
            cache: "no-store",
        });

        if (!response.ok) {
            return NextResponse.json({ items: [] });
        }

        const data = await response.json();
        return NextResponse.json(data);
    } catch (error) {
        console.error("Error proxying leaderboard request:", error);
        return NextResponse.json({ items: [] });
    }
}
