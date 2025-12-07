"use client";

import { Box, Coins, Crown } from "lucide-react";
import { cn } from "@/lib/utils";

type RewardOption = {
  id: string;
  title: string;
  value: string;
  icon: any;
  color: string;
  bg: string;
};

const OPTIONS: RewardOption[] = [
  {
    id: "nft",
    title: "Rare NFT",
    value: "Gen 1 Badge",
    icon: Box,
    color: "text-purple-400",
    bg: "bg-purple-500/10 border-purple-500/20",
  },
  {
    id: "cusd",
    title: "cUSD Drop",
    value: "$0.50 cUSD",
    icon: Coins,
    color: "text-green-400",
    bg: "bg-green-500/10 border-green-500/20",
  },
  {
    id: "xp",
    title: "Reputation",
    value: "+100 XP",
    icon: Crown,
    color: "text-yellow-400",
    bg: "bg-yellow-500/10 border-yellow-500/20",
  },
];

export function RewardSelector({ onSelect }: { onSelect: (id: string) => void }) {
  return (
    <div className="space-y-6 animate-in fade-in zoom-in duration-500 max-w-sm w-full">
      <div className="text-center space-y-2">
        <h3 className="text-2xl font-bold text-white">¡Eres Elegible! 🎉</h3>
        <p className="text-sm text-muted-foreground">
            Tus métricas de engagement son excelentes.<br/>Elige tu recompensa:
        </p>
      </div>

      <div className="grid gap-4 relative z-50">
        {OPTIONS.map((opt) => (
          <button
            key={opt.id}
            onClick={(e) => {
                // Prevenir propagación para evitar cierres accidentales
                e.stopPropagation();
                e.preventDefault();
                onSelect(opt.id);
            }}
            className={cn(
              "flex items-center gap-4 p-4 rounded-xl border transition-all hover:scale-[1.02] active:scale-95 text-left cursor-pointer z-50 shadow-lg relative bg-background/80 backdrop-blur-md",
              opt.bg
            )}
          >
            <div className={cn("p-3 rounded-full bg-black/20", opt.color)}>
                <opt.icon className="w-6 h-6" />
            </div>
            <div>
                <div className="font-bold text-lg text-white">{opt.value}</div>
                <div className="text-xs text-muted-foreground uppercase tracking-wider font-semibold">{opt.title}</div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
