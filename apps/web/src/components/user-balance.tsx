"use client";

import { useAccount, useBalance } from "wagmi";
import { Card, CardContent } from "@/components/ui/card";
import { Wallet, CreditCard } from "lucide-react";
import { useEffect, useState } from "react";

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

import { ConnectButton } from "@/components/connect-button";

// ... (previous imports)

export function UserBalance() {
  const [mounted, setMounted] = useState(false);
  const { address, isConnected } = useAccount();
  
  // Evitar hydration mismatch
  useEffect(() => {
    setMounted(true);
  }, []);

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
    // ... (rest of the component)
    <div className="w-full bg-background/60 backdrop-blur-xl rounded-2xl border shadow-sm p-4">
        <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
                <div className="p-1.5 bg-primary/10 rounded-full">
                    <Wallet className="w-3.5 h-3.5 text-primary" />
                </div>
                <span className="text-xs font-mono text-muted-foreground truncate max-w-[100px]">
                    {address.slice(0, 6)}...{address.slice(-4)}
                </span>
            </div>
            <div className="px-2 py-0.5 rounded-full bg-green-500/10 text-green-600 text-[10px] font-bold uppercase">
                Active
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
  );
}
