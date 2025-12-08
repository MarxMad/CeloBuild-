"use client";

import { Box, Coins, Crown, Sparkles, TrendingUp, User } from "lucide-react";
import { cn } from "@/lib/utils";
import type { LootboxEventPayload, AgentRunResponse } from "@/lib/lootbox";

type RewardType = NonNullable<LootboxEventPayload["rewardType"]>;

type RewardOption = {
  id: RewardType;
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
] as const;

export function RewardSelector({ 
  onSelect,
  userAnalysis,
  trendInfo
}: { 
  onSelect: (id: RewardType) => void | Promise<void>;
  userAnalysis?: AgentRunResponse["user_analysis"] | null;
  trendInfo?: AgentRunResponse["trend_info"] | null;
}) {
  return (
    <div className="space-y-6 animate-in fade-in zoom-in duration-500 max-w-sm w-full max-h-[90vh] overflow-y-auto">
      <div className="text-center space-y-2">
        <h3 className="text-2xl font-bold text-white">¡Eres Elegible! 🎉</h3>
        <p className="text-sm text-muted-foreground">
            Tus métricas de engagement son excelentes.<br/>Elige tu recompensa:
        </p>
      </div>

      {/* Análisis del Usuario */}
      {userAnalysis && (
        <div className="p-4 rounded-xl bg-white/5 border border-white/10 space-y-3">
          <div className="flex items-center gap-2 mb-2">
            <Sparkles className="w-4 h-4 text-[#FCFF52]" />
            <h5 className="text-sm font-bold text-foreground">Tu Análisis</h5>
          </div>
          
          {/* Username y Score */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <User className="w-3.5 h-3.5 text-muted-foreground" />
              <span className="text-xs text-muted-foreground">@</span>
              <span className="text-sm font-semibold text-foreground">
                {userAnalysis.username || "Usuario"}
              </span>
              {userAnalysis.power_badge && (
                <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-yellow-500/20 text-yellow-500 border border-yellow-500/30">
                  ⭐ Power
                </span>
              )}
            </div>
            {userAnalysis.score !== undefined && (
              <div className="text-sm font-mono font-bold text-[#FCFF52]">
                {userAnalysis.score.toFixed(1)} pts
              </div>
            )}
          </div>
          
          {/* Stats */}
          <div className="grid grid-cols-2 gap-2 text-xs">
            {userAnalysis.follower_count !== undefined && (
              <div className="flex items-center gap-1.5">
                <span className="text-muted-foreground">Followers:</span>
                <span className="font-semibold text-foreground">{userAnalysis.follower_count}</span>
              </div>
            )}
            {userAnalysis.participation?.total_engagement !== undefined && (
              <div className="flex items-center gap-1.5">
                <span className="text-muted-foreground">Engagement:</span>
                <span className="font-semibold text-foreground">
                  {userAnalysis.participation.total_engagement.toFixed(1)}
                </span>
              </div>
            )}
          </div>
          
          {/* Reasons */}
          {userAnalysis.reasons && userAnalysis.reasons.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {userAnalysis.reasons.map((reason, idx) => (
                <span
                  key={idx}
                  className="text-[9px] px-2 py-0.5 rounded-full bg-[#FCFF52]/10 text-[#FCFF52] border border-[#FCFF52]/20 uppercase"
                >
                  {reason}
                </span>
              ))}
            </div>
          )}
          
          {/* Participación */}
          {userAnalysis.participation?.directly_participated && (
            <div className="text-[10px] text-green-400 flex items-center gap-1">
              <span>✓</span>
              <span>Participaste en esta tendencia</span>
            </div>
          )}
        </div>
      )}

      {/* Información de la Tendencia */}
      {trendInfo && (
        <div className="p-3 rounded-lg bg-white/5 border border-white/10 space-y-2">
          <div className="flex items-center gap-2">
            <TrendingUp className="w-3 h-3 text-[#FCFF52]" />
            <span className="text-xs font-bold text-[#FCFF52] uppercase">Tendencia Detectada</span>
            {trendInfo.trend_score !== undefined && (
              <span className="text-[10px] font-mono text-muted-foreground ml-auto">
                {(trendInfo.trend_score * 100).toFixed(0)}%
              </span>
            )}
          </div>
          {trendInfo.source_text && (
            <p className="text-xs text-foreground line-clamp-2">
              {trendInfo.source_text}
            </p>
          )}
          {trendInfo.ai_analysis && (
            <div className="space-y-1">
              <div className="flex items-center gap-1.5">
                <span className="text-[10px] text-muted-foreground italic line-clamp-2">
                  💡 {trendInfo.ai_analysis}
                </span>
                {trendInfo.ai_enabled !== undefined && (
                  <span className={`text-[8px] px-1.5 py-0.5 rounded-full font-bold ${
                    trendInfo.ai_enabled 
                      ? "bg-purple-500/20 text-purple-400 border border-purple-500/30" 
                      : "bg-gray-500/20 text-gray-400 border border-gray-500/30"
                  }`}>
                    {trendInfo.ai_enabled ? "🤖 AI" : "📊 Básico"}
                  </span>
                )}
              </div>
            </div>
          )}
          {trendInfo.topic_tags && trendInfo.topic_tags.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {trendInfo.topic_tags.slice(0, 3).map((tag) => (
                <span
                  key={tag}
                  className="text-[9px] px-1.5 py-0.5 rounded-full bg-white/5 text-muted-foreground border border-white/10"
                >
                  #{tag}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

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
