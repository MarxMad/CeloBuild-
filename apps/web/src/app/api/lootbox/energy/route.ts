import { NextRequest, NextResponse } from "next/server";
import { spawn } from "child_process";

export const dynamic = 'force-dynamic';

export async function GET(req: NextRequest) {
    const searchParams = req.nextUrl.searchParams;
    const address = searchParams.get("address");

    if (!address) {
        return NextResponse.json({ error: "Address required" }, { status: 400 });
    }

    // Since EnergyService is in Python, we need a way to invoke it or read its JSON.
    // Reading JSON directly is risky due to concurrency/locking with the Python process.
    // However, for GET/Read operations, reading the JSON file might be acceptable if we tolerate slight inconsistency.
    // BUT the Python code uses a Lock. JavaScript accessing the file ignores that lock.

    // Better approach: Invoke a python script that imports the service and prints the status.
    // This re-uses the logic (including recharge calculation).

    // Wait, calling python for every poll is expensive.
    // Alternative: Re-implement the "Read" logic in TypeScript?
    // It's just JSON read + date math.
    // Format: { address: { last_consume_time: float, energy_consumed: int } }

    try {
        const fs = await import('fs/promises');
        const path = await import('path');
        // Assume path relative to the Next.js app... this is tricky in production/vercel.
        // But for local:
        const dataPath = path.resolve(process.cwd(), '../../apps/agents/data/energy_store.json');

        // Define constants matching Python
        const MAX_ENERGY = 3;
        const RECHARGE_TIME = 60 * 60; // 3600 seconds (60 minutes)

        let data: Record<string, any> = {};
        try {
            const fileContent = await fs.readFile(dataPath, 'utf-8');
            data = JSON.parse(fileContent);
        } catch (e) {
            // File might not exist yet -> Full Energy
        }

        const userState = data[address.toLowerCase()];

        if (!userState || !userState.consumed_bolts || userState.consumed_bolts.length === 0) {
            return NextResponse.json({
                current_energy: MAX_ENERGY,
                max_energy: MAX_ENERGY,
                next_refill_at: null,
                seconds_to_refill: 0
            });
        }

        const now = Date.now() / 1000;
        const consumedBolts: number[] = userState.consumed_bolts || [];

        // Filter out bolts that have already recharged (elapsed >= RECHARGE_TIME)
        const activeConsumed = consumedBolts.filter((boltTime: number) => {
            const elapsed = now - boltTime;
            return elapsed < RECHARGE_TIME;
        });

        const currentEnergy = MAX_ENERGY - activeConsumed.length;

        let secondsToRefill = 0;
        let nextRefillAt = null;

        if (activeConsumed.length > 0) {
            // Find the oldest consumed bolt (will recharge first)
            const oldestBoltTime = Math.min(...activeConsumed);
            const elapsed = now - oldestBoltTime;
            secondsToRefill = Math.max(0, Math.floor(RECHARGE_TIME - elapsed));
            nextRefillAt = oldestBoltTime + RECHARGE_TIME;
        }

        return NextResponse.json({
            current_energy: currentEnergy,
            max_energy: MAX_ENERGY,
            next_refill_at: nextRefillAt,
            seconds_to_refill: secondsToRefill
        });

    } catch (error) {
        console.error("Error reading energy:", error);
        return NextResponse.json({ error: "Internal Error" }, { status: 500 });
    }
}
