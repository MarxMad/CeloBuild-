"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { Loader2, Send, Wallet, ExternalLink, Box, Sparkles, TrendingUp, Gift, Zap, MessageSquare } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { DEFAULT_EVENT, type AgentRunResponse, type LootboxEventPayload } from "@/lib/lootbox";
import { useAccount } from "wagmi";
import { useFarcasterUser } from "./farcaster-provider";
import { AnalysisOverlay } from "./analysis-overlay";
import { useLanguage } from "@/components/language-provider";
import { EnergyDisplay } from "./energy-display";

type FormState = {
  frameId: string;
  channelId: string;
  trendScore: number;
  targetAddress: string;
};

export function TrendingCampaignForm() {
  const { t } = useLanguage();
  const { address, isConnected } = useAccount();
  const farcasterUser = useFarcasterUser();

  const [isLoading, setIsLoading] = useState(false);
  const [isAnimationComplete, setIsAnimationComplete] = useState(false);
  const [pendingResult, setPendingResult] = useState<AgentRunResponse | null>(null);
  const [result, setResult] = useState<AgentRunResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [progressStep, setProgressStep] = useState<'idle' | 'scanning' | 'analyzing' | 'verifying' | 'sending' | 'completed'>('idle');
  const [showRechargeModal, setShowRechargeModal] = useState(false);
  const [energyConsumed, setEnergyConsumed] = useState(false);
  const [previousEnergy, setPreviousEnergy] = useState(3);
  const [energyFromResponse, setEnergyFromResponse] = useState<{value: number, timestamp: number} | null>(null); // Energía recibida de la respuesta del backend

  const [isClient, setIsClient] = useState(false);
  useEffect(() => {
    setIsClient(true);
  }, []);

  // Effect to handle completion when both API and Animation are done
  useEffect(() => {
    if (isAnimationComplete && pendingResult) {
      setResult(pendingResult);
      setIsLoading(false);
      // NO consultar energía aquí si ya la tenemos de la respuesta
      // El estado de energía ya se actualizó desde energy_status en la respuesta
      console.log("🎁 [Result] Mostrando resultado (energía ya actualizada desde respuesta)");
    } else if (isAnimationComplete && error) {
      setIsLoading(false);
    }
  }, [isAnimationComplete, pendingResult, error]);

  const getRewardDisplay = (type?: AgentRunResponse["reward_type"]) => {
    switch (type) {
      case "cusd":
        return {
          title: "¡cUSD Recibido!", // Kept static or add to dictionary if critical
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

  const [verificationError, setVerificationError] = useState<string | null>(null);
  const [showThankYou, setShowThankYou] = useState(false);

  // ENERGY SYSTEM STATE
  const [energy, setEnergy] = useState({ 
    current: 3, 
    max: 3, 
    seconds: 0,
    bolts: [] as Array<{ index: number; available: boolean; seconds_to_refill: number; refill_at: number | null }>
  });

  const fetchEnergy = async (force: boolean = false) => {
    if (!address) return;
    
    // Si tenemos energía de la respuesta reciente (menos de 10 segundos), no sobrescribir
    // a menos que se fuerce explícitamente
    if (!force && energyFromResponse !== null) {
      const timeSinceResponse = Date.now() - energyFromResponse.timestamp;
      if (timeSinceResponse < 10000) {
        console.log(`⚡ [Energy] Ignorando consulta (${Math.floor(timeSinceResponse/1000)}s desde respuesta), usando energía de respuesta: ${energyFromResponse.value}`);
        return;
      }
    }
    
    try {
      const res = await fetch(`/api/lootbox/energy?address=${address}`);
      const data = await res.json();
      console.log("⚡ [Energy] Estado recibido del backend:", data);
      if (data && typeof data.current_energy === 'number') {
        const newEnergy = data.current_energy;
        const oldEnergy = energy.current;
        
        console.log(`⚡ [Energy] Actualizando: ${oldEnergy} -> ${newEnergy}`);
        
        // Detectar si se consumió energía
        if (oldEnergy > newEnergy && oldEnergy > 0) {
          console.log(`⚡ [Energy] Energía consumida detectada: ${oldEnergy} -> ${newEnergy}`);
          setEnergyConsumed(true);
          setPreviousEnergy(oldEnergy);
        }
        
        setEnergy({
          current: newEnergy,
          max: data.max_energy || 3,
          seconds: data.seconds_to_refill || 0,
          bolts: data.bolts || []
        });
        console.log(`⚡ [Energy] Estado actualizado: ${newEnergy}/${data.max_energy || 3} rayos`);
      }
    } catch (e) {
      console.error("Failed to fetch energy", e);
    }
  };

  // Función para volver a la pantalla principal
  const handleReset = () => {
    setResult(null);
    setPendingResult(null);
    setError(null);
    setIsLoading(false);
    setProgressStep('idle');
    setIsAnimationComplete(false);
    setEnergyConsumed(false);
    
    // NO limpiar energyFromResponse inmediatamente - mantener el estado actual
    // Solo consultar el endpoint si pasaron más de 5 segundos desde la última actualización
    const timeSinceResponse = energyFromResponse ? Date.now() - energyFromResponse.timestamp : Infinity;
    
    if (timeSinceResponse < 5000) {
      // Usar el estado que ya tenemos (de la respuesta del backend)
      console.log("🔄 [Reset] Usando estado de energía de la respuesta reciente, no consultando endpoint");
      // El estado de energía ya está actualizado desde la respuesta, no necesitamos consultar
    } else {
      // Si pasó mucho tiempo, consultar el endpoint para obtener estado actualizado
      console.log("🔄 [Reset] Consultando endpoint para obtener estado actualizado de energía...");
      setEnergyFromResponse(null); // Limpiar para permitir consulta fresca
      fetchEnergy(true);
      setTimeout(() => fetchEnergy(true), 300);
      setTimeout(() => fetchEnergy(true), 800);
    }
  };

  useEffect(() => {
    if (address) {
      // Solo consultar energía inicialmente, luego el polling cada 60s
      // Pero no sobrescribir si tenemos energía reciente de la respuesta
      fetchEnergy(true); // Forzar consulta inicial
      // Poll every 60s to sync (pero respetará energyFromResponse)
      const interval = setInterval(() => fetchEnergy(false), 60000);
      return () => clearInterval(interval);
    }
  }, [address]);

  // NO refrescar energía automáticamente cuando hay resultado
  // El estado de energía ya viene en la respuesta del backend (energy_status)
  // Solo refrescar si hay error o si pasaron más de 10 segundos desde la respuesta
  useEffect(() => {
    if (error) {
      // Si hay error, intentar obtener energía del endpoint
      fetchEnergy(true);
    }
    // Si hay resultado exitoso, la energía ya viene en energy_status, no consultar
  }, [result, error]);

  const handleRechargeShare = async () => {
    const text = `¡Estoy ganando recompensas crypto en Premio.xyz! 🏆\n\nMira si eres elegible por tu actividad en Farcaster. 👇`;
    const embed = "https://celo-build-web-8rej.vercel.app";
    const warpcastUrl = `https://warpcast.com/~/compose?text=${encodeURIComponent(text)}&embeds[]=${encodeURIComponent(embed)}`;

    // Try Farcaster SDK first (Mobile native)
    try {
      const { sdk } = await import("@farcaster/miniapp-sdk");
      sdk.actions.openUrl(warpcastUrl);
    } catch (e) {
      // Fallback to window.open (Web)
      window.open(warpcastUrl, "_blank");
    }

    // Call Verification API
    setIsLoading(true);
    const btn = document.getElementById('recharge-btn');
    if (btn) btn.innerText = "Verificando en Farcaster...";

    const verifyWithRetry = async (attempts = 5, delay = 2000) => {
      for (let i = 0; i < attempts; i++) {
        if (btn) btn.innerText = `Verificando (${i + 1}/${attempts})...`;

        try {
          await new Promise(r => setTimeout(r, delay));
          if (!address) throw new Error("No wallet connected");

          const response = await fetch("/api/lootbox/verify-recharge", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              address: address,
              fid: farcasterUser.fid ? Number(farcasterUser.fid) : undefined
            }),
          });

          const data = await response.json();

          if (data.verified) {

            setShowRechargeModal(false);
            setVerificationError(null);

            setShowThankYou(true);
            setTimeout(() => {
              setShowThankYou(false);
            }, 4000);

            return true;
          } else {
            setVerificationError(data.message || "No encontramos tu cast. Asegúrate de incluir 'premio.xyz' en el texto.");
          }
        } catch (e) {
          console.error("Verification attempt failed:", e);
          setVerificationError("Error de conexión. Intenta de nuevo.");
        }
      }
      return false;
    };

    verifyWithRetry().then((success) => {
      if (!success && !verificationError) {
        setVerificationError("Intentos agotados. Verifica que tu cast sea público.");
      }
    }).finally(() => setIsLoading(false));
  };




  const formatTimeRemaining = (ms: number) => {
    const hours = Math.floor(ms / (1000 * 60 * 60));
    const minutes = Math.floor((ms % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((ms % (1000 * 60)) / 1000);
    return `${hours}h ${minutes}m ${seconds}s`;
  };

  const handleAnalyzeAndClaim = async () => {
    if (!address) return;

    setIsLoading(true);
    setIsAnimationComplete(false);
    setPendingResult(null);
    setResult(null);
    setError(null);
    
    // Start UI Sequence
    setProgressStep('scanning');
    
    try {
    const payload: LootboxEventPayload = {
        frameId: undefined,
      channelId: "global",
      trendScore: 0,
        targetAddress: address,
        targetFid: farcasterUser.fid ? Number(farcasterUser.fid) : undefined,
      };

      console.log("🚀 Enviando solicitud de análisis y recompensa:", payload);

      // Start API call in background with timeout
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 120000); // 2 minutos timeout
      
      const apiPromise = fetch("/api/lootbox", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        signal: controller.signal,
      }).then(response => {
        clearTimeout(timeoutId);
        console.log(`📡 [API] Respuesta recibida: ${response.status} ${response.statusText}`);
        if (!response.ok) {
          console.error(`❌ [API] Error en respuesta: ${response.status}`);
        }
        return response;
      }).catch(error => {
        clearTimeout(timeoutId);
        if (error.name === 'AbortError') {
          console.error("⏱️ [API] Timeout: La solicitud tardó más de 2 minutos");
          throw new Error("La solicitud está tardando demasiado. Por favor intenta de nuevo.");
        }
        console.error("❌ [API] Error en fetch:", error);
        throw error;
      });

      // Enforce minimum durations for each step (Sequential UX)
      // Step 1: Scanning (5s)
      await new Promise(resolve => setTimeout(resolve, 5000));
      setProgressStep('analyzing');

      // Step 2: Analyzing (3s)
      await new Promise(resolve => setTimeout(resolve, 3000));
      setProgressStep('verifying');

      // Step 3: Verifying (3s)
      await new Promise(resolve => setTimeout(resolve, 3000));
      setProgressStep('sending');

      // Wait for API response (if not already done)
      console.log("⏳ [API] Esperando respuesta del backend...");
      const response = await apiPromise;
      console.log(`📥 [API] Respuesta recibida: ${response.status}`);
      
      let resultData;
      try {
        const responseText = await response.text();
        console.log(`📄 [API] Body recibido (primeros 500 chars):`, responseText.substring(0, 500));
        resultData = JSON.parse(responseText);
      } catch (parseError) {
        console.error("❌ [API] Error parseando respuesta JSON:", parseError);
        throw new Error("Error parseando respuesta del servidor");
      }
      
      console.log("✅ [API] Resultado parseado:", resultData);

      if (!response.ok) {
        const errorMessage = resultData?.error || resultData?.detail || "Error en la solicitud";
        if (errorMessage.includes("Backend no configurado")) {
          throw new Error("Error de configuración del backend. Por favor contacta al administrador.");
        }
        throw new Error(errorMessage);
      }

      // CRITICAL: Usar el estado de energía de la respuesta del backend directamente
      // Esto evita problemas de persistencia en serverless donde /tmp no persiste entre invocaciones
      if (resultData?.energy_status) {
        const energyStatus = resultData.energy_status;
        console.log("⚡ [Energy] Estado recibido de la respuesta del backend:", energyStatus);
        
        if (energyStatus && typeof energyStatus.current_energy === 'number') {
          const newEnergy = energyStatus.current_energy;
          const oldEnergy = energy.current;
          
          console.log(`⚡ [Energy] Actualizando desde respuesta: ${oldEnergy} -> ${newEnergy}`);
          
          // Actualizar estado de energía directamente desde la respuesta
          setEnergy({
            current: newEnergy,
            max: energyStatus.max_energy || 3,
            seconds: energyStatus.seconds_to_refill || 0,
            bolts: energyStatus.bolts || []
          });
          
          // Marcar que tenemos energía de la respuesta (para evitar sobrescribir con consultas)
          // Esto asegura que el estado se mantenga correctamente
          setEnergyFromResponse({
            value: newEnergy,
            timestamp: Date.now()
          });
          
          // Log para debugging
          console.log(`⚡ [Energy] Estado guardado desde respuesta: ${newEnergy}/${energyStatus.max_energy || 3}, bolts:`, energyStatus.bolts?.length || 0);
          
          // Detectar si se consumió energía
          if (oldEnergy > newEnergy && oldEnergy > 0) {
            console.log(`⚡ [Energy] Energía consumida detectada: ${oldEnergy} -> ${newEnergy}`);
            setEnergyConsumed(true);
            setPreviousEnergy(oldEnergy);
          }
        }
      } else {
        // Fallback: intentar obtener energía del endpoint si no viene en la respuesta
        console.log("⚠️ [Energy] No se recibió energy_status en la respuesta, consultando endpoint...");
        await fetchEnergy();
        setTimeout(() => fetchEnergy(), 1000);
      }

      setPendingResult(resultData);
      setProgressStep('completed');

      // Trigger XP refresh
      if (typeof window !== 'undefined') {
        console.log("🎁 Reward processed. Triggering XP refresh...");
        window.dispatchEvent(new Event('refresh-xp'));
      }

    } catch (err) {
      console.error("❌ Error:", err);
      setError(err instanceof Error ? err.message : "Hubo un problema procesando tu solicitud");
      setProgressStep('idle');
    }
  };

  const renderLoaderStep = () => {
    switch (progressStep) {
      case 'scanning':
        return (
          <div className="flex flex-col items-center justify-center py-10 space-y-6 animate-in fade-in zoom-in duration-500">
            <div className="relative">
              <div className="absolute inset-0 bg-green-500/20 dark:bg-[#FCFF52]/20 rounded-full animate-ping" />
              <div className="relative h-20 w-20 bg-white/80 dark:bg-black/50 rounded-full border border-green-500/30 dark:border-[#FCFF52]/30 flex items-center justify-center backdrop-blur-md">
                <TrendingUp className="h-10 w-10 text-green-600 dark:text-[#FCFF52] animate-pulse" />
              </div>
            </div>
            <div className="text-center space-y-2">
              <h3 className="text-xl font-bold text-white">{t("form_status_scan")}</h3>
              <p className="text-sm text-gray-400">{t("overlay_step1")}</p>
            </div>
          </div>
        );
      case 'analyzing':
        return (
          <div className="flex flex-col items-center justify-center py-10 space-y-6 animate-in fade-in zoom-in duration-500">
            <div className="relative">
              <div className="absolute inset-0 bg-blue-500/20 rounded-full animate-pulse" />
              <div className="relative h-20 w-20 bg-black/50 rounded-full border border-blue-500/30 flex items-center justify-center backdrop-blur-md">
                <Sparkles className="h-10 w-10 text-blue-400 animate-spin-slow" />
              </div>
            </div>
            <div className="text-center space-y-2">
              <h3 className="text-xl font-bold text-white">{t("form_status_analysis")}</h3>
              <p className="text-sm text-gray-400">{t("overlay_step2")}</p>
            </div>
          </div>
        );
      case 'verifying':
        return (
          <div className="flex flex-col items-center justify-center py-10 space-y-6 animate-in fade-in zoom-in duration-500">
            <div className="relative">
              <div className="absolute inset-0 bg-purple-500/20 rounded-full animate-pulse" />
              <div className="relative h-20 w-20 bg-black/50 rounded-full border border-purple-500/30 flex items-center justify-center backdrop-blur-md">
                <Box className="h-10 w-10 text-purple-400 animate-bounce" />
              </div>
            </div>
            <div className="text-center space-y-2">
              <h3 className="text-xl font-bold text-white">{t("form_status_verify")}</h3>
              <p className="text-sm text-gray-400">{t("overlay_step3")}</p>
            </div>
          </div>
        );
      case 'sending':
        return (
          <div className="flex flex-col items-center justify-center py-10 space-y-6 animate-in fade-in zoom-in duration-500">
            <div className="relative">
              <div className="absolute inset-0 bg-green-500/20 rounded-full animate-pulse" />
              <div className="relative h-20 w-20 bg-black/50 rounded-full border border-green-500/30 flex items-center justify-center backdrop-blur-md">
                <Gift className="h-10 w-10 text-green-400 animate-pulse" />
              </div>
            </div>
            <div className="text-center space-y-2">
              <h3 className="text-xl font-bold text-white">{t("form_status_send")}</h3>
              <p className="text-sm text-gray-400">{t("overlay_step4")}</p>
              <p className="text-[10px] text-gray-500 pt-2 animate-pulse">
                {t("form_status_verify")}...
              </p>
            </div>
          </div>
        );
      default:
        return null;
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
      <Card className="w-full bg-white/80 dark:bg-black/60 border-neutral-200 dark:border-white/10 backdrop-blur-2xl shadow-xl dark:shadow-[0_0_50px_-12px_rgba(252,255,82,0.15)] overflow-hidden relative group ring-1 ring-black/5 dark:ring-white/5">
        <div className="absolute inset-0 bg-gradient-to-b from-white/5 via-transparent to-transparent opacity-50" />
        <div className="absolute inset-0 bg-[url('/grid-pattern.svg')] opacity-10" />

        <CardHeader className="relative z-10 pb-0 pt-4">
          <CardTitle className="flex items-center gap-2 text-lg text-neutral-900 dark:text-white font-bold tracking-tight">
            <div className="p-1.5 rounded-lg bg-green-600/10 dark:bg-[#FCFF52]/10 ring-1 ring-green-600/20 dark:ring-[#FCFF52]/20">
              <Sparkles className="w-4 h-4 text-green-600 dark:text-[#FCFF52] animate-pulse" />
            </div>
            Verificar Elegibilidad
          </CardTitle>
          <CardDescription className="text-gray-500 dark:text-gray-400 text-sm">
            {t("hero_description")}
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-6 relative z-10 pt-4">
          {!isConnected ? (
            <div className="py-8 px-4 rounded-xl bg-black/5 dark:bg-white/5 border border-black/10 dark:border-white/10 text-center space-y-3 hover:bg-black/10 dark:hover:bg-white/10 transition-colors group/connect">
              <div className="h-12 w-12 rounded-full bg-white/50 dark:bg-white/5 flex items-center justify-center mx-auto group-hover/connect:scale-110 transition-transform duration-500">
                <Wallet className="w-6 h-6 text-gray-500 group-hover/connect:text-black dark:group-hover/connect:text-white transition-colors" />
              </div>
              <div className="space-y-0.5">
                <p className="text-neutral-900 dark:text-white font-medium text-base">{t("nav_connect")}</p>
                <p className="text-xs text-gray-500">Minipay / Valora</p>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Info Panel - Only show if not loading or if result is ready */}
              {!isLoading && !result && (
                <div className="rounded-xl bg-white/50 dark:bg-black/40 border border-neutral-200 dark:border-white/10 overflow-hidden">
                  {/* Wallet Row */}
                  <div className="p-3 border-b border-neutral-200 dark:border-white/5 flex items-center justify-between group/item hover:bg-black/5 dark:hover:bg-white/5 transition-colors">
                    <div className="flex items-center gap-2">
                      <div className="p-1 rounded-md bg-blue-500/10 text-blue-400">
                        <Wallet className="w-3.5 h-3.5" />
                      </div>
                      <span className="text-xs text-gray-500 dark:text-gray-400 font-medium">Wallet</span>
                    </div>
                    <span className="font-mono text-green-700 dark:text-[#FCFF52] bg-green-600/10 dark:bg-[#FCFF52]/10 px-2 py-0.5 rounded-full text-[10px] border border-green-600/20 dark:border-[#FCFF52]/20 shadow-sm dark:shadow-[0_0_10px_rgba(252,255,82,0.1)]">
                      {address?.slice(0, 6)}...{address?.slice(-4)}
                    </span>
                  </div>

                  {/* Farcaster Row */}
                  {farcasterUser.username && (
                    <div className="p-3 flex items-center justify-between group/item hover:bg-black/5 dark:hover:bg-white/5 transition-colors">
                      <div className="flex items-center gap-2">
                        <div className="p-1 rounded-md bg-purple-500/10 text-purple-400">
                          <TrendingUp className="w-3.5 h-3.5" />
                        </div>
                        <span className="text-xs text-gray-400 font-medium">Farcaster</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <span className="text-xs font-medium text-neutral-900 dark:text-white">@{farcasterUser.username}</span>
                        {farcasterUser.fid && (
                          <span className="text-[9px] text-gray-400 bg-white/10 px-1.5 py-px rounded-full border border-white/10">
                            FID: {farcasterUser.fid}
                          </span>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Loader Steps */}
              {isLoading && renderLoaderStep()}

              {!result && !isLoading && (
                <>
                  <div className="mb-4 flex flex-col items-center gap-3">
                    <EnergyDisplay
                      currentEnergy={energy.current}
                      maxEnergy={energy.max}
                      secondsToRefill={energy.seconds}
                      bolts={energy.bolts}
                    />
                  </div>

                  <Button
                    className={`w-full font-black h-14 text-lg shadow-lg dark:shadow-[0_0_30px_rgba(252,255,82,0.3)] transition-all duration-300 rounded-xl relative overflow-hidden group/btn ${energy.current === 0
                      ? "bg-amber-500 hover:bg-amber-600 dark:bg-orange-500 dark:hover:bg-orange-600 text-white animate-pulse"
                      : "bg-green-600 dark:bg-[#FCFF52] hover:bg-green-700 dark:hover:bg-[#e6e945] text-white dark:text-black hover:shadow-xl dark:hover:shadow-[0_0_50px_rgba(252,255,82,0.5)]"
                      }`}
                    onClick={() => {
                      if (energy.current > 0) {
                        handleAnalyzeAndClaim();
                      } else {
                        setShowRechargeModal(true);
                      }
                    }}
                    disabled={isLoading}
                  >
                    {energy.current === 0 ? (
                      <div className="relative flex items-center justify-center gap-2">
                        <Zap className="h-5 w-5 fill-current" />
                        <span>⚡ Recargar Ahora</span>
                      </div>
                ) : (
                <>
                        <div className="absolute inset-0 bg-white/20 translate-y-full group-hover/btn:translate-y-0 transition-transform duration-300" />
                        <div className="relative flex items-center justify-center gap-2">
                          <Gift className="h-5 w-5 group-hover/btn:rotate-12 transition-transform" />
                          <span>{t("form_analyze_btn")}</span>
                        </div>
                      </>
                    )}
                  </Button>
                </>
                )}

              {/* Recharge Modal Overlay */}
              {showRechargeModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
                  <div className="bg-background border border-border w-full max-w-sm rounded-2xl p-6 shadow-2xl relative overflow-hidden">

                    {/* Background FX */}
                    <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-amber-500 to-transparent" />
                    <div className="absolute -top-10 -right-10 w-32 h-32 bg-amber-500/10 rounded-full blur-3xl" />

                    <div className="text-center space-y-4 relative z-10">
                      <div className="w-16 h-16 bg-amber-500/10 rounded-full flex items-center justify-center mx-auto border border-amber-500/20">
                        <Zap className="w-8 h-8 text-amber-500" />
                      </div>

                      <div>
                        <h3 className="text-xl font-bold text-foreground">¡Sin Energía! 🔋</h3>
                        <p className="text-sm text-muted-foreground mt-2">
                          Debes esperar <span className="font-mono font-bold text-amber-500">{formatTimeRemaining(energy.seconds * 1000)}</span> para el siguiente loot.
                        </p>
                        <p className="text-sm font-medium text-foreground mt-4">
                          ¿Quieres recargar instantáneamente?
                        </p>
                      </div>

                      <div className="pt-2 space-y-3">
                        <Button
                          className="w-full bg-[#855DCD] hover:bg-[#7C55C3] text-white font-bold gap-2"
                          onClick={handleRechargeShare}
                          id="recharge-btn"
                        >
                          <TrendingUp className="w-4 h-4" />
                          Compartir para Recargar
                        </Button>

                        <Button
                          variant="ghost"
                          className="w-full text-muted-foreground hover:text-foreground"
                          onClick={() => setShowRechargeModal(false)}
                        >
                          Esperar
            </Button>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Thank You Message Overlay */}
              {showThankYou && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/90 backdrop-blur-md animate-in fade-in duration-500">
                  <div className="flex flex-col items-center justify-center space-y-6 text-center animate-in zoom-in slide-in-from-bottom-10 duration-500">
                    <div className="relative">
                      <div className="absolute inset-0 bg-green-500/30 rounded-full animate-ping blur-xl" />
                      <div className="relative h-24 w-24 bg-[#FCFF52]/10 rounded-full flex items-center justify-center border border-[#FCFF52]/50 shadow-[0_0_30px_rgba(252,255,82,0.3)]">
                        <Sparkles className="w-12 h-12 text-[#FCFF52] animate-pulse" />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <h2 className="text-3xl font-black text-white tracking-tight">
                        ¡Energía Recargada!
                      </h2>
                      <p className="text-lg text-green-300 font-medium max-w-xs mx-auto">
                        Gracias por compartir Premio.xyz
                      </p>
                    </div>
                  </div>
                </div>
              )}


            </div>
          )}
        </CardContent>
      </Card>

      {/* Result Display */}
      {result && (
        <div className="mt-8 space-y-6 animate-in fade-in slide-in-from-bottom-8 duration-700">
          {/* Mensaje de energía consumida después de obtener recompensa - SIEMPRE visible cuando hay resultado exitoso */}
          {result.eligible !== false && result.mode !== "failed" && (
            <div className="animate-in fade-in slide-in-from-top-2 duration-300 bg-gradient-to-br from-amber-500/20 via-amber-500/10 to-transparent border border-amber-500/40 rounded-xl px-4 py-4 text-center mb-4 shadow-lg shadow-amber-500/20">
              <div className="flex items-center justify-center gap-2 text-amber-400 mb-3">
                <Zap className="w-6 h-6 animate-pulse" />
                <span className="text-base font-bold">
                  ⚡ Rayo de Energía Consumido
                </span>
              </div>
              <p className="text-sm text-amber-300/90 mb-3 font-medium">
                Has usado <strong className="text-[#FCFF52]">1 rayo</strong> de tus {energy.max} rayos para obtener esta recompensa
              </p>
              
              {/* Estado actual de rayos */}
              <div className="bg-black/40 rounded-lg p-3 mb-3 border border-amber-500/20">
                <div className="flex items-center justify-center gap-2 mb-2">
                  <span className="text-xs text-amber-400/80">Rayos disponibles:</span>
                  <span className="text-lg font-bold text-[#FCFF52]">{energy.current}/{energy.max}</span>
                </div>
                
                {/* Mostrar cuenta regresiva de rayos consumidos */}
                {energy.bolts && energy.bolts.some(b => !b.available) && (
                  <div className="mt-2 pt-2 border-t border-amber-500/20">
                    <p className="text-[10px] text-amber-400/70 mb-2">Próximas recargas:</p>
                    <div className="flex flex-wrap items-center justify-center gap-2">
                      {energy.bolts
                        .filter(b => !b.available && b.seconds_to_refill > 0)
                        .map((bolt, idx) => {
                          const minutes = Math.floor(bolt.seconds_to_refill / 60);
                          const seconds = bolt.seconds_to_refill % 60;
                          return (
                            <div key={idx} className="flex items-center gap-1 text-[10px] bg-black/60 px-2 py-1 rounded border border-amber-500/30">
                              <Zap className="w-3 h-3 text-gray-500" />
                              <span className="text-amber-300 font-mono">
                                {minutes}m {seconds.toString().padStart(2, '0')}s
                              </span>
                            </div>
                          );
                        })}
                    </div>
                  </div>
                )}
              </div>
              
              <p className="text-[10px] text-amber-400/60 italic">
                💡 Cada rayo se recarga automáticamente 60 minutos después de ser consumido
              </p>
            </div>
          )}
          
          {/* Mostrar display de energía actualizado después de consumir - SIEMPRE visible cuando hay resultado exitoso */}
          {result.eligible !== false && result.mode !== "failed" && (
            <div className="mb-4">
              <EnergyDisplay
                currentEnergy={energy.current}
                maxEnergy={energy.max}
                secondsToRefill={energy.seconds}
                bolts={energy.bolts}
              />
            </div>
          )}

          {/* Success Card - PREMIUM REDESIGN */}
          {result.eligible !== false && result.mode !== "failed" && result.mode !== "analysis_only" && (
            <div className="relative rounded-3xl overflow-hidden p-1 p-gradient-to-br from-green-500/50 via-[#FCFF52]/50 to-green-900/50 shadow-2xl shadow-green-900/40 group/card">
              <div className="absolute inset-0 bg-gradient-to-br from-green-500/20 via-[#FCFF52]/10 to-transparent blur-xl opacity-50 animate-pulse" />
              <div className="relative bg-[#0a0a0a] rounded-[22px] p-6 sm:p-8 flex flex-col items-center text-center overflow-hidden">
                  {/* Background Effects */}
                  <div className="absolute inset-0 bg-[url('/grid-pattern.svg')] opacity-[0.03]" />
                  <div className="absolute top-[-50%] left-[-50%] w-[200%] h-[200%] bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-green-500/5 via-transparent to-transparent animate-spin-slow-reverse opacity-50" />

                {/* 1. HEADER & HERO XP */}
                <div className="relative z-10 space-y-2 mb-6 sm:mb-8">
                  <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-green-500/10 border border-green-500/20 text-green-400 text-[10px] font-bold uppercase tracking-widest mb-2">
                    <Sparkles className="w-3 h-3" />
                    {getRewardDisplay(result.reward_type).title}
                  </div>

                  {result.xp_granted !== undefined && (
                    <div className="relative">
                      <h2 className="text-6xl sm:text-7xl font-black text-transparent bg-clip-text bg-gradient-to-b from-[#FCFF52] to-yellow-600 drop-shadow-[0_2px_10px_rgba(252,255,82,0.3)] filter">
                        +{result.xp_granted}
                      </h2>
                      <span className="text-xl font-bold text-yellow-500/80 tracking-widest uppercase mt-[-10px] block">
                        XP Ganados
                      </span>
                    </div>
                  )}
                </div>

                {/* 2. NFT SHOWCASE (If available) */}
                {result.nft_images && (
                  (() => {
                    const userAddress = address?.toLowerCase();
                    const imageUri = Object.entries(result.nft_images || {}).find(([addr]) => addr.toLowerCase() === userAddress)?.[1]
                      || Object.values(result.nft_images || {})[0];

                    if (imageUri) {
                      return (
                        <div className="relative w-full max-w-[240px] aspect-[2/3] rounded-xl overflow-hidden border border-white/10 shadow-2xl mb-8 group-hover/card:scale-[1.02] transition-transform duration-500">
                          <img
                            src={imageUri}
                            alt="Legendary Artifact"
                            className="w-full h-full object-cover"
                          />
                          {/* Rare Badge */}
                          <div className="absolute top-2 right-2">
                            <span className="bg-black/60 backdrop-blur-md text-[#FCFF52] text-[10px] font-bold px-2 py-0.5 rounded border border-[#FCFF52]/30">
                              RARE
                            </span>
                          </div>
                        </div>
                      );
                    }
                    return null;
                  })()
                )}

                {/* 2.5 BONUS REWARD SUMMARY (NEW) */}
                {(result.cast_text || result.xp_granted) && (
                  <div className="w-full max-w-sm bg-white/5 border border-white/10 rounded-xl p-4 mb-6 backdrop-blur-sm">

                    {/* Cast Quote */}
                    {result.cast_text && (
                      <div className="mb-4 text-left">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2 text-muted-foreground">
                            <div className="p-1 bg-blue-500/20 rounded-lg">
                              <MessageSquare className="w-3 h-3 text-blue-400" />
                            </div>
                            <span className="text-xs font-medium uppercase tracking-wider">Cast Premiado</span>
                          </div>
                          {result.cast_hash && result.user_analysis?.username && (
                            <span
                              onClick={() => {
                                const username = result.user_analysis?.username || 'unknown';
                                const hash = result.cast_hash ? result.cast_hash.substring(0, 10) : '';
                                const url = `https://warpcast.com/${username}/${hash}`;
                                import("@farcaster/miniapp-sdk").then(({ sdk }) => {
                                  sdk.actions.openUrl(url);
                                }).catch(() => {
                                  window.open(url, "_blank");
                                });
                              }}
                              className="flex items-center gap-1 text-[10px] text-blue-400 hover:text-blue-300 hover:underline cursor-pointer"
                            >
                              Ver en Farcaster <ExternalLink className="w-3 h-3" />
                            </span>
                          )}
                        </div>
                        <div className="relative pl-3 border-l-2 border-green-500/50">
                          <p className="text-sm text-gray-300 italic line-clamp-3">
                            "{result.cast_text}"
                          </p>
                        </div>
                      </div>
                    )}

                    {/* XP Row */}
                    {result.xp_granted !== undefined && (
                      <div className="flex items-center justify-between bg-black/40 rounded-lg p-3 border border-white/5">
                        <div className="flex items-center gap-2">
                          <Sparkles className="w-4 h-4 text-[#FCFF52]" />
                          <span className="text-sm font-bold text-gray-200">Recompensa Extra</span>
                        </div>
                        <span className="text-[#FCFF52] font-mono font-bold">+{result.xp_granted} XP</span>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}

            {/* 3. PRIMARY ACTION (Share) */}
            {result.eligible !== false && result.mode !== "failed" && result.mode !== "analysis_only" && (
              <Button
                className="w-full bg-[#855DCD] hover:bg-[#7C55C3] text-white font-bold h-12 sm:h-14 text-base sm:text-lg rounded-xl shadow-lg shadow-purple-500/20 mb-3 group/share relative overflow-hidden"
                onClick={() => {
                  const score = result.user_analysis?.score?.toFixed(0) || "0";
                  const rewardName = getRewardDisplay(result.reward_type).title;
                  const rewardVal = result.xp_granted ? `${result.xp_granted} XP` : rewardName;
                  const username = result.user_analysis?.username || "Explorer";

                  const appUrl = "https://celo-build-web-8rej.vercel.app";
                  const victoryUrl = `${appUrl}/share/victory?user=${encodeURIComponent(username)}&xp=${result.xp_granted || 0}&score=${score}&reward=${encodeURIComponent(result.reward_type || 'XP')}&locale=es`;

                  const text = `¡Victoria! He ganado ${rewardVal} en Premio.xyz 🏆\n\nReclama tu recompensa aquí 👇`;
                  const warpcastUrl = `https://warpcast.com/~/compose?text=${encodeURIComponent(text)}&embeds[]=${encodeURIComponent(victoryUrl)}`;

                  import("@farcaster/miniapp-sdk").then(({ sdk }) => {
                    sdk.actions.openUrl(warpcastUrl);
                  }).catch(() => {
                    window.open(warpcastUrl, "_blank");
                  });
                }}
              >
                <div className="absolute inset-0 bg-white/20 translate-y-full group-hover/share:translate-y-0 transition-transform duration-300" />
                <div className="relative flex items-center justify-center gap-2">
                  <TrendingUp className="w-5 h-5" />
                  Presumir Victoria
                </div>
              </Button>
            )}

            {/* 4. SECONDARY ACTION (View Tx) */}
            {result.explorer_url && result.eligible !== false && result.mode !== "failed" && result.mode !== "analysis_only" && (
              <a
                href={result.explorer_url}
                target="_blank"
                rel="noopener noreferrer"
                className="relative z-20 text-xs text-gray-500 hover:text-green-400 transition-colors flex items-center justify-center gap-1 group/link p-2"
              >
                Ver Transacción en Bloque
                <ExternalLink className="w-3 h-3 opacity-50 group-hover/link:opacity-100" />
              </a>
            )}

            {/* 5. BOTÓN VOLVER A OBTENER RECOMPENSA */}
            {result.eligible !== false && result.mode !== "failed" && result.mode !== "analysis_only" && (
              <Button
                onClick={handleReset}
                className="w-full mt-4 bg-gray-700 hover:bg-gray-600 text-white font-bold h-12 text-base rounded-xl shadow-lg transition-all duration-300"
              >
                <Gift className="w-5 h-5 mr-2" />
                Volver a Obtener Recompensa
              </Button>
            )}
          </div>
        )}

      {/* NOTE: Viral Score Analysis section removed as per user request to avoid confusion. */}

      {/* BOTÓN REINICIAR ELIMINADO para evitar spam y forzar cooldown en la UI principal */}

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
        // Check for specific "already rewarded" error
        result.error?.includes("already rewarded") ? (
          <div className="mt-6 rounded-xl bg-blue-500/10 border border-blue-500/30 p-5 text-blue-200 space-y-3 animate-in fade-in slide-in-from-bottom-4 duration-300">
            <div className="flex items-center gap-2">
              <div className="h-8 w-8 rounded-full bg-blue-500/20 flex items-center justify-center">
                <span className="text-blue-400 text-lg">ℹ️</span>
              </div>
              <h4 className="font-bold text-base text-blue-100">¡Ya premiamos este Cast!</h4>
            </div>
            <p className="text-sm text-blue-200/80 pl-10">
              Tu último cast ya se convirtió en NFT. <br />
              <strong>¡Publica algo nuevo en Farcaster para ganar otro premio!</strong>
            </p>
          </div>
        ) : (
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
        )
      )}
    </div>
  );
}
