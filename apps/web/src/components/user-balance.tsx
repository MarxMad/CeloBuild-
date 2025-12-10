"use client";

import { useAccount, useBalance } from "wagmi";
import { Card, CardContent } from "@/components/ui/card";
import { Wallet, CreditCard, Crown, User } from "lucide-react";
import { useEffect, useState } from "react";
import { useFarcasterUser } from "./farcaster-provider";
import { ConnectButton } from "@/components/connect-button";
import Link from "next/link";

const cUSD_ADDRESS = "0x765de816845861e75a25fca122bb6898b8b1282a";

function BalanceItem({ label, value, symbol }: { label: string; value: string; symbol: string }) {
    return (
        <div className="flex flex-col">
            <span className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold opacity-70">{label}</span>
            <div className="flex items-baseline gap-1">
                <span className="text-lg font-bold tracking-tight">{value}</span>
                <span className="text-xs font-medium text-muted-foreground">{symbol}</span>
            </div>
        </div>
    )
}

export function UserBalance() {
    const [mounted, setMounted] = useState(false);
    const { address, isConnected } = useAccount();
    const farcasterUser = useFarcasterUser();
    const [xp, setXp] = useState(0);
    const [rank, setRank] = useState<number | null>(null);

    // Evitar hydration mismatch
    useEffect(() => {
        setMounted(true);
    }, []);

    // Fetch XP
    useEffect(() => {
        if (address) {
            const fetchXp = async () => {
                try {
                    console.log(`🔍 Checking XP balance for ${address}...`);
                    const res = await fetch(`/api/lootbox/xp/${address}`);
                    if (res.ok) {
                        const data = await res.json();
                        const newXp = data.xp || 0;
                        setRank(data.rank || null);
                        console.log(`✅ XP Balance fetched: ${newXp}, Rank: ${data.rank}`);

                        setXp((prev) => {
                            if (newXp > prev) {
                                console.log(`🎉 XP Increased! ${prev} -> ${newXp}`);
                            }
                            return newXp;
                        });
                    }
                } catch (e) {
                    console.error("Error fetching XP:", e);
                }
            };

            fetchXp();
            // Poll XP every 10 seconds
            const interval = setInterval(fetchXp, 10000);

            // Listen for manual refresh events
            const handleRefresh = () => {
                console.log("Refreshing XP...");
                fetchXp();
                // Retry multiple times to account for blockchain latency (up to 20s)
                setTimeout(fetchXp, 2000);
                setTimeout(fetchXp, 5000);
                setTimeout(fetchXp, 10000);
                setTimeout(fetchXp, 15000);
                setTimeout(fetchXp, 20000);
            };
            window.addEventListener('refresh-xp', handleRefresh);

            return () => {
                clearInterval(interval);
                window.removeEventListener('refresh-xp', handleRefresh);
            };
        }
    }, [address]);

    // ... (useBalance hooks)
    const { data: celoBalance } = useBalance({
        address,
        query: {
            enabled: !!address, // Solo ejecutar si hay address
        }
    });

    const { data: cUSDBalance } = useBalance({
        address,
        token: cUSD_ADDRESS,
        query: {
            enabled: !!address,
        }
    });

    if (!mounted || !isConnected || !address) {
        return (
            <div className="flex justify-center mt-2 relative z-10">
                <div className="scale-105">
                    <ConnectButton />
                </div>
            </div>
        );
    }

    return (
        <Link href="/profile" className="block w-full cursor-pointer transition-transform hover:scale-[1.02] active:scale-[0.98]">
            <div className="w-full bg-background/60 backdrop-blur-xl rounded-2xl border shadow-sm p-4 hover:border-yellow-500/30 transition-colors">
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                        <div className="p-1.5 bg-primary/10 rounded-full">
                            {farcasterUser?.username ? (
                                <User className="w-3.5 h-3.5 text-primary" />
                            ) : (
                                <Wallet className="w-3.5 h-3.5 text-primary" />
                            )}
                        </div>
                        <div className="flex flex-col">
                            <span className="text-xs font-bold text-foreground">
                                {farcasterUser?.username ? `@${farcasterUser.username}` : "Wallet Conectada"}
                            </span>
                            <span className="text-[10px] font-mono text-muted-foreground truncate max-w-[100px]">
                                {address.slice(0, 6)}...{address.slice(-4)}
                            </span>
                        </div>
                    </div>
                    <div className="px-2 py-0.5 rounded-full bg-yellow-500/10 text-yellow-600 border border-yellow-500/20 text-[10px] font-bold uppercase flex items-center gap-1">
                        <Crown className="w-3 h-3" />
                        {xp} XP
                    </div>
                    {rank !== null && (
                        <div className="px-2 py-0.5 rounded-full bg-purple-500/10 text-purple-600 border border-purple-500/20 text-[10px] font-bold uppercase">
                            #{rank} Rank
                        </div>
                    )}
                    <div className="px-2 py-0.5 rounded-full bg-green-500/10 text-green-600 text-[10px] font-bold uppercase">
                        Active
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-2 gap-4 divide-x">
                <BalanceItem
                    label="Native"
                    value={parseFloat(celoBalance?.formatted || '0').toFixed(2)}
                    symbol="CELO"
                />
                <div className="pl-4">
                    <BalanceItem
                        label="Stable"
                        value={parseFloat(cUSDBalance?.formatted || '0').toFixed(2)}
                        symbol="cUSD"
                    />
                </div>
            </div>
        </div>
        </Link >
    );
}
