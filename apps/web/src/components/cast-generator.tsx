"use client";

import { useState, useEffect } from "react";
import { Loader2, Sparkles, Calendar, Send, Wallet, CheckCircle2, XCircle } from "lucide-react";
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
    console.log("🎨 [CastGenerator] Iniciando generación de cast para tema:", selectedTopic);
    setIsGenerating(true);
    setGeneratedCast("");
    setPublishError(null);
    setPublishSuccess(false);

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
      console.log("✅ [CastGenerator] Cast generado exitosamente:", data.cast_text?.substring(0, 50) + "...");
      setGeneratedCast(data.cast_text || "");
    } catch (error: any) {
      console.error("❌ [CastGenerator] Error generando cast:", error);
      setPublishError(error.message || t("cast_error_generating"));
    } finally {
      setIsGenerating(false);
    }
  };

  const handlePublish = async () => {
    if (!generatedCast || !agentAddress) {
      console.warn("⚠️ [CastGenerator] No se puede publicar: cast o dirección del agente faltante");
      return;
    }

    console.log("💰 [CastGenerator] Iniciando pago de 1 CELO a:", agentAddress);
    setIsPublishing(true);
    setPublishError(null);
    setPublishSuccess(false);

    try {
      // Precio: 1 CELO nativo
      const amount = parseEther("1");
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

  // Cuando la transacción se confirma, publicar el cast
  useEffect(() => {
    if (isConfirmed && hash && generatedCast && !publishSuccess) {
      const publishCast = async () => {
        console.log("📤 [CastGenerator] Transacción confirmada, publicando cast...");
        console.log("📋 [CastGenerator] Datos:", { hash, castLength: generatedCast.length, scheduledTime });
        setIsPublishing(true);
        try {
          const backendUrl = getBackendUrl();
          if (!backendUrl) {
            throw new Error(t("cast_error_backend"));
          }

          const scheduledDateTime = scheduledTime 
            ? new Date(scheduledTime).toISOString()
            : null;

          const payload = {
            topic: selectedTopic,
            cast_text: generatedCast,
            user_address: userAddress,
            user_fid: userFid,
            payment_tx_hash: hash,
            scheduled_time: scheduledDateTime,
          };
          console.log("📤 [CastGenerator] Enviando request a /api/casts/publish:", { ...payload, cast_text: generatedCast.substring(0, 50) + "..." });

          const response = await fetch(`${backendUrl}/api/casts/publish`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
          });

          if (!response.ok) {
            let errorMessage = t("cast_error_publishing");
            let approvalUrl: string | null = null;
            
            try {
              const error = await response.json();
              errorMessage = error.detail || error.message || errorMessage;
              console.error("❌ [CastGenerator] Error del backend:", error);
              
              // Extraer approval URL si está en el mensaje
              const approvalUrlMatch = errorMessage.match(/https?:\/\/[^\s]+/);
              if (approvalUrlMatch) {
                approvalUrl = approvalUrlMatch[0];
              }
              
              // También verificar header
              const headerApprovalUrl = response.headers.get("X-Approval-URL");
              if (headerApprovalUrl) {
                approvalUrl = headerApprovalUrl;
              }
            } catch {
              errorMessage = `Error ${response.status}: ${response.statusText}`;
              console.error(`❌ [CastGenerator] Error ${response.status}: ${response.statusText}`);
            }
            
            // Si hay approval URL, mostrar mensaje especial
            if (approvalUrl) {
              setPublishError(
                `${t("cast_error_signer_required")}\n\n${t("cast_approval_url")}: ${approvalUrl}`
              );
              // Abrir approval URL en nueva pestaña
              window.open(approvalUrl, "_blank");
            } else {
              setPublishError(errorMessage);
            }
            
            throw new Error(errorMessage);
          }

          const data = await response.json();
          console.log("✅ [CastGenerator] Respuesta del backend:", data);
          
          // Mostrar mensaje de éxito con XP otorgado
          const xpGranted = data.xp_granted || 0;
          console.log(`🎉 [CastGenerator] XP otorgado: ${xpGranted}, Estado: ${data.status}`);
          
          if (xpGranted > 0) {
            console.log("✅ [CastGenerator] Cast publicado exitosamente con XP");
            setPublishSuccess(true);
            setPublishError(null);
          } else {
            // Si no se otorgó XP, puede ser que esté programado o haya un error
            if (data.status === "scheduled") {
              console.log("📅 [CastGenerator] Cast programado exitosamente");
              setPublishSuccess(true);
              setPublishError(null);
            } else {
              console.warn("⚠️ [CastGenerator] Cast publicado pero sin XP:", data);
              setPublishError(data.message || t("cast_error_publishing"));
              setPublishSuccess(false);
            }
          }
          
          // Limpiar después de 5 segundos para permitir ver el mensaje de éxito
          setTimeout(() => {
            console.log("🧹 [CastGenerator] Limpiando estado...");
            setGeneratedCast("");
            setScheduledTime("");
            setPublishSuccess(false);
            setTxHash(null);
          }, 5000);
        } catch (error: any) {
          console.error("❌ [CastGenerator] Error publicando cast:", error);
          setPublishError(error.message || t("cast_error_publishing"));
          setPublishSuccess(false);
        } finally {
          setIsPublishing(false);
        }
      };

      publishCast();
    }
  }, [isConfirmed, hash, generatedCast, publishSuccess]); // Solo ejecutar cuando se confirma la transacción

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
            disabled={isGenerating}
            className="w-full h-12 text-base font-semibold"
            size="lg"
          >
            {isGenerating ? (
              <>
                <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                {t("cast_generating")}
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
                <Textarea
                  value={generatedCast}
                  readOnly
                  className="mt-2 min-h-[80px] max-h-[200px] overflow-y-auto"
                  style={{
                    height: 'auto',
                    minHeight: '80px',
                  }}
                  rows={Math.max(3, Math.ceil(generatedCast.length / 50))}
                />
                <div className="text-xs text-muted-foreground mt-1">
                  {generatedCast.length}/100 {t("cast_characters")}
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
                disabled={isPublishing || isPendingTx || isConfirming || !agentAddress}
                className="w-full"
                size="lg"
              >
                {isPublishing || isPendingTx || isConfirming ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    {isPendingTx || isConfirming ? t("cast_confirming_payment") : t("cast_publishing")}
                  </>
                ) : (
                  <>
                    <Send className="mr-2 h-4 w-4" />
                    {t("cast_publish_btn")}
                  </>
                )}
              </Button>

              {publishSuccess && (
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-green-600 dark:text-green-400">
                    <CheckCircle2 className="h-5 w-5" />
                    <span>{t("cast_published_success")}</span>
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {t("cast_success_note")}
                  </div>
                  {txHash && (
                    <div className="text-sm">
                      <a
                        href={`https://celoscan.io/tx/${txHash}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary hover:underline flex items-center gap-1"
                      >
                        {t("cast_view_tx")}
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                        </svg>
                      </a>
                    </div>
                  )}
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
    </div>
  );
}

