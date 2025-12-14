"use client";

import { useState, useEffect } from "react";
import { Loader2, Sparkles, Calendar, Send, Wallet, CheckCircle2, XCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useWriteContract, useWaitForTransactionReceipt } from "wagmi";
import { parseEther, formatEther } from "viem";
import { STABLE_TOKEN_ADDRESSES } from "@/lib/minipay";
import { stableTokenABI } from "@celo/abis";
import { cn } from "@/lib/utils";
import { getBackendUrl } from "@/lib/backend";

const TOPICS = {
  tech: { name: "Tech", emoji: "💻", description: "Tecnología, blockchain, Web3" },
  musica: { name: "Música", emoji: "🎵", description: "Música, artistas, canciones" },
  motivacion: { name: "Motivación", emoji: "🚀", description: "Superación personal, crecimiento" },
  chistes: { name: "Chistes", emoji: "😂", description: "Humor, memes, contenido divertido" },
  frases_celebres: { name: "Frases Célebres", emoji: "💬", description: "Citas inspiradoras" },
} as const;

type Topic = keyof typeof TOPICS;

interface CastGeneratorProps {
  userAddress: string;
  userFid: number;
}

export function CastGenerator({ userAddress, userFid }: CastGeneratorProps) {
  const [selectedTopic, setSelectedTopic] = useState<Topic>("tech");
  const [generatedCast, setGeneratedCast] = useState<string>("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [agentAddress, setAgentAddress] = useState<string>("");
  const [isLoadingAddress, setIsLoadingAddress] = useState(true);
  const [scheduledTime, setScheduledTime] = useState<string>("");
  const [isPublishing, setIsPublishing] = useState(false);
  const [publishError, setPublishError] = useState<string | null>(null);
  const [publishSuccess, setPublishSuccess] = useState(false);

  // Wagmi hooks para transacciones
  const { writeContract, data: hash, isPending: isPendingTx } = useWriteContract();
  const { isLoading: isConfirming, isSuccess: isConfirmed } = useWaitForTransactionReceipt({
    hash,
  });

  // Cargar dirección del agente al montar
  useEffect(() => {
    const fetchAgentAddress = async () => {
      try {
        const backendUrl = getBackendUrl();
        if (!backendUrl) {
          setPublishError("Backend no configurado. Verifica NEXT_PUBLIC_AGENT_SERVICE_URL");
          setIsLoadingAddress(false);
          return;
        }

        const response = await fetch(`${backendUrl}/api/casts/agent-address`);
        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(`Error obteniendo dirección del agente: ${response.status} ${errorText}`);
        }
        
        const data = await response.json();
        setAgentAddress(data.agent_address);
        setPublishError(null); // Limpiar error si se carga correctamente
      } catch (error: any) {
        console.error("Error obteniendo dirección del agente:", error);
        setPublishError(error.message || "Error conectando con el backend");
      } finally {
        setIsLoadingAddress(false);
      }
    };

    fetchAgentAddress();
  }, []); // Solo ejecutar una vez al montar

  const handleGenerate = async () => {
    setIsGenerating(true);
    setGeneratedCast("");
    setPublishError(null);
    setPublishSuccess(false);

    try {
      const backendUrl = getBackendUrl();
      if (!backendUrl) {
        throw new Error("Backend no configurado. Verifica NEXT_PUBLIC_AGENT_SERVICE_URL");
      }

      const response = await fetch(`${backendUrl}/api/casts/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          topic: selectedTopic,
          user_address: userAddress,
          user_fid: userFid,
        }),
      });

      if (!response.ok) {
        let errorMessage = "Error generando cast";
        try {
          const error = await response.json();
          errorMessage = error.detail || error.message || errorMessage;
        } catch {
          errorMessage = `Error ${response.status}: ${response.statusText}`;
        }
        throw new Error(errorMessage);
      }

      const data = await response.json();
      setGeneratedCast(data.cast_text || "");
    } catch (error: any) {
      console.error("Error generando cast:", error);
      setPublishError(error.message || "Error generando cast");
    } finally {
      setIsGenerating(false);
    }
  };

  const handlePublish = async () => {
    if (!generatedCast || !agentAddress) return;

    setIsPublishing(true);
    setPublishError(null);
    setPublishSuccess(false);

    try {
      // Precio: 0.5 cUSD = 500000000000000000 wei
      const amount = parseEther("0.5");

      // Transferir cUSD al agente
      writeContract({
        address: STABLE_TOKEN_ADDRESSES.cUSD as `0x${string}`,
        abi: stableTokenABI,
        functionName: "transfer",
        args: [agentAddress as `0x${string}`, amount],
      });
    } catch (error: any) {
      setPublishError(error.message || "Error iniciando pago");
      setIsPublishing(false);
    }
  };

  // Cuando la transacción se confirma, publicar el cast
  useEffect(() => {
    if (isConfirmed && hash && generatedCast && !publishSuccess) {
      const publishCast = async () => {
        setIsPublishing(true);
        try {
          const backendUrl = getBackendUrl();
          if (!backendUrl) {
            throw new Error("Backend no configurado. Verifica NEXT_PUBLIC_AGENT_SERVICE_URL");
          }

          const scheduledDateTime = scheduledTime 
            ? new Date(scheduledTime).toISOString()
            : null;

          const response = await fetch(`${backendUrl}/api/casts/publish`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              topic: selectedTopic,
              cast_text: generatedCast,
              user_address: userAddress,
              user_fid: userFid,
              payment_tx_hash: hash,
              scheduled_time: scheduledDateTime,
            }),
          });

          if (!response.ok) {
            let errorMessage = "Error publicando cast";
            try {
              const error = await response.json();
              errorMessage = error.detail || error.message || errorMessage;
            } catch {
              errorMessage = `Error ${response.status}: ${response.statusText}`;
            }
            throw new Error(errorMessage);
          }

          const data = await response.json();
          setPublishSuccess(true);
          setPublishError(null);
          // Limpiar después de 3 segundos para permitir ver el mensaje de éxito
          setTimeout(() => {
            setGeneratedCast("");
            setScheduledTime("");
            setPublishSuccess(false);
          }, 3000);
        } catch (error: any) {
          console.error("Error publicando cast:", error);
          setPublishError(error.message || "Error publicando cast");
          setPublishSuccess(false);
        } finally {
          setIsPublishing(false);
        }
      };

      publishCast();
    }
  }, [isConfirmed, hash]); // Solo ejecutar cuando se confirma la transacción

  return (
    <div className="space-y-6">
      {/* Selección de Tema */}
      <Card className="border-white/5 bg-background/50 backdrop-blur-sm">
        <CardHeader>
          <CardTitle className="text-lg">Selecciona un Tema</CardTitle>
          <CardDescription className="text-xs">Elige el tema para tu cast</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-3">
            {(Object.keys(TOPICS) as Topic[]).map((topic) => {
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
          <CardTitle className="text-lg">Generar Cast con IA</CardTitle>
          <CardDescription className="text-xs">
            Usa inteligencia artificial para crear contenido viral
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
                Generando...
              </>
            ) : (
              <>
                <Sparkles className="mr-2 h-5 w-5" />
                Generar Cast
              </>
            )}
          </Button>

          {generatedCast && (
            <div className="space-y-4">
              <div>
                <Label>Cast Generado</Label>
                <Textarea
                  value={generatedCast}
                  readOnly
                  className="mt-2 min-h-[100px]"
                />
                <div className="text-xs text-muted-foreground mt-1">
                  {generatedCast.length}/320 caracteres
                </div>
              </div>

              {/* Programar Cast (Opcional) */}
              <div>
                <Label htmlFor="scheduled-time">
                  Programar para más tarde (Opcional)
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
                    Se publicará el {new Date(scheduledTime).toLocaleString()}
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
                    {isPendingTx || isConfirming ? "Confirmando pago..." : "Publicando..."}
                  </>
                ) : (
                  <>
                    <Send className="mr-2 h-4 w-4" />
                    Publicar por 0.5 cUSD
                  </>
                )}
              </Button>

              {publishSuccess && (
                <div className="flex items-center gap-2 text-green-600 dark:text-green-400">
                  <CheckCircle2 className="h-5 w-5" />
                  <span>¡Cast publicado exitosamente! Ganaste 100 XP</span>
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
              <div className="font-semibold text-base">Precio: 0.5 cUSD</div>
              <div className="text-sm text-muted-foreground">
                Por cada cast publicado recibirás <span className="font-semibold text-primary">100 XP</span> como recompensa
              </div>
              {isLoadingAddress && (
                <div className="text-xs text-muted-foreground flex items-center gap-2 mt-2">
                  <Loader2 className="h-3 w-3 animate-spin" />
                  Cargando dirección del agente...
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

