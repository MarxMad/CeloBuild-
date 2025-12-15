"use client";

import { useState, useEffect } from "react";
import { Loader2, Sparkles, Calendar, Send, Wallet, CheckCircle2, XCircle, AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useSendTransaction, useWaitForTransactionReceipt } from "wagmi";
import { parseEther, formatEther } from "viem";
import { cn } from "@/lib/utils";
import { getBackendUrl } from "@/lib/backend";
import { useLanguage } from "@/components/language-provider";

type Topic = "tech" | "musica" | "motivacion" | "chistes" | "frases_celebres";

// TOPICS se define dentro del componente para acceder a t()
const getTopics = (t: (key: string) => string) => ({
  tech: { name: t("topic_tech"), emoji: "💻", description: t("topic_tech_desc") },
  musica: { name: t("topic_musica"), emoji: "🎵", description: t("topic_musica_desc") },
  motivacion: { name: t("topic_motivacion"), emoji: "🚀", description: t("topic_motivacion_desc") },
  chistes: { name: t("topic_chistes"), emoji: "😂", description: t("topic_chistes_desc") },
  frases_celebres: { name: t("topic_frases_celebres"), emoji: "💬", description: t("topic_frases_celebres_desc") },
} as const);

interface CastGeneratorProps {
  userAddress: string;
  userFid: number;
}

