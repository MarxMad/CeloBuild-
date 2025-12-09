"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { Loader2, Send, Wallet, ExternalLink, Box, Sparkles, TrendingUp } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { DEFAULT_EVENT, type AgentRunResponse, type LootboxEventPayload } from "@/lib/lootbox";
import { useAccount } from "wagmi";
import { AnalysisOverlay } from "./analysis-overlay";
import { RewardSelector } from "./reward-selector";
import { useFarcasterUser } from "./farcaster-provider";

type FormState = {
  frameId: string;
  channelId: string;
  trendScore: number;
  targetAddress: string;
};

export function TrendingCampaignForm() {
  const { address } = useAccount();
  const farcasterUser = useFarcasterUser();
  const [form, setForm] = useState<FormState>({
    frameId: DEFAULT_EVENT.frameId || "",
    channelId: DEFAULT_EVENT.channelId,
    trendScore: DEFAULT_EVENT.trendScore,
    targetAddress: "",
  });

  // States for the new flow
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [showRewards, setShowRewards] = useState(false);
  const [loading, setLoading] = useState(false);
  const [selectedRewardType, setSelectedRewardType] = useState<LootboxEventPayload["rewardType"] | null>(null);
  const [result, setResult] = useState<AgentRunResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [userAnalysis, setUserAnalysis] = useState<AgentRunResponse["user_analysis"] | null>(null);
  const [trendInfo, setTrendInfo] = useState<AgentRunResponse["trend_info"] | null>(null);
  const getRewardDisplay = (type?: AgentRunResponse["reward_type"]) => {
    switch (type) {
      case "cusd":
        return {
          title: "MiniPay enviado",
          subtitle: "Revisa tu balance cUSD en MiniPay.",
        };
      case "xp":
        return {
          title: "¡XP Otorgado!",
          subtitle: "Has recibido puntos de experiencia on-chain por tu contribución.",
        };
      case "analysis":
        return {
          title: "Análisis Completado",
          subtitle: "Eres elegible. Selecciona tu recompensa abajo.",
        };
      default:
        return {
          title: "¡Loot NFT minteado!",
          subtitle: "NFT coleccionable enviado a tu wallet.",
        };
    }
  };

  // Trigger analysis animation first
  const handleStartAnalysis = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!address) return;

    setIsAnalyzing(true);
    setError(null);
    setUserAnalysis(null);
    setTrendInfo(null);

    try {
      // Ejecutar análisis ANTES de mostrar el selector de recompensas
      // Esto detecta la tendencia y analiza al usuario específico
      const analysisPayload: LootboxEventPayload = {
        frameId: undefined, // El backend generará el frame_id cuando detecte la tendencia
        channelId: "global",
        trendScore: 0,
        targetAddress: address, // Enviar address para recompensa
        targetFid: farcasterUser.fid ? Number(farcasterUser.fid) : undefined, // Asegurar que sea número
        rewardType: "analysis", // Modo análisis: solo verificar elegibilidad sin distribuir
      };

      console.log("📤 Enviando análisis:", {
        ...analysisPayload,
        hasFid: !!farcasterUser.fid,
        fidValue: farcasterUser.fid
      });

      const response = await fetch("/api/lootbox", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(analysisPayload),
      });

      if (!response.ok) {
        const errorData = await response.json();
        const errorMessage = errorData?.error || errorData?.detail || "Error en el análisis";

        // Detectar errores de configuración
        if (
          errorMessage.includes("Backend no configurado") ||
          errorMessage.includes("AGENT_SERVICE_URL") ||
          errorMessage.includes("DEPLOYMENT_NOT_FOUND") ||
          errorMessage.includes("deployment could not be found")
        ) {
          throw new Error(
            "Error de configuración: El backend no está configurado correctamente en Vercel.\n\n" +
            "Pasos para solucionarlo:\n" +
            "1. Ve a tu proyecto del frontend en Vercel\n" +
            "2. Settings → Environment Variables\n" +
            "3. Agrega estas variables:\n" +
            "   - AGENT_SERVICE_URL = https://celo-build-backend-agents.vercel.app\n" +
            "   - NEXT_PUBLIC_AGENT_SERVICE_URL = https://celo-build-backend-agents.vercel.app\n" +
            "4. Haz un Redeploy del frontend"
          );
        }

        throw new Error(errorMessage);
      }

      const analysisResult = await response.json();
      console.log("Análisis completado:", analysisResult);

      // Verificar si el usuario es elegible
      if (analysisResult.eligible === false) {
        // Usuario no es elegible - mostrar mensaje del backend
        const errorMessage = analysisResult.eligibility_message ||
          "No eres elegible en este momento. Intenta participar más en Farcaster o tener una cuenta vinculada a tu wallet.";
        setError(errorMessage);
        setIsAnalyzing(false);
        setUserAnalysis(null);
        setTrendInfo(null);
        return;
      }

      // Guardar datos del análisis para mostrar en el RewardSelector
      setUserAnalysis(analysisResult.user_analysis || null);
      setTrendInfo(analysisResult.trend_info || null);

      // Cuando el overlay completa, mostrar selector de recompensas con el análisis
      // El AnalysisOverlay se encargará de llamar onAnalysisComplete después de la animación

    } catch (err) {
      setError(err instanceof Error ? err.message : "Error en el análisis");
      setIsAnalyzing(false);
    }
  };

  const onAnalysisComplete = () => {
    setIsAnalyzing(false);
    setShowRewards(true);
  };

  const handleRewardSelect = async (rewardId: LootboxEventPayload["rewardType"]) => {
    setShowRewards(false);
    setSelectedRewardType(rewardId); // Guardar el tipo seleccionado para el loader
    setLoading(true);
    setResult(null);
    setError(null);

    console.log("Recompensa seleccionada:", rewardId); // Debug

    // Aquí es donde mandamos el 'reward_type' al backend para que el contrato sepa qué mintear
    // (A futuro: actualizar contrato para soportar rewardType)
    // No enviar frameId - el backend lo generará automáticamente cuando detecte la tendencia
    const payload: LootboxEventPayload = {
      frameId: undefined,  // El backend generará el frame_id cuando detecte la tendencia
      channelId: "global",
      trendScore: 0,
      targetAddress: address || undefined,
      targetFid: farcasterUser.fid ? Number(farcasterUser.fid) : undefined, // IMPORTANTE: Enviar FID también al reclamar
      rewardType: rewardId ?? "nft",
    };

    try {
      const response = await fetch("/api/lootbox", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        const errorData = await response.json();
        const errorMessage = errorData?.error || errorData?.detail || "Error desconocido";

        // Detectar errores de configuración
        if (
          errorMessage.includes("Backend no configurado") ||
          errorMessage.includes("AGENT_SERVICE_URL") ||
          errorMessage.includes("DEPLOYMENT_NOT_FOUND") ||
          errorMessage.includes("deployment could not be found")
        ) {
          throw new Error(
            "Error de configuración: El backend no está configurado correctamente en Vercel.\n\n" +
            "Pasos para solucionarlo:\n" +
            "1. Ve a tu proyecto del frontend en Vercel\n" +
            "2. Settings → Environment Variables\n" +
            "3. Agrega estas variables:\n" +
            "   - AGENT_SERVICE_URL = https://celo-build-backend-agents.vercel.app\n" +
            "   - NEXT_PUBLIC_AGENT_SERVICE_URL = https://celo-build-backend-agents.vercel.app\n" +
            "4. Haz un Redeploy del frontend"
          );
        }

        throw new Error(errorMessage);
      }
      setResult(await response.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error inesperado");
    } finally {
      setLoading(false);
      setSelectedRewardType(null); // Limpiar después de completar
    }
  };

  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
  }, []);

  if (!isClient) return null; // Avoid hydration mismatch

  return (
    <div className="space-y-6 relative">
      {/* Step 1: Analysis Overlay */}
      {isAnalyzing && (
        <AnalysisOverlay onComplete={onAnalysisComplete} />
      )}

      {/* Step 2: Reward Selection */}
      {showRewards && (
        <div className="fixed inset-0 bg-black/90 z-40 flex items-center justify-center p-6 backdrop-blur-sm">
          <RewardSelector
            onSelect={handleRewardSelect}
            userAnalysis={userAnalysis}
            trendInfo={trendInfo}
          />
        </div>
      )}

      <form className="grid gap-5" onSubmit={handleStartAnalysis}>

        <div className="flex flex-col gap-4 items-center justify-center py-4">
          <div className="text-center space-y-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-green-500/10 text-green-500 text-[10px] font-bold uppercase tracking-widest animate-pulse">
              <span className="w-2 h-2 rounded-full bg-green-500"></span>
              Live Monitor
            </div>
            <h3 className="text-xl font-bold text-white">Agentes Autónomos</h3>
            <p className="text-xs text-muted-foreground max-w-[280px] mx-auto">
              El sistema escaneará Farcaster buscando tendencias virales y recompensará automáticamente a tu wallet.
            </p>
          </div>
        </div>

        {/* Only show button if we are not in success state yet */}
        {!result && (
          <Button type="submit" disabled={loading || !address} className="w-full h-16 text-lg font-bold shadow-xl shadow-primary/10 rounded-2xl border-t border-white/10 relative overflow-hidden group" size="lg">
            <div className="absolute inset-0 bg-gradient-to-r from-primary/80 to-secondary/80 opacity-0 group-hover:opacity-10 transition-opacity" />
            {loading ? (
              <>
                <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                {selectedRewardType === "cusd"
                  ? "Enviando cUSD..."
                  : selectedRewardType === "xp"
                    ? "Otorgando XP..."
                    : "Minteando Premio..."}
              </>
            ) : (
              <>
                <Sparkles className="mr-2 h-5 w-5 animate-pulse" />
                {address ? "Activar Recompensas" : "Conecta Wallet para Iniciar"}
              </>
            )}
          </Button>
        )}

        {!address && (
          <p className="text-center text-[10px] text-red-400 font-medium animate-pulse">
            * Wallet requerida para recibir premios
          </p>
        )}
      </form>

      {result && (
        <div className="mt-6 space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
          {/* Success Card */}
          {result && result.eligible && result.mode !== "failed" && (
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

              {/* Análisis del Usuario */}
              {result.user_analysis && (
                <div className="p-4 rounded-xl bg-white/5 border border-white/10 space-y-3">
                  <div className="flex items-center gap-2 mb-2">
                    <Sparkles className="w-4 h-4 text-[#FCFF52]" />
                    <h5 className="text-sm font-bold text-foreground">Tu Análisis</h5>
                  </div>

                  {/* Username y Score */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-muted-foreground">@</span>
                      <span className="text-sm font-semibold text-foreground">
                        {result.user_analysis.username || "Usuario"}
                      </span>
                      {result.user_analysis.power_badge && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-yellow-500/20 text-yellow-500 border border-yellow-500/30">
                          ⭐ Power
                        </span>
                      )}
                    </div>
                    {result.user_analysis.score !== undefined && (
                      <div className="text-sm font-mono font-bold text-[#FCFF52]">
                        {result.user_analysis.score.toFixed(1)} pts
                      </div>
                    )}
                  </div>

                  {/* Stats */}
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    {result.user_analysis.follower_count !== undefined && (
                      <div className="flex items-center gap-1.5">
                        <span className="text-muted-foreground">Followers:</span>
                        <span className="font-semibold text-foreground">{result.user_analysis.follower_count}</span>
                      </div>
                    )}
                    {result.user_analysis.participation?.total_engagement !== undefined && (
                      <div className="flex items-center gap-1.5">
                        <span className="text-muted-foreground">Engagement:</span>
                        <span className="font-semibold text-foreground">
                          {result.user_analysis.participation.total_engagement.toFixed(1)}
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Reasons */}
                  {result.user_analysis.reasons && result.user_analysis.reasons.length > 0 && (
                    <div className="flex flex-wrap gap-1.5">
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

                  {/* Participación */}
                  {result.user_analysis.participation?.directly_participated && (
                    <div className="text-[10px] text-green-400 flex items-center gap-1">
                      <span>✓</span>
                      <span>Participaste en esta tendencia</span>
                    </div>
                  )}
                </div>
              )}

              {/* Información de la Tendencia */}
              {result.trend_info && (
                <div className="p-3 rounded-lg bg-white/5 border border-white/10 space-y-2">
                  <div className="flex items-center gap-2">
                    <TrendingUp className="w-3 h-3 text-[#FCFF52]" />
                    <span className="text-xs font-bold text-[#FCFF52] uppercase">Tendencia Detectada</span>
                    {result.trend_info.trend_score !== undefined && (
                      <span className="text-[10px] font-mono text-muted-foreground ml-auto">
                        {(result.trend_info.trend_score * 100).toFixed(0)}%
                      </span>
                    )}
                  </div>
                  {result.trend_info.source_text && (
                    <p className="text-xs text-foreground line-clamp-2">
                      {result.trend_info.source_text}
                    </p>
                  )}
                  {result.trend_info.ai_analysis && (
                    <div className="space-y-1">
                      <div className="flex items-center gap-1.5">
                        <span className="text-[10px] text-muted-foreground italic line-clamp-2">
                          💡 {result.trend_info.ai_analysis}
                        </span>
                        {result.trend_info.ai_enabled !== undefined && (
                          <span className={`text-[8px] px-1.5 py-0.5 rounded-full font-bold ${result.trend_info.ai_enabled
                            ? "bg-purple-500/20 text-purple-400 border border-purple-500/30"
                            : "bg-gray-500/20 text-gray-400 border border-gray-500/30"
                            }`}>
                            {result.trend_info.ai_enabled ? "🤖 AI" : "📊 Básico"}
                          </span>
                        )}
                      </div>
                    </div>
                  )}
                  {result.trend_info.topic_tags && result.trend_info.topic_tags.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {result.trend_info.topic_tags.slice(0, 3).map((tag) => (
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

              {/* Otras Tendencias (si hay múltiples) */}
              {result.trends && result.trends.length > 1 && (
                <div className="space-y-2 mt-4">
                  <h5 className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Otras Tendencias</h5>
                  <div className="space-y-2">
                    {result.trends.slice(1, 5).map((trend, idx) => (
                      <div key={idx} className="p-2 rounded-lg bg-white/5 border border-white/10 flex items-start gap-2">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-[10px] font-bold text-foreground truncate">
                              @{trend.author?.username || "unknown"}
                            </span>
                            <span className="text-[9px] font-mono text-muted-foreground ml-auto">
                              {(trend.trend_score * 100).toFixed(0)}%
                            </span>
                          </div>
                          <p className="text-[10px] text-muted-foreground line-clamp-2">
                            {trend.ai_analysis || trend.source_text}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

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

          {/* Console Output */}
          {/* Oculto por petición de diseño limpio, descomentar si se requiere debug */}
          {/* 
            <div className="rounded-xl bg-black/90 p-4 font-mono text-[10px] text-green-400 overflow-x-auto border border-white/10 shadow-inner">
              <p className="mb-2 text-gray-500 border-b border-gray-800 pb-1">System Log</p>
              <p><span className="text-blue-400">Thread:</span> {result.thread_id}</p>
              <div className="mt-2 whitespace-pre-wrap opacity-80">{result.summary}</div>
            </div> 
            */}

          {/* Reset Button */}
          <Button variant="ghost" className="w-full text-xs text-muted-foreground" onClick={() => {
            setResult(null);
            setSelectedRewardType(null);
            setShowRewards(false);
            setIsAnalyzing(false);
          }}>
            Reiniciar Proceso
          </Button>
        </div>
      )}

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
          <p className="text-xs text-red-400/70 pl-10 mt-2">
            💡 Consejo: Vincular una cuenta de Farcaster aumenta tu elegibilidad y score de recompensas.
          </p>
        </div>
      )}

      {result && result.mode === "failed" && (
        <div className="mt-6 rounded-xl bg-orange-500/10 border border-orange-500/30 p-5 text-orange-400 space-y-2 animate-in fade-in slide-in-from-bottom-4 duration-300">
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-full bg-orange-500/20 flex items-center justify-center">
              <span className="text-orange-400 text-lg">⚠️</span>
            </div>
            <h4 className="font-bold text-base text-orange-300">Error en la Transacción</h4>
          </div>
          <p className="text-sm text-orange-400/90 pl-10">
            Hubo un problema enviando tu recompensa on-chain. Por favor intenta de nuevo en unos momentos.
          </p>
        </div>
      )}
    </div>
  );
}

