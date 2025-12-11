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
        const body = await request.json();
        const backendUrl = `${AGENT_SERVICE_URL}/api/lootbox/verify-recharge`;

        console.log(`Proxying verify-recharge to: ${backendUrl}`);

        const response = await fetch(backendUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(body),
            cache: "no-store",
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.error(`Backend returned error ${response.status}: ${errorText}`);
            return NextResponse.json(
                { error: "Backend Error", detail: errorText },
                { status: response.status }
            );
        }

        const data = await response.json();
        return NextResponse.json(data);
    } catch (error) {
        console.error("Error proxying verify-recharge request:", error);
        return NextResponse.json(
            { error: "Internal Server Error" },
            { status: 500 }
        );
    }
}
