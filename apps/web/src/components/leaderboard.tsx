"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Trophy, TrendingUp } from "lucide-react";

type LeaderboardEntry = {
  username?: string;
  address: string;
  score: number;
  reward_type?: string;
  tx_hash?: string;
  topic_tags?: string[];
};

type TrendItem = { tag: string; posts: number };

const rewardLabel: Record<string, string> = {
  nft: "Loot NFT",
  cusd: "MiniPay Drop",
  xp: "XP Boost",
  pending: "Pendiente",
};

type TrendData = {
  frame_id?: string;
  cast_hash?: string;
  trend_score?: number;
  source_text?: string;
  ai_analysis?: string;
  topic_tags?: string[];
  channel_id?: string;
  timestamp?: number;
};

export function Leaderboard() {
  const [entries, setEntries] = useState<LeaderboardEntry[]>([]);
  const [activeTrends, setActiveTrends] = useState<TrendItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fetch leaderboard y trends en paralelo
        const [leaderboardResp, trendsResp] = await Promise.all([
          fetch("/api/leaderboard?limit=5", { cache: "no-store" }),
          fetch("/api/trends?limit=10", { cache: "no-store" }),
        ]);

        // Procesar leaderboard
        if (leaderboardResp.ok) {
          const leaderboardData = await leaderboardResp.json();
          const items = (leaderboardData.items ?? []) as LeaderboardEntry[];
          setEntries(items);
        }

        // Procesar trends
        if (trendsResp.ok) {
          const trendsData = await trendsResp.json();
          const trends = (trendsData.items ?? []) as TrendData[];
          
          // Construir tendencias activas desde los trends detectados
          const trendSummary = buildTrendSummaryFromTrends(trends);
          if (trendSummary.length > 0) {
            setActiveTrends(trendSummary);
          } else {
            // Fallback: usar topic_tags del leaderboard si no hay trends recientes
            const leaderboardData = await leaderboardResp.json();
            const items = (leaderboardData.items ?? []) as LeaderboardEntry[];
            setActiveTrends(buildTrendSummary(items));
          }
        } else {
          // Fallback: usar leaderboard si trends falla
          const leaderboardData = await leaderboardResp.json();
          const items = (leaderboardData.items ?? []) as LeaderboardEntry[];
          setActiveTrends(buildTrendSummary(items));
        }
      } catch (error) {
        console.error(error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  return (
    <div className="grid gap-6 md:grid-cols-2 animate-in fade-in slide-in-from-bottom-8 duration-700">
      <Card className="bg-white/5 border-white/10 backdrop-blur-sm">
        <CardHeader className="pb-3">
          <div className="flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-[#FCFF52]" />
            <CardTitle className="text-sm font-bold uppercase tracking-wider text-muted-foreground">
              Tendencias Activas
            </CardTitle>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          {loading && <div className="text-xs text-muted-foreground">Escaneando Farcaster...</div>}
          {!loading && activeTrends.length === 0 && (
            <div className="text-xs text-muted-foreground">Sin tendencias recientes.</div>
          )}
          {activeTrends.map((trend) => (
            <div
              key={trend.tag}
              className="flex items-center justify-between p-3 rounded-xl bg-white/5 hover:bg-white/10 transition-colors border border-transparent hover:border-[#FCFF52]/30"
            >
              <div>
                <div className="font-bold text-sm text-foreground">#{trend.tag}</div>
                <div className="text-[10px] text-muted-foreground">{trend.posts} señales</div>
              </div>
              <div className="text-[10px] uppercase font-bold text-[#FCFF52] bg-[#FCFF52]/10 px-2 py-1 rounded-full">
                Loot activo
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      <Card className="bg-white/5 border-white/10 backdrop-blur-sm">
        <CardHeader className="pb-3">
          <div className="flex items-center gap-2">
            <Trophy className="w-4 h-4 text-yellow-500" />
            <CardTitle className="text-sm font-bold uppercase tracking-wider text-muted-foreground">
              Top Ganadores (24h)
            </CardTitle>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          {loading && (
            <div className="text-xs text-muted-foreground">Compilando registros on-chain...</div>
          )}
          {!loading && entries.length === 0 && (
            <div className="text-xs text-muted-foreground">Aún no hay ganadores.</div>
          )}
          {entries.map((winner, index) => (
            <div key={`${winner.address}-${index}`} className="flex items-center justify-between p-2">
              <div className="flex items-center gap-3">
                <div
                  className={`w-6 h-6 flex items-center justify-center rounded-full text-xs font-bold ${
                    index === 0
                      ? "bg-yellow-500 text-black"
                      : index === 1
                      ? "bg-gray-400 text-black"
                      : index === 2
                      ? "bg-orange-700 text-white"
                      : "bg-white/10 text-muted-foreground"
                  }`}
                >
                  {index + 1}
                </div>
                <div className="flex flex-col">
                  <span className="text-sm font-medium">
                    {winner.username ?? winner.address.slice(0, 6)}
                  </span>
                  <span className="text-[10px] text-muted-foreground uppercase tracking-wider">
                    {rewardLabel[winner.reward_type ?? "pending"] ?? "Pendiente"}
                  </span>
                </div>
              </div>
              <div className="text-right">
                <span className="text-xs font-mono text-[#FCFF52]">{Number(winner.score ?? 0).toFixed(0)} pts</span>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}

function buildTrendSummary(entries: LeaderboardEntry[]): TrendItem[] {
  const counter = new Map<string, number>();
  entries.forEach((entry) => {
    entry.topic_tags?.forEach((tag) => {
      counter.set(tag, (counter.get(tag) ?? 0) + 1);
    });
  });
  return Array.from(counter.entries())
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3)
    .map(([tag, posts]) => ({ tag, posts }));
}

function buildTrendSummaryFromTrends(trends: TrendData[]): TrendItem[] {
  const counter = new Map<string, number>();
  trends.forEach((trend) => {
    trend.topic_tags?.forEach((tag) => {
      counter.set(tag, (counter.get(tag) ?? 0) + 1);
    });
  });
  return Array.from(counter.entries())
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3)
    .map(([tag, posts]) => ({ tag, posts }));
}

