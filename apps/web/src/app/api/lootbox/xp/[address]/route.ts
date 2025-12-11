import { NextResponse } from "next/server";

const AGENT_SERVICE_URL = process.env.AGENT_SERVICE_URL ?? process.env.NEXT_PUBLIC_AGENT_SERVICE_URL;

export async function GET(
    request: Request,
    { params }: { params: { address: string } }
) {
    if (!AGENT_SERVICE_URL) {
        return NextResponse.json(
            { error: "Backend configuration missing" },
            { status: 500 }
        );
    }

    const address = params.address;

    try {
        const backendUrl = `${AGENT_SERVICE_URL}/api/lootbox/xp/${address}`;
        console.log(`[XP Proxy] Requesting: ${backendUrl}`);

        const response = await fetch(backendUrl, {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
            },
            cache: "no-store",
        });

        console.log(`[XP Proxy] Backend status: ${response.status}`);

        if (!response.ok) {
            const errorText = await response.text();
            console.error(`[XP Proxy] Error body: ${errorText}`);

            let errorJson;
            try {
                errorJson = JSON.parse(errorText);
            } catch {
                errorJson = { detail: errorText };
            }

            return NextResponse.json(
                {
                    error: `Failed to fetch XP from backend (Status ${response.status})`,
                    backend_error: errorJson,
                    url: backendUrl // DEBUG: Expose URL to frontend for verification
                },
                { status: response.status }
            );
        }

        const data = await response.json();
        return NextResponse.json(data);
    } catch (error) {
        console.error("Error proxying XP request:", error);
        return NextResponse.json(
            { error: "Internal Server Error" },
            { status: 500 }
        );
    }
}
