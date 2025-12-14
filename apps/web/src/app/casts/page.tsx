"use client";

import { useState } from "react";
import { CastGenerator } from "@/components/cast-generator";
import { ScheduledCastsList } from "@/components/scheduled-casts-list";
import { useAccount } from "wagmi";
import { useFarcasterUser } from "@/components/farcaster-provider";
import { Sparkles, Calendar } from "lucide-react";
import { cn } from "@/lib/utils";

export default function CastsPage() {
  const { address, isConnected } = useAccount();
  const farcasterUser = useFarcasterUser();
  const [activeTab, setActiveTab] = useState<"generate" | "scheduled">("generate");

  if (!isConnected || !address) {
    return (
      <main className="flex-1 bg-background min-h-screen pb-20">
        <div className="container px-4 mx-auto max-w-md py-12">
          <div className="text-center space-y-4">
            <div className="relative h-24 w-24 mx-auto mb-6">
              <div className="absolute inset-0 bg-primary/20 rounded-full animate-pulse" />
              <div className="relative h-24 w-24 bg-background/80 rounded-full border border-primary/30 flex items-center justify-center backdrop-blur-md">
                <Sparkles className="h-12 w-12 text-primary" />
              </div>
            </div>
            <h1 className="text-2xl font-bold">Generar Casts con IA</h1>
            <p className="text-muted-foreground">
              Conecta tu wallet para generar y programar casts en Farcaster
            </p>
          </div>
        </div>
      </main>
    );
  }

  if (!farcasterUser?.fid) {
    return (
      <main className="flex-1 bg-background min-h-screen pb-20">
        <div className="container px-4 mx-auto max-w-md py-12">
          <div className="text-center space-y-4">
            <div className="relative h-24 w-24 mx-auto mb-6">
              <div className="absolute inset-0 bg-primary/20 rounded-full animate-pulse" />
              <div className="relative h-24 w-24 bg-background/80 rounded-full border border-primary/30 flex items-center justify-center backdrop-blur-md">
                <Sparkles className="h-12 w-12 text-primary" />
              </div>
            </div>
            <h1 className="text-2xl font-bold">Generar Casts con IA</h1>
            <p className="text-muted-foreground">
              Necesitas estar autenticado con Farcaster para generar casts
            </p>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="flex-1 bg-background min-h-screen pb-20">
      {/* Header */}
      <div className="relative overflow-hidden bg-background/50 pb-6 pt-6 rounded-b-[2.5rem] shadow-2xl border-b border-white/5">
        <div className="container px-4 mx-auto max-w-md relative z-10">
          <div className="text-center mb-6">
            <div className="relative h-20 w-20 mx-auto mb-4">
              <div className="absolute inset-0 bg-primary/20 rounded-full animate-pulse" />
              <div className="relative h-20 w-20 bg-background/80 rounded-full border border-primary/30 flex items-center justify-center backdrop-blur-md">
                <Sparkles className="h-10 w-10 text-primary" />
              </div>
            </div>
            <h1 className="text-2xl font-bold mb-2">Generar Casts con IA</h1>
            <p className="text-sm text-muted-foreground">
              Crea contenido viral para Farcaster. Paga 0.5 cUSD y gana 100 XP por cada cast publicado.
            </p>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="container px-4 mx-auto max-w-md mt-6 mb-6">
        <div className="grid grid-cols-2 p-1 bg-muted rounded-xl">
          <button
            onClick={() => setActiveTab("generate")}
            className={cn(
              "flex items-center justify-center gap-2 py-2.5 text-sm font-medium rounded-lg transition-all",
              activeTab === "generate"
                ? "bg-background text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            )}
          >
            <Sparkles className="w-4 h-4" />
            Generar
          </button>
          <button
            onClick={() => setActiveTab("scheduled")}
            className={cn(
              "flex items-center justify-center gap-2 py-2.5 text-sm font-medium rounded-lg transition-all",
              activeTab === "scheduled"
                ? "bg-background text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            )}
          >
            <Calendar className="w-4 h-4" />
            Programados
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="container px-4 mx-auto max-w-md animate-in fade-in slide-in-from-bottom-4 duration-500">
        {activeTab === "generate" ? (
          <CastGenerator 
            userAddress={address}
            userFid={farcasterUser.fid}
          />
        ) : (
          <ScheduledCastsList userAddress={address} />
        )}
      </div>
    </main>
  );
}

