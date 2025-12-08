import { NextResponse } from "next/server";

const AGENT_SERVICE_URL = process.env.AGENT_SERVICE_URL ?? process.env.NEXT_PUBLIC_AGENT_SERVICE_URL;

export async function POST(request: Request) {
    if (!AGENT_SERVICE_URL) {
        return NextResponse.json(
            { error: "Backend configuration missing" },
            { status: 500 }
        );
    }

    try {
        const backendUrl = `${AGENT_SERVICE_URL}/api/lootbox/scan`;
        console.log("[SCAN] Triggering manual scan:", backendUrl);

        const response = await fetch(backendUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            cache: "no-store",
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.error(`[SCAN] Backend error: ${response.status} - ${errorText}`);
            return NextResponse.json(
                { error: "Failed to trigger scan" },
                { status: response.status }
            );
        }

        const data = await response.json();
        return NextResponse.json(data);
    } catch (error) {
        console.error("[SCAN] Error proxying scan request:", error);
        return NextResponse.json(
            { error: "Internal Server Error" },
            { status: 500 }
        );
    }
}
