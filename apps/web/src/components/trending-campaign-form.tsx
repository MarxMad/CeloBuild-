"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { Loader2, Send, Wallet, ExternalLink, Box, Sparkles, TrendingUp, Gift } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { DEFAULT_EVENT, type AgentRunResponse, type LootboxEventPayload } from "@/lib/lootbox";
import { useAccount } from "wagmi";
import { useFarcasterUser } from "./farcaster-provider";
import { AnalysisOverlay } from "./analysis-overlay";

type FormState = {
  frameId: string;
  channelId: string;
  trendScore: number;
  targetAddress: string;
};

export function TrendingCampaignForm() {
  const { address, isConnected } = useAccount();
  const farcasterUser = useFarcasterUser();

  const [isLoading, setIsLoading] = useState(false);
  const [isAnimationComplete, setIsAnimationComplete] = useState(false);
  const [pendingResult, setPendingResult] = useState<AgentRunResponse | null>(null);
  const [result, setResult] = useState<AgentRunResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [isClient, setIsClient] = useState(false);
  useEffect(() => {
    setIsClient(true);
  }, []);

  // Effect to handle completion when both API and Animation are done
  useEffect(() => {
    if (isAnimationComplete && pendingResult) {
      setResult(pendingResult);
      setIsLoading(false);
    } else if (isAnimationComplete && error) {
      setIsLoading(false);
    }
  }, [isAnimationComplete, pendingResult, error]);

  const getRewardDisplay = (type?: AgentRunResponse["reward_type"]) => {
    switch (type) {
      case "cusd":
        return {
          title: "¡cUSD Recibido!",
          subtitle: "Has recibido cUSD directamente en tu wallet.",
        };
      case "xp":
        return {
          title: "¡XP Otorgado!",
          subtitle: "Has ganado experiencia por tu participación.",
        };
      case "nft":
      default:
        return {
          title: "¡NFT Minteado!",
          subtitle: "Has recibido un NFT exclusivo en tu wallet.",
        };
    }
  };

  const handleAnalyzeAndClaim = async () => {
    if (!address) return;

    setIsLoading(true);
    setIsAnimationComplete(false);
    setPendingResult(null);
    setResult(null);
    setError(null);

    try {
      const payload: LootboxEventPayload = {
        frameId: undefined,
        channelId: "global",
        trendScore: 0, // El backend calculará esto
        targetAddress: address,
        targetFid: farcasterUser.fid ? Number(farcasterUser.fid) : undefined,
        // rewardType omitido para selección automática
      };

      console.log("🚀 Enviando solicitud de análisis y recompensa:", payload);

      const response = await fetch("/api/lootbox", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const resultData = await response.json();
      console.log("✅ Resultado:", resultData);

      if (!response.ok) {
        const errorMessage = resultData?.error || resultData?.detail || "Error en la solicitud";

        // Manejo específico de errores de configuración
        if (errorMessage.includes("Backend no configurado")) {
          throw new Error("Error de configuración del backend. Por favor contacta al administrador.");
        }

        throw new Error(errorMessage);
      }

      setPendingResult(resultData);

      // Trigger XP refresh
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new Event('refresh-xp'));
      }

    } catch (err) {
      console.error("❌ Error:", err);
      setError(err instanceof Error ? err.message : "Hubo un problema procesando tu solicitud");
      // If error occurs, we still wait for animation or show error immediately?
      // Let's show error immediately if animation is taking too long? 
      // Or just let animation finish then show error. 
      // For better UX, let's wait for animation to finish so it doesn't flash.
    }
  };

  if (!isClient) return null;

  return (
    <div className="space-y-6 relative max-w-md mx-auto">
      {isLoading && (
        <AnalysisOverlay
          isDone={!!pendingResult || !!error}
          onComplete={() => setIsAnimationComplete(true)}
        />
      )}
      <Card className="w-full bg-black/60 border-white/10 backdrop-blur-2xl shadow-[0_0_50px_-12px_rgba(252,255,82,0.15)] overflow-hidden relative group ring-1 ring-white/5">
        <div className="absolute inset-0 bg-gradient-to-b from-white/5 via-transparent to-transparent opacity-50" />
        <div className="absolute inset-0 bg-[url('/grid-pattern.svg')] opacity-10" />

        <CardHeader className="relative z-10 pb-2">
          <CardTitle className="flex items-center gap-3 text-2xl text-white font-bold tracking-tight">
            <div className="p-2 rounded-lg bg-[#FCFF52]/10 ring-1 ring-[#FCFF52]/20">
              <Sparkles className="w-5 h-5 text-[#FCFF52] animate-pulse" />
            </div>
            Verificar Elegibilidad
          </CardTitle>
          <CardDescription className="text-gray-400 text-base">
            Analiza tu participación en Farcaster y obtén recompensas automáticamente.
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-8 relative z-10 pt-6">
          {!isConnected ? (
            <div className="py-10 px-6 rounded-2xl bg-white/5 border border-white/10 text-center space-y-4 hover:bg-white/10 transition-colors group/connect">
              <div className="h-16 w-16 rounded-full bg-white/5 flex items-center justify-center mx-auto group-hover/connect:scale-110 transition-transform duration-500">
                <Wallet className="w-8 h-8 text-gray-500 group-hover/connect:text-white transition-colors" />
              </div>
              <div className="space-y-1">
                <p className="text-white font-medium text-lg">Conecta tu Wallet</p>
                <p className="text-sm text-gray-500">Necesaria para recibir recompensas en Celo</p>
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Info Panel */}
              <div className="rounded-2xl bg-black/40 border border-white/10 overflow-hidden">
                {/* Wallet Row */}
                <div className="p-4 border-b border-white/5 flex items-center justify-between group/item hover:bg-white/5 transition-colors">
                  <div className="flex items-center gap-3">
                    <div className="p-1.5 rounded-md bg-blue-500/10 text-blue-400">
                      <Wallet className="w-4 h-4" />
                    </div>
                    <span className="text-sm text-gray-400 font-medium">Wallet</span>
                  </div>
                  <span className="font-mono text-[#FCFF52] bg-[#FCFF52]/10 px-3 py-1 rounded-full text-xs border border-[#FCFF52]/20 shadow-[0_0_10px_rgba(252,255,82,0.1)]">
                    {address?.slice(0, 6)}...{address?.slice(-4)}
                  </span>
                </div>

                {/* Farcaster Row */}
                {farcasterUser.username && (
                  <div className="p-4 flex items-center justify-between group/item hover:bg-white/5 transition-colors">
                    <div className="flex items-center gap-3">
                      <div className="p-1.5 rounded-md bg-purple-500/10 text-purple-400">
                        <TrendingUp className="w-4 h-4" />
                      </div>
                      <span className="text-sm text-gray-400 font-medium">Farcaster</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-white">@{farcasterUser.username}</span>
                      {farcasterUser.fid && (
                        <span className="text-[10px] text-gray-400 bg-white/10 px-2 py-0.5 rounded-full border border-white/10">
                          FID: {farcasterUser.fid}
                        </span>
                      )}
                    </div>
                  </div>
                )}
              </div>

              {!result && (
                <Button
                  className="w-full bg-[#FCFF52] hover:bg-[#e6e945] text-black font-black h-14 text-lg shadow-[0_0_30px_rgba(252,255,82,0.3)] hover:shadow-[0_0_50px_rgba(252,255,82,0.5)] transition-all duration-300 rounded-xl relative overflow-hidden group/btn"
                  onClick={handleAnalyzeAndClaim}
                  disabled={isLoading}
                >
                  <div className="absolute inset-0 bg-white/20 translate-y-full group-hover/btn:translate-y-0 transition-transform duration-300" />
                  <div className="relative flex items-center justify-center gap-2">
                    {isLoading ? (
                      <>
                        <Loader2 className="h-5 w-5 animate-spin" />
                        <span>Verificando...</span>
                      </>
                    ) : (
                      <>
                        <Gift className="h-5 w-5 group-hover/btn:rotate-12 transition-transform" />
                        <span>Reclamar Recompensa</span>
                      </>
                    )}
                  </div>
                </Button>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Result Display */}
      {result && (
        <div className="mt-6 space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
          {/* Success Card */}
          {result.eligible !== false && result.mode !== "failed" && result.mode !== "analysis_only" && (
            <div className="p-5 rounded-2xl bg-gradient-to-br from-green-500/10 to-emerald-500/5 border border-green-500/20 flex flex-col gap-4">
              <div className="flex items-center gap-4">
                <div className="h-12 w-12 rounded-full bg-green-500 flex items-center justify-center text-white shadow-lg shadow-green-500/30">
                  <Box className="h-6 w-6" />
                </div>
                <div className="flex-1">
                  <h4 className="font-bold text-lg text-foreground">{getRewardDisplay(result.reward_type).title}</h4>
                  <p className="text-xs text-muted-foreground">{getRewardDisplay(result.reward_type).subtitle}</p>
                </div>
              </div>

              {/* NFT Image Display */}
              {result.nft_images && (
                (() => {
                  // Try to find image by address (case insensitive) or fallback to first available image
                  const userAddress = address?.toLowerCase();
                  const imageUri = Object.entries(result.nft_images || {}).find(([addr]) => addr.toLowerCase() === userAddress)?.[1]
                    || Object.values(result.nft_images || {})[0];

                  if (imageUri) {
                    return (
                      <div className="rounded-xl overflow-hidden border border-white/10 shadow-lg relative aspect-[2/3] mx-auto w-2/3">
                        <img
                          src={imageUri}
                          alt="NFT Reward"
                          className="w-full h-full object-cover"
                        />
                        <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent pointer-events-none" />
                        <div className="absolute bottom-2 left-0 right-0 text-center">
                          <span className="text-[10px] font-bold text-yellow-400 uppercase tracking-wider bg-black/40 px-2 py-1 rounded-full backdrop-blur-sm border border-yellow-500/20">
                            New Artifact
                          </span>
                        </div>
                      </div>
                    );
                  }
                  return null;
                })()
              )}

              {/* Transaction Link */}
              {result.explorer_url && (
                <Button variant="outline" className="w-full border-green-500/30 hover:bg-green-500/10 text-green-600 dark:text-green-400" asChild>
                  <Link href={result.explorer_url} target="_blank">
                    Ver Transacción
                    <ExternalLink className="ml-2 h-4 w-4" />
                  </Link>
                </Button>
              )}

              {/* Share Button */}
              <Button
                className="w-full bg-[#855DCD] hover:bg-[#7C55C3] text-white font-bold shadow-lg shadow-purple-500/20"
                onClick={() => {
                  const score = result.user_analysis?.score?.toFixed(0) || "0";
                  const rewardName = getRewardDisplay(result.reward_type).title;
                  const text = `¡Acabo de ganar ${rewardName} en Premio.xyz! 🏆\n\nMi nivel de viralidad es: ${score}/100 🚀\n\nDescubre tu nivel y gana recompensas en crypto y NFTs aquí: https://celo-build-web-8rej.vercel.app`;
                  const embed = "https://celo-build-web-8rej.vercel.app";
                  const url = `https://warpcast.com/~/compose?text=${encodeURIComponent(text)}&embeds[]=${encodeURIComponent(embed)}`;

                  // Try SDK first, fallback to window.open
                  import("@farcaster/miniapp-sdk").then(({ sdk }) => {
                    sdk.actions.openUrl(url);
                  }).catch(() => {
                    window.open(url, "_blank");
                  });
                }}
              >
                <TrendingUp className="w-4 h-4 mr-2" />
                Compartir en Farcaster
              </Button>
            </div>
          )}

          {/* Analysis Details (Always show if available) */}
          {(result.user_analysis || result.trend_info) && (
            <div className="p-4 rounded-xl bg-white/5 border border-white/10 space-y-3">
              <div className="flex items-center gap-2 mb-2">
                <Sparkles className="w-4 h-4 text-[#FCFF52]" />
                <h5 className="text-sm font-bold text-foreground">Detalles del Análisis</h5>
              </div>

              {result.user_analysis && (
                <>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-muted-foreground">@</span>
                      <span className="text-sm font-semibold text-foreground">
                        {result.user_analysis.username || "Usuario"}
                      </span>
                    </div>
                    {result.user_analysis.score !== undefined && (
                      <div className="text-sm font-mono font-bold text-[#FCFF52]">
                        {result.user_analysis.score.toFixed(1)} pts
                      </div>
                    )}
                  </div>

                  {result.user_analysis.reasons && result.user_analysis.reasons.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mt-2">
                      {result.user_analysis.reasons.map((reason, idx) => (
                        <span
                          key={idx}
                          className="text-[9px] px-2 py-0.5 rounded-full bg-[#FCFF52]/10 text-[#FCFF52] border border-[#FCFF52]/20 uppercase"
                        >
                          {reason}
                        </span>
                      ))}
                    </div>
                  )}
                </>
              )}
            </div>
          )}

          {/* Reset Button */}
          <Button variant="ghost" className="w-full text-xs text-muted-foreground" onClick={() => {
            setResult(null);
            setError(null);
          }}>
            Reiniciar Proceso
          </Button>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="mt-6 rounded-xl bg-red-500/10 border border-red-500/30 p-5 text-red-400 space-y-2 animate-in fade-in slide-in-from-bottom-4 duration-300">
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-full bg-red-500/20 flex items-center justify-center">
              <span className="text-red-400 text-lg">⚠️</span>
            </div>
            <h4 className="font-bold text-base text-red-300">No Eres Elegible</h4>
          </div>
          <p className="text-sm text-red-400/90 pl-10">
            {error}
          </p>
        </div>
      )}

      {/* Transaction Failed Display */}
      {result && result.mode === "failed" && (
        <div className="mt-6 rounded-xl bg-orange-500/10 border border-orange-500/30 p-5 text-orange-400 space-y-2 animate-in fade-in slide-in-from-bottom-4 duration-300">
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-full bg-orange-500/20 flex items-center justify-center">
              <span className="text-orange-400 text-lg">⚠️</span>
            </div>
            <h4 className="font-bold text-base text-orange-300">Error en la Transacción</h4>
          </div>
          <p className="text-sm text-orange-400/90 pl-10">
            Hubo un problema enviando tu recompensa on-chain.
            {result.error && (
              <span className="block mt-1 font-mono text-xs opacity-80 bg-black/20 p-2 rounded">
                Error: {result.error}
              </span>
            )}
          </p>
        </div>
      )}
    </div>
  );
}
