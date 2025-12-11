import { NextResponse } from "next/server";

export const dynamic = 'force-dynamic';

const AGENT_SERVICE_URL = process.env.AGENT_SERVICE_URL ?? process.env.NEXT_PUBLIC_AGENT_SERVICE_URL;

export async function POST(request: Request) {
    if (!AGENT_SERVICE_URL) {
        return NextResponse.json({ error: "Backend not configured" }, { status: 503 });
    }

    try {
        console.log(`Proxying POST to: ${AGENT_SERVICE_URL}/api/lootbox/leaderboard/sync`);

        const response = await fetch(`${AGENT_SERVICE_URL}/api/lootbox/leaderboard/sync`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.error(`Backend sync error: ${response.status} - ${errorText}`);
            return NextResponse.json({ error: errorText }, { status: response.status });
        }

        const data = await response.json();
        return NextResponse.json(data);
    } catch (error) {
        console.error("Proxy sync error:", error);
        return NextResponse.json({ error: "Internal Proxy Error" }, { status: 500 });
    }
}
