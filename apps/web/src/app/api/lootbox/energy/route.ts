import { NextRequest, NextResponse } from "next/server";

export const dynamic = 'force-dynamic';

const AGENT_SERVICE_URL = process.env.AGENT_SERVICE_URL ?? process.env.NEXT_PUBLIC_AGENT_SERVICE_URL;

export async function GET(req: NextRequest) {
    const searchParams = req.nextUrl.searchParams;
    const address = searchParams.get("address");

    if (!address) {
        return NextResponse.json({ error: "Address required" }, { status: 400 });
    }

    if (!AGENT_SERVICE_URL) {
        console.error("[Energy Proxy] AGENT_SERVICE_URL not configured");
        // Fallback: return full energy if backend not configured
        return NextResponse.json({
            current_energy: 3,
            max_energy: 3,
            next_refill_at: null,
            seconds_to_refill: 0
        });
    }

    try {
        const backendUrl = `${AGENT_SERVICE_URL}/api/lootbox/energy?address=${encodeURIComponent(address)}`;
        console.log(`[Energy Proxy] Requesting: ${backendUrl}`);

        const response = await fetch(backendUrl, {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
            },
            cache: "no-store",
        });

        console.log(`[Energy Proxy] Backend status: ${response.status}`);

        if (!response.ok) {
            const errorText = await response.text();
            console.error(`[Energy Proxy] Error body: ${errorText}`);
            
            // Fallback: return full energy if backend error
            return NextResponse.json({
                current_energy: 3,
                max_energy: 3,
                next_refill_at: null,
                seconds_to_refill: 0
            });
        }

        const data = await response.json();
        console.log(`[Energy Proxy] Energy status:`, data);
        return NextResponse.json(data);
    } catch (error) {
        console.error("[Energy Proxy] Error proxying energy request:", error);
        // Fallback: return full energy on error
        return NextResponse.json({
            current_energy: 3,
            max_energy: 3,
            next_refill_at: null,
            seconds_to_refill: 0
        });
    }
}
