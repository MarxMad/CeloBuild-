import { NextResponse } from "next/server";

const AGENT_SERVICE_URL = process.env.AGENT_SERVICE_URL ?? process.env.NEXT_PUBLIC_AGENT_SERVICE_URL;

export async function POST(request: Request) {
    if (!AGENT_SERVICE_URL) {
        console.error("AGENT_SERVICE_URL no configurado");
        return NextResponse.json({ error: "Backend configuration missing" }, { status: 500 });
    }

    try {
        const payload = await request.json();
        const backendUrl = `${AGENT_SERVICE_URL}/api/webhook`;

        console.log(`[WEBHOOK] Forwarding to backend: ${backendUrl}`);

        const response = await fetch(backendUrl, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });

        if (!response.ok) {
            console.error(`[WEBHOOK] Backend error: ${response.status}`);
            return NextResponse.json({ error: "Backend processing failed" }, { status: response.status });
        }

        const result = await response.json();
        return NextResponse.json(result);
    } catch (error) {
        console.error("[WEBHOOK] Proxy error:", error);
        return NextResponse.json({ error: "Internal Server Error" }, { status: 500 });
    }
}
