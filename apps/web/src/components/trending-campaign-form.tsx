"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { Loader2, Send, Wallet, ExternalLink, Box, Sparkles } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { DEFAULT_EVENT, type AgentRunResponse, type LootboxEventPayload } from "@/lib/lootbox";
import { useAccount } from "wagmi";
import { AnalysisOverlay } from "./analysis-overlay";
import { RewardSelector } from "./reward-selector";

type FormState = {
  frameId: string;
  channelId: string;
  trendScore: number;
  targetAddress: string;
};

export function TrendingCampaignForm() {
  const { address } = useAccount();
  const [form, setForm] = useState<FormState>({
    frameId: DEFAULT_EVENT.frameId,
    channelId: DEFAULT_EVENT.channelId,
    trendScore: DEFAULT_EVENT.trendScore,
    targetAddress: "",
  });
  
  // States for the new flow
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [showRewards, setShowRewards] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AgentRunResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const getRewardDisplay = (type?: AgentRunResponse["reward_type"]) => {
    switch (type) {
      case "cusd":
        return {
          title: "MiniPay enviado",
          subtitle: "Revisa tu balance cUSD en MiniPay.",
        };
      case "xp":
        return {
          title: "+XP on-chain",
          subtitle: "Tu reputación fue actualizada en el registro.",
        };
      default:
        return {
          title: "¡Loot NFT minteado!",
          subtitle: "NFT coleccionable enviado a tu wallet.",
        };
    }
  };

  // Trigger analysis animation first
  const handleStartAnalysis = (e: React.FormEvent) => {
    e.preventDefault();
    if (!address) return;
    setIsAnalyzing(true);
    // When overlay completes, it calls onAnalysisComplete
  };

  const onAnalysisComplete = () => {
    setIsAnalyzing(false);
    setShowRewards(true);
  };

  const handleRewardSelect = async (rewardId: LootboxEventPayload["rewardType"]) => {
    setShowRewards(false);
    setLoading(true); 
    setResult(null);
    setError(null);
    
    console.log("Recompensa seleccionada:", rewardId); // Debug
    
    // Aquí es donde mandamos el 'reward_type' al backend para que el contrato sepa qué mintear
    // (A futuro: actualizar contrato para soportar rewardType)
    const payload: LootboxEventPayload = {
      frameId: "", 
      channelId: "global",
      trendScore: 0,
      targetAddress: address || undefined,
      rewardType: rewardId ?? "nft",
    };

    try {
      const response = await fetch("/api/lootbox", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        throw new Error((await response.json()).error ?? "Error desconocido");
      }
      setResult(await response.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error inesperado");
    } finally {
      setLoading(false);
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
                <RewardSelector onSelect={handleRewardSelect} />
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
                    Minteando Premio...
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
             {result && (
                <div className="p-5 rounded-2xl bg-gradient-to-br from-green-500/10 to-emerald-500/5 border border-green-500/20 flex flex-col gap-4">
                    <div className="flex items-center gap-4">
                        <div className="h-12 w-12 rounded-full bg-green-500 flex items-center justify-center text-white shadow-lg shadow-green-500/30">
                             <Box className="h-6 w-6" />
                        </div>
                        <div>
                            <h4 className="font-bold text-lg text-foreground">{getRewardDisplay(result.reward_type).title}</h4>
                            <p className="text-xs text-muted-foreground">{getRewardDisplay(result.reward_type).subtitle}</p>
                        </div>
                    </div>
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
             <Button variant="ghost" className="w-full text-xs text-muted-foreground" onClick={() => setResult(null)}>
                Reiniciar Proceso
             </Button>
          </div>
        )}

        {error && (
          <div className="mt-6 rounded-xl bg-red-500/10 border border-red-500/20 p-4 text-sm text-red-500 text-center font-medium">
            {error}
          </div>
        )}
    </div>
  );
}

