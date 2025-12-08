"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Trophy, TrendingUp, Sparkles, MessageSquare, RefreshCw } from "lucide-react";

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
  author_username?: string;
  author_fid?: number;
};

export function Leaderboard() {
  const [entries, setEntries] = useState<LeaderboardEntry[]>([]);
  const [activeTrends, setActiveTrends] = useState<TrendItem[]>([]);
  const [trendDetails, setTrendDetails] = useState<TrendData[]>([]);
  const [loading, setLoading] = useState(true);
  const [isScanning, setIsScanning] = useState(false);
  const [cooldownRemaining, setCooldownRemaining] = useState<number | null>(null);

  // Check cooldown on mount
  useEffect(() => {
    const lastScan = localStorage.getItem("lastTrendScanTime");
    if (lastScan) {
      const elapsed = Date.now() - parseInt(lastScan);
      const sixHours = 6 * 60 * 60 * 1000;
      if (elapsed < sixHours) {
        setCooldownRemaining(sixHours - elapsed);
      }
    }
  }, []);

  // Update cooldown timer
  useEffect(() => {
    if (cooldownRemaining !== null && cooldownRemaining > 0) {
      const interval = setInterval(() => {
        setCooldownRemaining((prev) => {
          if (prev === null || prev <= 1000) return null;
          return prev - 1000;
        });
      }, 1000);
      return () => clearInterval(interval);
    }
  }, [cooldownRemaining]);

  const handleRefresh = async () => {
    if (cooldownRemaining !== null) return;

    setIsScanning(true);
    try {
      const res = await fetch("/api/lootbox/scan", { method: "POST" });
      if (res.ok) {
        localStorage.setItem("lastTrendScanTime", Date.now().toString());
        setCooldownRemaining(6 * 60 * 60 * 1000);
        // Reload data after a short delay to allow backend to save
        setTimeout(() => {
          // Force reload by triggering the fetch effect (or manually calling fetch)
          window.location.reload(); // Simple way to refresh everything
        }, 2000);
      }
    } catch (e) {
      console.error("Scan failed", e);
    } finally {
      setIsScanning(false);
    }
  };

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fetch leaderboard y trends en paralelo
        const [leaderboardResp, trendsResp] = await Promise.all([
          fetch("/api/leaderboard?limit=5", { cache: "no-store" }),
          fetch("/api/trends?limit=5", { cache: "no-store" }),
        ]);

        // Procesar leaderboard y guardar datos para reutilizar
        let leaderboardItems: LeaderboardEntry[] = [];
        if (leaderboardResp.ok) {
          const leaderboardData = await leaderboardResp.json();
          leaderboardItems = (leaderboardData.items ?? []) as LeaderboardEntry[];
          setEntries(leaderboardItems);
        }

        // Procesar trends
        if (trendsResp.ok) {
          const trendsData = await trendsResp.json();
          const trends = (trendsData.items ?? []) as TrendData[];

          // Guardar detalles completos de tendencias
          setTrendDetails(trends);

          // Construir tendencias activas desde los trends detectados
          const trendSummary = buildTrendSummaryFromTrends(trends);
          if (trendSummary.length > 0) {
            setActiveTrends(trendSummary);
          } else {
            // Fallback: usar topic_tags del leaderboard si no hay trends recientes
            setActiveTrends(buildTrendSummary(leaderboardItems));
          }
        } else {
          // Fallback: usar leaderboard si trends falla
          setActiveTrends(buildTrendSummary(leaderboardItems));
        }
      } catch (error) {
        console.error(error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();

    // Refrescar cada 30 segundos
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  // Obtener hasta 5 tendencias más recientes
  const topTrends = trendDetails.slice(0, 5);

  return (
    <div className="grid gap-4 sm:gap-6 md:grid-cols-2 animate-in fade-in slide-in-from-bottom-8 duration-700">
      <Card className="bg-white/5 border-white/10 backdrop-blur-sm">
        <CardHeader className="pb-2 sm:pb-3 px-3 sm:px-6">
          <div className="flex items-center justify-between w-full">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-[#FCFF52] flex-shrink-0" />
              <CardTitle className="text-xs sm:text-sm font-bold uppercase tracking-wider text-muted-foreground">
                Tendencias Activas
              </CardTitle>
            </div>
            <button
              onClick={handleRefresh}
              disabled={isScanning || cooldownRemaining !== null}
              className="p-1.5 rounded-full hover:bg-white/10 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              title={cooldownRemaining ? `Disponible en ${Math.ceil(cooldownRemaining / (1000 * 60 * 60))}h` : "Actualizar Tendencias"}
            >
              <RefreshCw className={`w-3.5 h-3.5 text-muted-foreground ${isScanning ? "animate-spin" : ""}`} />
            </button>
          </div>
        </CardHeader>
        <CardContent className="space-y-2 sm:space-y-3 px-3 sm:px-6 pb-4 sm:pb-6 max-h-[600px] sm:max-h-[700px] overflow-y-auto scrollbar-thin scrollbar-thumb-[#FCFF52]/20 scrollbar-track-transparent">
          {loading && (
            <div className="text-[10px] sm:text-xs text-muted-foreground text-center py-2">
              Escaneando Farcaster...
            </div>
          )}
          {!loading && topTrends.length === 0 && (
            <div className="text-[10px] sm:text-xs text-muted-foreground text-center py-2">
              Sin tendencias recientes.
            </div>
          )}

          {/* Mostrar hasta 5 tendencias con detalles - Responsive */}
          {!loading && topTrends.map((trend, index) => (
            <div
              key={trend.frame_id || trend.cast_hash || index}
              className={`p-2.5 sm:p-3 rounded-lg sm:rounded-xl border mb-2 transition-all hover:scale-[1.01] ${index === 0
                  ? "bg-gradient-to-br from-[#FCFF52]/10 to-transparent border-[#FCFF52]/20 shadow-sm"
                  : "bg-white/5 border-white/10"
                }`}
            >
              {/* Header con score */}
              <div className="flex items-start justify-between gap-2 mb-1.5 sm:mb-2 flex-wrap">
                <div className="flex items-center gap-1.5 sm:gap-2 flex-shrink-0">
                  {index === 0 && (
                    <Sparkles className="w-3 h-3 sm:w-3.5 sm:h-3.5 text-[#FCFF52] flex-shrink-0" />
                  )}
                  <span className="text-[9px] sm:text-[10px] uppercase font-bold text-[#FCFF52] whitespace-nowrap">
                    #{index + 1} Trend
                  </span>
                </div>
                {trend.trend_score !== undefined && (
                  <div className="text-[9px] sm:text-[10px] font-mono text-[#FCFF52] bg-[#FCFF52]/10 px-1.5 sm:px-2 py-0.5 rounded-full flex-shrink-0">
                    {(trend.trend_score * 100).toFixed(0)}%
                  </div>
                )}
              </div>

              {/* Autor */}
              {trend.author_username && (
                <div className="mb-1 sm:mb-1.5">
                  <span className="text-[9px] sm:text-[10px] text-muted-foreground">Por </span>
                  <span className="text-[9px] sm:text-[10px] font-semibold text-foreground break-words">
                    @{trend.author_username}
                  </span>
                </div>
              )}

              {/* Texto del cast */}
              {trend.source_text && (
                <div className="mb-1 sm:mb-1.5">
                  <div className="flex items-start gap-1.5 sm:gap-2">
                    <MessageSquare className="w-2.5 h-2.5 sm:w-3 sm:h-3 text-muted-foreground mt-0.5 flex-shrink-0" />
                    <p className="text-[10px] sm:text-xs text-foreground line-clamp-2 sm:line-clamp-3 break-words">
                      {trend.source_text}
                    </p>
                  </div>
                </div>
              )}

              {/* Análisis IA (solo para #1) */}
              {trend.ai_analysis && index === 0 && (
                <div className="mb-1 sm:mb-1.5 p-1.5 sm:p-2 rounded-md sm:rounded-lg bg-white/5 border border-white/10">
                  <p className="text-[9px] sm:text-[10px] text-muted-foreground italic line-clamp-2 break-words">
                    💡 {trend.ai_analysis}
                  </p>
                </div>
              )}

              {/* Tags */}
              {trend.topic_tags && trend.topic_tags.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-1 sm:mt-1.5">
                  {trend.topic_tags.slice(0, 3).map((tag) => (
                    <span
                      key={tag}
                      className="text-[8px] sm:text-[9px] px-1.5 sm:px-2 py-0.5 rounded-full bg-white/5 text-muted-foreground border border-white/10 whitespace-nowrap"
                    >
                      #{tag}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}

          {/* Tags de tendencias activas - Responsive */}
          {activeTrends.map((trend) => (
            <div
              key={trend.tag}
              className="flex items-center justify-between p-2 sm:p-3 rounded-lg sm:rounded-xl bg-white/5 hover:bg-white/10 transition-all border border-transparent hover:border-[#FCFF52]/30 hover:scale-[1.02]"
            >
              <div className="min-w-0 flex-1">
                <div className="font-bold text-xs sm:text-sm text-foreground truncate">
                  #{trend.tag}
                </div>
                <div className="text-[9px] sm:text-[10px] text-muted-foreground">
                  {trend.posts} señales
                </div>
              </div>
              <div className="text-[9px] sm:text-[10px] uppercase font-bold text-[#FCFF52] bg-[#FCFF52]/10 px-1.5 sm:px-2 py-0.5 sm:py-1 rounded-full flex-shrink-0 ml-2">
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
                  className={`w-6 h-6 flex items-center justify-center rounded-full text-xs font-bold ${index === 0
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

