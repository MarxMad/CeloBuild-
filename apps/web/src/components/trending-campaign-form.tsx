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
  const [result, setResult] = useState<AgentRunResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [isClient, setIsClient] = useState(false);
  useEffect(() => {
    setIsClient(true);
  }, []);

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
    setError(null);
    setResult(null);

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

      setResult(resultData);

      // Determinar mensaje de éxito
      const display = getRewardDisplay(resultData.reward_type);



    } catch (err) {
      console.error("❌ Error:", err);
      setError(err instanceof Error ? err.message : "Hubo un problema procesando tu solicitud");

    } finally {
      setIsLoading(false);
    }
  };

  if (!isClient) return null;

  return (
    <div className="space-y-6 relative">
      <Card className="w-full bg-black/40 border-white/10 backdrop-blur-xl shadow-2xl overflow-hidden relative group">
        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-primary/5 opacity-0 group-hover:opacity-100 transition-opacity duration-700" />

        <CardHeader className="relative z-10">
          <CardTitle className="flex items-center gap-3 text-xl text-white">
            <Sparkles className="w-5 h-5 text-primary animate-pulse" />
            Verificar Elegibilidad
          </CardTitle>
          <CardDescription className="text-gray-400">
            Analiza tu participación en Farcaster y obtén recompensas automáticamente.
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-6 relative z-10">
          {!isConnected ? (
            <div className="p-6 rounded-xl bg-white/5 border border-white/10 text-center space-y-3">
              <Wallet className="w-10 h-10 text-gray-500 mx-auto mb-2" />
              <p className="text-gray-300 font-medium">Conecta tu wallet para continuar</p>
              <p className="text-xs text-gray-500">Necesitas una wallet de Celo para recibir recompensas</p>
            </div>
          ) : (
            <div className="space-y-6">
              <div className="p-4 rounded-xl bg-primary/5 border border-primary/10 space-y-3">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-400">Wallet Conectada</span>
                  <span className="font-mono text-primary bg-primary/10 px-2 py-0.5 rounded text-xs">
                    {address?.slice(0, 6)}...{address?.slice(-4)}
                  </span>
                </div>

                {farcasterUser.username && (
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-400">Usuario Farcaster</span>
                    <span className="font-medium text-white flex items-center gap-1">
                      @{farcasterUser.username}
                      {farcasterUser.fid && (
                        <span className="text-[10px] text-gray-500 bg-gray-800 px-1.5 py-0.5 rounded-full">
                          FID: {farcasterUser.fid}
                        </span>
                      )}
                    </span>
                  </div>
                )}
              </div>

              {!result && (
                <Button
                  className="w-full bg-primary hover:bg-primary/90 text-black font-bold h-12 text-lg shadow-[0_0_20px_rgba(252,255,82,0.3)] hover:shadow-[0_0_30px_rgba(252,255,82,0.5)] transition-all duration-300"
                  onClick={handleAnalyzeAndClaim}
                  disabled={isLoading}
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                      Analizando y Verificando...
                    </>
                  ) : (
                    <>
                      <Gift className="mr-2 h-5 w-5" />
                      Verificar y Reclamar Recompensa
                    </>
                  )}
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

              {/* Transaction Link */}
              {result.explorer_url && (
                <Button variant="outline" className="w-full border-green-500/30 hover:bg-green-500/10 text-green-600 dark:text-green-400" asChild>
                  <Link href={result.explorer_url} target="_blank">
                    Ver Transacción
                    <ExternalLink className="ml-2 h-4 w-4" />
                  </Link>
                </Button>
              )}
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
          </p>
        </div>
      )}
    </div>
  );
}
