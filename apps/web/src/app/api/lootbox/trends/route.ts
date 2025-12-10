import { NextResponse } from "next/server";

const AGENT_SERVICE_URL = process.env.AGENT_SERVICE_URL ?? process.env.NEXT_PUBLIC_AGENT_SERVICE_URL;

export async function GET(request: Request) {
    if (!AGENT_SERVICE_URL) {
        return NextResponse.json({ items: [] });
    }

    try {
        const { searchParams } = new URL(request.url);
        const limit = searchParams.get("limit") || "10";

        const backendUrl = `${AGENT_SERVICE_URL}/api/lootbox/trends?limit=${limit}`;
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
        console.error("Error proxying trends request:", error);
        return NextResponse.json({ items: [] });
    }
}