export function CastGenerator({ userAddress, userFid }: CastGeneratorProps) {
  const { t, locale } = useLanguage();
  const [selectedTopic, setSelectedTopic] = useState<Topic>("tech");
  const [generatedCast, setGeneratedCast] = useState<string>("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [agentAddress, setAgentAddress] = useState<string>("");
  const [isLoadingAddress, setIsLoadingAddress] = useState(true);
  const [scheduledTime, setScheduledTime] = useState<string>("");
  const [isPublishing, setIsPublishing] = useState(false);
  const [publishError, setPublishError] = useState<string | null>(null);
  const [publishSuccess, setPublishSuccess] = useState(false);
  const [txHash, setTxHash] = useState<string | null>(null);
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [xpGranted, setXpGranted] = useState<number>(0);
  const [publishedCastHash, setPublishedCastHash] = useState<string | null>(null);

  // Wagmi hooks para transacciones de CELO nativo
  const { sendTransaction, data: hash, isPending: isPendingTx } = useSendTransaction();
  const { isLoading: isConfirming, isSuccess: isConfirmed } = useWaitForTransactionReceipt({
    hash,
  });

  // Logs de estado de transacción
  useEffect(() => {
    if (hash) {
      console.log("📝 [CastGenerator] Hash de transacción:", hash);
    }
    if (isPendingTx) {
      console.log("⏳ [CastGenerator] Transacción pendiente...");
    }
    if (isConfirming) {
      console.log("⏳ [CastGenerator] Confirmando transacción...");
    }
    if (isConfirmed) {
      console.log("✅ [CastGenerator] Transacción confirmada exitosamente");
    }
  }, [hash, isPendingTx, isConfirming, isConfirmed]);

  // Cargar dirección del agente al montar
  useEffect(() => {
    const fetchAgentAddress = async () => {
      console.log("🔍 [CastGenerator] Cargando dirección del agente...");
      try {
        const backendUrl = getBackendUrl();
        if (!backendUrl) {
          console.error("❌ [CastGenerator] Backend no configurado");
          setPublishError(t("cast_error_backend"));
          setIsLoadingAddress(false);
          return;
        }

        console.log(`📡 [CastGenerator] Llamando a ${backendUrl}/api/casts/agent-address`);
        const response = await fetch(`${backendUrl}/api/casts/agent-address`);
        if (!response.ok) {
          const errorText = await response.text();
          console.error(`❌ [CastGenerator] Error ${response.status}: ${errorText}`);
          throw new Error(`${t("cast_error_address")} ${response.status} ${errorText}`);
        }
        
        const data = await response.json();
        console.log("✅ [CastGenerator] Dirección del agente obtenida:", data.agent_address);
        setAgentAddress(data.agent_address);
        setPublishError(null); // Limpiar error si se carga correctamente
      } catch (error: any) {
        console.error("❌ [CastGenerator] Error obteniendo dirección del agente:", error);
        setPublishError(error.message || t("cast_error_address"));
      } finally {
        setIsLoadingAddress(false);
      }
    };

    fetchAgentAddress();
  }, []); // Solo ejecutar una vez al montar

  const handleGenerate = async () => {
    if (!agentAddress) {
      console.warn("⚠️ [CastGenerator] No se puede generar: dirección del agente faltante");
      setPublishError(t("cast_error_address"));
      return;
    }
    
    // Mostrar diálogo de confirmación de pago antes de generar
    setShowConfirmDialog(true);
  };

  const handleConfirmPaymentAndGenerate = async () => {
    setShowConfirmDialog(false);
    console.log("💰 [CastGenerator] Iniciando pago de 0.5 CELO para generar cast...");
    setIsGenerating(true);
    setIsPublishing(true);
    setPublishError(null);
    setPublishSuccess(false);
    setGeneratedCast("");
    setXpGranted(0);
    setPublishedCastHash(null);
    setTxHash(null);

    try {
      // Precio: 0.5 CELO nativo
      const amount = parseEther("0.5");
      
      console.log("📝 [CastGenerator] Enviando transacción:", { to: agentAddress, value: amount.toString() });
      
      sendTransaction({
        to: agentAddress as `0x${string}`,
        value: amount,
      });
      
      console.log("✅ [CastGenerator] Transacción enviada, esperando confirmación...");
    } catch (error: any) {
      console.error("❌ [CastGenerator] Error iniciando pago:", error);
      setPublishError(error.message || t("cast_error_payment"));
      setIsGenerating(false);
      setIsPublishing(false);
    }
  };

  const handlePublish = async () => {
    if (!generatedCast) {
      console.warn("⚠️ [CastGenerator] No se puede publicar: cast faltante");
      return;
    }
    
    console.log("📤 [CastGenerator] Abriendo Warpcast composer y otorgando XP...");
    setIsPublishing(true);
    setPublishError(null);
    
    try {
      // Abrir Warpcast composer con el texto del cast
      const warpcastUrl = `https://warpcast.com/~/compose?text=${encodeURIComponent(generatedCast)}`;

      try {
        const { sdk } = await import("@farcaster/miniapp-sdk");
        sdk.actions.openUrl(warpcastUrl);
      } catch (e) {
        // Fallback para web
        window.open(warpcastUrl, "_blank");
      }

      // Otorgar XP directamente (sin verificar publicación)
      const backendUrl = getBackendUrl();
      if (!backendUrl) {
        throw new Error(t("cast_error_backend"));
      }

      const response = await fetch(`${backendUrl}/api/casts/grant-xp`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_address: userAddress,
        }),
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({ message: response.statusText }));
        throw new Error(error.message || "Error otorgando XP");
      }

      const data = await response.json();
      
      if (data.success) {
        console.log("✅ [CastGenerator] XP otorgado exitosamente:", data.xp_granted);
        setXpGranted(data.xp_granted || 25);
        setPublishSuccess(true);
        setPublishError(null);
        
        // Disparar evento para refrescar XP en el dashboard
        window.dispatchEvent(new Event('refresh-xp'));
      } else {
        throw new Error(data.message || "Error otorgando XP");
      }
    } catch (error: any) {
      console.error("❌ [CastGenerator] Error publicando:", error);
      setPublishError(error.message || "Error al publicar");
    } finally {
      setIsPublishing(false);
    }
  };

  const handleConfirmPayment = async () => {
    setShowConfirmDialog(false);
    console.log("💰 [CastGenerator] Iniciando pago de 0.5 CELO a:", agentAddress);
    setIsPublishing(true);
    setPublishError(null);
    setPublishSuccess(false);

    try {
      // Precio: 0.5 CELO nativo
      const amount = parseEther("0.5");
      console.log("📝 [CastGenerator] Enviando transacción:", { to: agentAddress, value: amount.toString() });

      // Transferir CELO nativo al agente
      sendTransaction({
        to: agentAddress as `0x${string}`,
        value: amount,
        // Agregar descripción para que el wallet muestre claramente el monto
        data: undefined, // No hay data, es una transferencia simple
      });
      console.log("✅ [CastGenerator] Transacción enviada, esperando confirmación...");
    } catch (error: any) {
      console.error("❌ [CastGenerator] Error iniciando pago:", error);
      setPublishError(error.message || t("cast_error_payment"));
      setIsPublishing(false);
    }
  };

  // Guardar hash de la transacción cuando se confirma
  useEffect(() => {
    if (isConfirmed && hash) {
      console.log("✅ [CastGenerator] Transacción confirmada:", hash);
      setTxHash(hash);
    }
  }, [isConfirmed, hash]);

  // Cuando la transacción se confirma, generar el cast automáticamente
  useEffect(() => {
    if (isConfirmed && hash && !generatedCast && isGenerating) {
      const generateCastAfterPayment = async () => {
        console.log("✅ [CastGenerator] Transacción confirmada, generando cast...");
        
        try {
          const backendUrl = getBackendUrl();
          if (!backendUrl) {
            throw new Error(t("cast_error_backend"));
          }

          const payload = {
            topic: selectedTopic,
            user_address: userAddress,
            user_fid: userFid,
          };
          console.log("📤 [CastGenerator] Enviando request a /api/casts/generate:", payload);

          const response = await fetch(`${backendUrl}/api/casts/generate`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
          });

          if (!response.ok) {
            let errorMessage = t("cast_error_generating");
            try {
              const error = await response.json();
              errorMessage = error.detail || error.message || errorMessage;
              console.error("❌ [CastGenerator] Error del backend:", error);
            } catch {
              errorMessage = `Error ${response.status}: ${response.statusText}`;
              console.error(`❌ [CastGenerator] Error ${response.status}: ${response.statusText}`);
            }
            throw new Error(errorMessage);
          }

          const data = await response.json();
          console.log("✅ [CastGenerator] Cast generado exitosamente");
          setGeneratedCast(data.cast_text || "");
          setIsGenerating(false);
          setIsPublishing(false);
        } catch (error: any) {
          console.error("❌ [CastGenerator] Error generando cast:", error);
          setPublishError(error.message || t("cast_error_generating"));
          setIsGenerating(false);
          setIsPublishing(false);
        }
      };

      generateCastAfterPayment();
    }
  }, [isConfirmed, hash, generatedCast, isGenerating, selectedTopic, userAddress, userFid]);


  const TOPICS = getTopics(t as (key: string) => string);

  return (
    <div className="space-y-6">
      {/* Selección de Tema */}
      <Card className="border-white/5 bg-background/50 backdrop-blur-sm">
        <CardHeader>
          <CardTitle className="text-lg">{t("cast_select_topic")}</CardTitle>
          <CardDescription className="text-xs">{t("cast_select_topic_desc")}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-3">
            {(Object.keys(TOPICS) as Topic[]).map((topic: Topic) => {
              const topicInfo = TOPICS[topic];
              const isSelected = selectedTopic === topic;
              return (
                <button
                  key={topic}
                  onClick={() => setSelectedTopic(topic)}
                  className={cn(
                    "p-4 rounded-xl border-2 transition-all relative overflow-hidden",
                    isSelected
                      ? "border-primary bg-primary/10 shadow-lg shadow-primary/20"
                      : "border-border/50 bg-background/50 hover:border-primary/50 hover:bg-primary/5"
                  )}
                >
                  {isSelected && (
                    <div className="absolute inset-0 bg-primary/5 animate-pulse" />
                  )}
                  <div className="relative">
                    <div className="text-3xl mb-2">{topicInfo.emoji}</div>
                    <div className="font-semibold text-sm mb-1">{topicInfo.name}</div>
                    <div className="text-xs text-muted-foreground">
                      {topicInfo.description}
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Generar Cast */}
      <Card className="border-white/5 bg-background/50 backdrop-blur-sm">
        <CardHeader>
          <CardTitle className="text-lg">{t("cast_generate_title")}</CardTitle>
          <CardDescription className="text-xs">
            {t("cast_generate_desc")}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Button
            onClick={handleGenerate}
            disabled={isGenerating || isPendingTx || isConfirming || !agentAddress}
            className="w-full h-12 text-base font-semibold"
            size="lg"
          >
            {isGenerating || isPendingTx || isConfirming ? (
              <>
                <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                {isPendingTx || isConfirming ? t("cast_confirming_payment") : t("cast_generating")}
              </>
            ) : (
              <>
                <Sparkles className="mr-2 h-5 w-5" />
                {t("cast_generate_btn")}
              </>
            )}
          </Button>

          {generatedCast && (
            <div className="space-y-4">
              <div>
                <Label>{t("cast_generated")}</Label>
                <div className="mt-2 p-4 rounded-lg border-2 border-primary/50 bg-background/80 backdrop-blur-sm">
                  <p className="text-sm leading-relaxed whitespace-pre-wrap break-words">
                    {generatedCast}
                  </p>
                </div>
                <div className="text-xs text-muted-foreground mt-1">
                  {generatedCast.length}/150 {t("cast_characters")}
                </div>
              </div>

              {/* Programar Cast (Opcional) */}
              <div>
                <Label htmlFor="scheduled-time">
                  {t("cast_schedule_title")}
                </Label>
                <input
                  id="scheduled-time"
                  type="datetime-local"
                  value={scheduledTime}
                  onChange={(e) => setScheduledTime(e.target.value)}
                  min={new Date().toISOString().slice(0, 16)}
                  className="mt-2 w-full px-3 py-2 border border-input bg-background rounded-md text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
                />
                {scheduledTime && (
                  <div className="text-xs text-muted-foreground mt-1">
                    {t("cast_schedule_will_publish")} {new Date(scheduledTime).toLocaleString(locale === 'es' ? 'es-ES' : 'en-US')}
                  </div>
                )}
              </div>

              {/* Publicar */}
              <Button
                onClick={handlePublish}
                disabled={isPublishing || !generatedCast}
                className="w-full"
                size="lg"
              >
                {isPublishing ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    {t("cast_publishing")}
                  </>
                ) : (
                  <>
                    <Send className="mr-2 h-4 w-4" />
                    {t("cast_publish_btn")}
                  </>
                )}
              </Button>

              {/* Comprobante de Publicación Exitosa */}
              {publishSuccess && (
                <div className="mt-6 rounded-2xl bg-gradient-to-br from-green-500/20 via-green-500/10 to-transparent border-2 border-green-500/40 p-6 space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500 relative overflow-hidden">
                  {/* Background Effects */}
                  <div className="absolute top-0 left-0 w-full h-full bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-green-500/5 via-transparent to-transparent opacity-50" />
                  
                  <div className="relative z-10 space-y-4">
                    {/* Header */}
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className="w-10 h-10 rounded-full bg-green-500/20 flex items-center justify-center border border-green-500/30">
                          <CheckCircle2 className="h-6 w-6 text-green-400" />
                        </div>
                        <div>
                          <h3 className="text-lg font-bold text-green-400">¡Cast Publicado!</h3>
                          <p className="text-xs text-muted-foreground">{t("cast_success_note")}</p>
                        </div>
                      </div>
                    </div>

                    {/* XP Otorgado */}
                    {xpGranted > 0 && (
                      <div className="bg-black/40 rounded-xl p-4 border border-green-500/20">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <Sparkles className="w-5 h-5 text-[#FCFF52]" />
                            <span className="text-sm font-semibold text-foreground">XP Otorgado</span>
                          </div>
                          <span className="text-2xl font-black text-[#FCFF52]">+{xpGranted}</span>
                        </div>
                      </div>
                    )}

                    {/* Detalles de Transacciones */}
                    <div className="space-y-2">
                      {/* Pago de 0.5 CELO */}
                      {txHash && (
                        <div className="flex items-center justify-between bg-black/40 rounded-lg p-3 border border-white/10">
                          <div className="flex items-center gap-2">
                            <Wallet className="w-4 h-4 text-primary" />
                            <span className="text-xs font-medium text-muted-foreground">Pago de 0.5 CELO</span>
                          </div>
                          <a
                            href={`https://celoscan.io/tx/${txHash}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-xs text-primary hover:underline flex items-center gap-1"
                          >
                            Ver en CeloScan
                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                            </svg>
                          </a>
                        </div>
                      )}

                      {/* Hash del Cast Publicado */}
                      {publishedCastHash && (
                        <div className="flex items-center justify-between bg-black/40 rounded-lg p-3 border border-white/10">
                          <div className="flex items-center gap-2">
                            <Send className="w-4 h-4 text-blue-400" />
                            <span className="text-xs font-medium text-muted-foreground">Cast Hash</span>
                          </div>
                          <span className="text-xs font-mono text-blue-400 truncate max-w-[120px]">
                            {publishedCastHash.slice(0, 10)}...
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {publishError && (
                <div className="flex items-center gap-2 text-red-600 dark:text-red-400">
                  <XCircle className="h-5 w-5" />
                  <span>{publishError}</span>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Información de Precio */}
      <Card className="border-white/5 bg-background/50 backdrop-blur-sm">
        <CardContent className="pt-6">
          <div className="flex items-start gap-3">
            <div className="relative">
              <div className="absolute inset-0 bg-primary/20 rounded-full animate-pulse" />
              <div className="relative h-10 w-10 bg-background/80 rounded-full border border-primary/30 flex items-center justify-center backdrop-blur-md">
                <Wallet className="h-5 w-5 text-primary" />
              </div>
            </div>
            <div className="space-y-1 flex-1">
              <div className="font-semibold text-base">{t("cast_price")}</div>
              <div className="text-sm text-muted-foreground">
                {t("cast_price_desc")} <span className="font-semibold text-primary">{t("cast_price_xp")}</span> {t("cast_price_reward")}
              </div>
              {isLoadingAddress && (
                <div className="text-xs text-muted-foreground flex items-center gap-2 mt-2">
                  <Loader2 className="h-3 w-3 animate-spin" />
                  {t("cast_loading_address")}
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Modal de Confirmación de Pago */}
      {showConfirmDialog && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="bg-background border border-border w-full max-w-sm rounded-2xl p-6 shadow-2xl relative overflow-hidden">
            {/* Background FX */}
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-primary to-transparent" />
            <div className="absolute -top-10 -right-10 w-32 h-32 bg-primary/10 rounded-full blur-3xl" />

            <div className="text-center space-y-4 relative z-10">
              <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto border border-primary/20">
                <AlertTriangle className="w-8 h-8 text-primary" />
              </div>

              <div>
                <h3 className="text-xl font-bold text-foreground mb-2">{t("cast_confirm_title")}</h3>
                <p className="text-sm text-foreground mb-3">
                  {t("cast_confirm_message_generate") || "Vas a pagar 0.5 CELO para generar este cast con IA."}
                </p>
                <p className="text-sm text-muted-foreground">
                  {t("cast_confirm_details")}
                </p>
              </div>

              <div className="pt-2 space-y-3">
                <Button
                  onClick={handleConfirmPaymentAndGenerate}
                  className="w-full h-12 text-base font-semibold bg-primary hover:bg-primary/90"
                  size="lg"
                >
                  <Wallet className="mr-2 h-5 w-5" />
                  {t("cast_confirm_continue")}
                </Button>
                <Button
                  onClick={() => setShowConfirmDialog(false)}
                  variant="outline"
                  className="w-full"
                  size="lg"
                >
                  {t("cast_confirm_cancel")}
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

