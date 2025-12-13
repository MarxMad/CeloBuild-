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
        const bolts = Array.from({ length: 3 }).map((_, i) => ({
            index: i,
            available: true,
            seconds_to_refill: 0,
            refill_at: null
        }));
        return NextResponse.json({
            current_energy: 3,
            max_energy: 3,
            next_refill_at: null,
            seconds_to_refill: 0,
            bolts: bolts
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
            const bolts = Array.from({ length: 3 }).map((_, i) => ({
                index: i,
                available: true,
                seconds_to_refill: 0,
                refill_at: null
            }));
            return NextResponse.json({
                current_energy: 3,
                max_energy: 3,
                next_refill_at: null,
                seconds_to_refill: 0,
                bolts: bolts
            });
        }

        const data = await response.json();
        console.log(`[Energy Proxy] Energy status:`, data);
        
        // Asegurar que bolts esté presente
        if (!data.bolts) {
          // Si el backend no devuelve bolts, crear array básico
          const bolts = [];
          for (let i = 0; i < (data.max_energy || 3); i++) {
            bolts.push({
              index: i,
              available: i < (data.current_energy || 0),
              seconds_to_refill: i === data.current_energy ? (data.seconds_to_refill || 0) : 0,
              refill_at: i === data.current_energy && data.next_refill_at ? data.next_refill_at : null
            });
          }
          data.bolts = bolts;
        }
        
        return NextResponse.json(data);
    } catch (error) {
        console.error("[Energy Proxy] Error proxying energy request:", error);
        // Fallback: return full energy on error
        const bolts = Array.from({ length: 3 }).map((_, i) => ({
            index: i,
            available: true,
            seconds_to_refill: 0,
            refill_at: null
        }));
        return NextResponse.json({
            current_energy: 3,
            max_energy: 3,
            next_refill_at: null,
            seconds_to_refill: 0,
            bolts: bolts
        });
    }
}
