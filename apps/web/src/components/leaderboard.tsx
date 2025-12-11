"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Trophy, TrendingUp, Sparkles, MessageSquare, RefreshCw, ExternalLink } from "lucide-react";
import { useLanguage } from "@/components/language-provider";

type LeaderboardEntry = {
  username?: string;
  address: string;
  score: number;
  xp?: number;
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
  const { t } = useLanguage();
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

  // Load cached data on mount
  useEffect(() => {
    try {
      const cachedEntries = localStorage.getItem("leaderboard_entries");
      if (cachedEntries) {
        setEntries(JSON.parse(cachedEntries));
        setLoading(false);
      }

      const cachedTrends = localStorage.getItem("leaderboard_trends");
      if (cachedTrends) {
        setActiveTrends(JSON.parse(cachedTrends));
      }

      const cachedTrendDetails = localStorage.getItem("leaderboard_trend_details");
      if (cachedTrendDetails) {
        setTrendDetails(JSON.parse(cachedTrendDetails));
      }
    } catch (e) {
      console.warn("Error loading cache", e);
    }
  }, []);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Smart Caching Logic (12h)
        // Only fetch if data is stale or missing
        const lastFetch = localStorage.getItem("leaderboard_last_fetch");
        const now = Date.now();
        const twelveHours = 12 * 60 * 60 * 1000;

        const hasCachedEntries = !!localStorage.getItem("leaderboard_entries");
        const hasCachedTrends = !!localStorage.getItem("leaderboard_trends");

        // If we have data and it's fresh enough (less than 12h old), skip fetch
        if (lastFetch && (now - parseInt(lastFetch) < twelveHours) && hasCachedEntries && hasCachedTrends) {
          console.log("Using cached dashboard data (fresh < 12h)");
          setLoading(false);
          return;
        }

        console.log("Fetching fresh dashboard data...");
        // Fetch leaderboard y trends en paralelo
        const [leaderboardResp, trendsResp] = await Promise.all([
          fetch("/api/lootbox/leaderboard?limit=30", { cache: "no-store" }),
          fetch("/api/lootbox/trends?limit=5", { cache: "no-store" }),
        ]);

        // Success flag
        let success = false;

        // Procesar leaderboard y guardar datos para reutilizar
        let leaderboardItems: LeaderboardEntry[] = [];
        if (leaderboardResp.ok) {
          const leaderboardData = await leaderboardResp.json();
          leaderboardItems = (leaderboardData.items ?? []) as LeaderboardEntry[];

          // Deduplicate items by address (frontend safety net)
          const uniqueItems = Array.from(
            new Map(leaderboardItems.map(item => [item.address.toLowerCase(), item])).values()
          );

          if (uniqueItems.length > 0) {
            setEntries(uniqueItems);
            localStorage.setItem("leaderboard_entries", JSON.stringify(uniqueItems));
            success = true;
          }
        }

        // Procesar trends
        let trendsData: { items: TrendData[] } | null = null;
        if (trendsResp.ok) {
          trendsData = await trendsResp.json();
          const trends = (trendsData?.items ?? []) as TrendData[];

          // Guardar detalles completos de tendencias
          // FIX: En Vercel serverless, a veces recibimos [] si cae en una lambda nueva sin caché.
          // Para evitar parpadeo, solo actualizamos si hay datos, o si es la carga inicial.
          if (trends.length > 0) {
            setTrendDetails(trends);
            localStorage.setItem("leaderboard_trend_details", JSON.stringify(trends));

            // Construir tendencias activas desde los trends detectados
            const trendSummary = buildTrendSummaryFromTrends(trends);
            setActiveTrends(trendSummary);
            localStorage.setItem("leaderboard_trends", JSON.stringify(trendSummary));
          } else if (trendDetails.length === 0) {
            // Solo si no tenemos datos previos, usamos el fallback
            const fallbackTrends = buildTrendSummary(leaderboardItems);
            setActiveTrends(fallbackTrends);
            // No guardamos fallback en cache para intentar obtener reales luego
          }
          // Si trends es [] pero ya tenemos trendDetails, mantenemos los viejos (cache visual)
        } else {
          // Fallback: usar leaderboard si trends falla y no tenemos datos
          if (trendDetails.length === 0) {
            setActiveTrends(buildTrendSummary(leaderboardItems));
          }
        }

        // AUTO-SCAN: Si no hay trends y no hay cooldown, escanear automáticamente
        // Esto soluciona el problema de "iniciando por primera vez no hay tendencias"
        const lastScan = localStorage.getItem("lastTrendScanTime");
        // reused 'now' from top
        const canScan = !lastScan || (now - parseInt(lastScan) > (6 * 60 * 60 * 1000));

        // Si no hay trends cargados (o son muy pocos) y podemos escanear
        // FIX: Usar trendsData que ya fue leída, no intentar clonar response consumido
        const trendsEmpty = !trendsResp.ok || (trendsData?.items?.length ?? 0) === 0;

        if (canScan && trendsEmpty) {
          console.log("🚀 Auto-scanning trends for first time user...");
          // Trigger scan in background
          fetch("/api/lootbox/scan", { method: "POST" }).then(res => {
            if (res.ok) {
              localStorage.setItem("lastTrendScanTime", Date.now().toString());
              // Reload data after scan
              setTimeout(() => window.location.reload(), 2000);
            }
          });
        }

        // Update fetch time on success
        if (success) {
          localStorage.setItem("leaderboard_last_fetch", Date.now().toString());
        }

      } catch (error) {
        console.error(error);
      } finally {
        setLoading(false);
      }
    };

    // Initial fetch
    fetchData();

    // Removed polling interval to reduce API usage and load
    // const interval = setInterval(fetchData, 5000);
    // return () => clearInterval(interval);
  }, []);

  // Obtener hasta 5 tendencias más recientes
  const topTrends = trendDetails.slice(0, 5);

  return (
    <div className="grid gap-4 sm:gap-6 md:grid-cols-2 animate-in fade-in slide-in-from-bottom-8 duration-700">
      <Card className="bg-white/5 border-white/10 backdrop-blur-sm">
        <CardHeader className="pb-2 sm:pb-3 px-3 sm:px-6">
          <div className="flex items-center justify-between w-full">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-green-600 dark:text-[#FCFF52] flex-shrink-0" />
              <CardTitle className="text-xs sm:text-sm font-bold uppercase tracking-wider text-muted-foreground">
                {t("trends_title")}
              </CardTitle>
            </div>
            <button
              onClick={handleRefresh}
              disabled={isScanning || cooldownRemaining !== null}
              className="p-1.5 rounded-full hover:bg-white/10 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              title={cooldownRemaining ? `${t("trends_available_in")} ${Math.ceil(cooldownRemaining / (1000 * 60 * 60))}h` : t("trends_refresh")}
            >
              <RefreshCw className={`w-3.5 h-3.5 text-muted-foreground ${isScanning ? "animate-spin" : ""}`} />
            </button>
          </div>
        </CardHeader>
        <CardContent className="space-y-2 sm:space-y-3 px-3 sm:px-6 pb-4 sm:pb-6 max-h-[600px] sm:max-h-[700px] overflow-y-auto scrollbar-thin scrollbar-thumb-green-600/20 dark:scrollbar-thumb-[#FCFF52]/20 scrollbar-track-transparent">
          {loading && (
            <div className="space-y-2">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="p-3 rounded-xl border border-white/5 bg-white/5 animate-pulse">
                  <div className="flex justify-between mb-2">
                    <div className="h-3 w-20 bg-white/10 rounded" />
                    <div className="h-3 w-8 bg-white/10 rounded" />
                  </div>
                  <div className="h-3 w-16 bg-white/10 rounded mb-2" />
                  <div className="h-8 w-full bg-white/5 rounded" />
                </div>
              ))}
            </div>
          )}
          {!loading && topTrends.length === 0 && (
            <div className="text-[10px] sm:text-xs text-muted-foreground text-center py-2">
              {t("trends_empty")}
            </div>
          )}

          {/* Mostrar hasta 5 tendencias con detalles - Responsive */}
          {!loading && topTrends.map((trend, index) => (
            <div
              key={trend.frame_id || trend.cast_hash || index}
              className={`p-2.5 sm:p-3 rounded-lg sm:rounded-xl border mb-2 transition-all hover:scale-[1.01] ${index === 0
                ? "bg-gradient-to-br from-green-600/10 dark:from-[#FCFF52]/10 to-transparent border-green-600/20 dark:border-[#FCFF52]/20 shadow-sm"
                : "bg-white/5 border-white/10"
                }`}
            >
              {/* Header con score */}
              <div className="flex items-start justify-between gap-2 mb-1.5 sm:mb-2 flex-wrap">
                <div className="flex items-center gap-1.5 sm:gap-2 flex-shrink-0">
                  {index === 0 && (
                    <Sparkles className="w-3 h-3 sm:w-3.5 sm:h-3.5 text-green-600 dark:text-[#FCFF52] flex-shrink-0" />
                  )}
                  <span className="text-[9px] sm:text-[10px] uppercase font-bold text-green-700 dark:text-[#FCFF52] whitespace-nowrap">
                    {index + 1} {t("trend_rank")}
                  </span>
                </div>
                {trend.trend_score !== undefined && (
                  <div className="text-[9px] sm:text-[10px] font-mono text-green-700 dark:text-[#FCFF52] bg-green-600/10 dark:bg-[#FCFF52]/10 px-1.5 sm:px-2 py-0.5 rounded-full flex-shrink-0">
                    {(trend.trend_score * 100).toFixed(0)}%
                  </div>
                )}
              </div>

              {/* Autor */}
              {trend.author_username && (
                <div className="mb-1 sm:mb-1.5">
                  <span className="text-[9px] sm:text-[10px] text-muted-foreground">{t("trend_by")} </span>
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

              {/* Link a la tendencia */}
              <div className="mt-2">
                <a
                  href={`https://warpcast.com/${trend.author_username || 'unknown'}/${trend.cast_hash || ''}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1.5 text-[10px] sm:text-xs font-bold text-green-700 dark:text-[#FCFF52] hover:underline group/link"
                >
                  <Sparkles className="w-3 h-3 group-hover/link:animate-pulse" />
                  {t("trend_join")}
                  <ExternalLink className="w-3 h-3 opacity-70" />
                </a>
              </div>

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
          {activeTrends.map((trend, index) => (
            <div
              key={trend.tag}
              className="flex items-center justify-between p-2 sm:p-3 rounded-lg sm:rounded-xl bg-white/5 hover:bg-white/10 transition-all border border-transparent hover:border-green-600/30 dark:hover:border-[#FCFF52]/30 hover:scale-[1.02]"
            >
              <div className="min-w-0 flex-1">
                <div className="font-bold text-xs sm:text-sm text-foreground truncate">
                  #{trend.tag}
                </div>
                <div className="text-[9px] sm:text-[10px] text-muted-foreground">
                  {trend.posts} señales
                </div>
              </div>
              {index < 3 && (
                <div className="text-[9px] sm:text-[10px] uppercase font-bold text-green-700 dark:text-[#FCFF52] bg-green-600/10 dark:bg-[#FCFF52]/10 px-1.5 sm:px-2 py-0.5 sm:py-1 rounded-full flex-shrink-0 ml-2">
                  #{index + 1}
                </div>
              )}
            </div>
          ))}
        </CardContent>
      </Card>

      <Card className="bg-white/5 border-white/10 backdrop-blur-sm">
        <CardHeader className="pb-3">
          <div className="flex items-center gap-2">
            <Trophy className="w-4 h-4 text-yellow-500" />
            <CardTitle className="text-sm font-bold uppercase tracking-wider text-muted-foreground">
              {t("leaderboard_title")}
            </CardTitle>
          </div>
        </CardHeader>
        <CardContent className="space-y-3 max-h-[600px] sm:max-h-[700px] overflow-y-auto scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent">
          {loading && (
            <div className="space-y-3">
              {[...Array(10)].map((_, i) => (
                <div key={i} className="flex items-center justify-between p-2 animate-pulse">
                  <div className="flex items-center gap-3">
                    <div className="w-6 h-6 rounded-full bg-white/10" />
                    <div className="flex flex-col gap-1">
                      <div className="h-4 w-24 bg-white/10 rounded" />
                      <div className="h-3 w-16 bg-white/5 rounded" />
                    </div>
                  </div>
                  <div className="h-4 w-12 bg-white/10 rounded" />
                </div>
              ))}
            </div>
          )}
          {!loading && entries.length === 0 && (
            <div className="text-xs text-muted-foreground">{t("leaderboard_empty")}</div>
          )}
          {!loading && entries.map((winner, index) => (
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
                    {winner.username
                      ? `@${winner.username.replace(/^@/, '')}`
                      : `${winner.address.slice(0, 6)}...${winner.address.slice(-4)}`
                    }
                  </span>
                  <span className="text-[10px] text-muted-foreground uppercase tracking-wider">
                    {/* Simplified reward label logic for I18n */}
                    {winner.reward_type && t(`reward_${winner.reward_type}` as any) ? t(`reward_${winner.reward_type}` as any) : t("leaderboard_pending")}
                  </span>
                </div>
              </div>
              {winner.xp !== undefined && (
                <span className="text-xs font-mono text-green-600 dark:text-[#FCFF52]">
                  +{winner.xp} XP
                </span>
              )}
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

