"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { Zap, Info, PlayCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { UserBalance } from "@/components/user-balance";
import { TrendingCampaignForm } from "@/components/trending-campaign-form";
import { Instructions } from "@/components/instructions";
import { AgentVis } from "@/components/agent-vis";
import { Leaderboard } from "@/components/leaderboard";
import { cn } from "@/lib/utils";
import { sdk } from "@farcaster/miniapp-sdk";

export default function Home() {
  const [activeTab, setActiveTab] = useState<"app" | "guide">("app");

  // Asegurar que ready() se llama cuando el contenido está completamente renderizado
  useEffect(() => {
    const ensureReady = async () => {
      try {
        // Esperar un momento para que todo el contenido esté renderizado
        await new Promise((resolve) => setTimeout(resolve, 100));
        await sdk.actions.ready();
      } catch (error) {
        // Ignorar si no estamos en contexto de MiniApp
      }
    };

    ensureReady();
  }, []);

  return (
    <main className="flex-1 bg-background min-h-screen pb-20">
      {/* Mobile-first Header */}
      <div className="relative overflow-hidden bg-background/50 pb-8 pt-6 rounded-b-[2.5rem] shadow-2xl border-b border-white/5">
        <div className="container px-4 mx-auto max-w-md relative z-10">
          <div className="flex items-center justify-center gap-2 mb-4">
             <div className="px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-[10px] font-bold uppercase tracking-wider text-primary">
               MiniPay Ready
             </div>
          </div>
          
          <h1 className="text-4xl font-extrabold text-center tracking-tight mb-2 text-white animate-in fade-in slide-in-from-bottom-2 duration-700 drop-shadow-md">
            Premio.xyz
            <span className="inline-block ml-2 animate-pulse text-[#FCFF52]"></span>
          </h1>
          <p className="text-center text-gray-400 text-sm mb-6">
            Recompensas virales en Farcaster.
          </p>

          {/* Agent Vis - Compact for Mobile */}
          <div className="relative mx-auto w-full h-[180px] mb-4">
            <AgentVis />
            <div className="absolute bottom-0 left-0 right-0 text-center text-[10px] text-muted-foreground/60 uppercase tracking-widest">
               System Online
            </div>
          </div>

          <UserBalance />
        </div>
      </div>

      {/* Tab Navigation (Segmented Control) */}
      <div className="container px-4 mx-auto max-w-md mt-6 mb-6">
        <div className="grid grid-cols-2 p-1 bg-muted rounded-xl">
          <button
            onClick={() => setActiveTab("app")}
            className={cn(
              "flex items-center justify-center gap-2 py-2.5 text-sm font-medium rounded-lg transition-all",
              activeTab === "app" 
                ? "bg-background text-foreground shadow-sm" 
                : "text-muted-foreground hover:text-foreground"
            )}
          >
            <PlayCircle className="w-4 h-4" />
            Simulador
          </button>
          <button
            onClick={() => setActiveTab("guide")}
            className={cn(
              "flex items-center justify-center gap-2 py-2.5 text-sm font-medium rounded-lg transition-all",
              activeTab === "guide" 
                ? "bg-background text-foreground shadow-sm" 
                : "text-muted-foreground hover:text-foreground"
            )}
          >
            <Info className="w-4 h-4" />
            Guía
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="container px-4 mx-auto max-w-md animate-in fade-in slide-in-from-bottom-4 duration-500">
        {activeTab === "app" ? (
          <div className="space-y-8">
            <TrendingCampaignForm />
            
            <Leaderboard />

            <div className="text-center">
              <Button variant="ghost" size="sm" className="text-xs text-muted-foreground" asChild>
                <Link href="https://docs.celo.org/build/build-on-minipay/overview" target="_blank">
                  Powered by Celo MiniPay
                </Link>
              </Button>
            </div>
          </div>
        ) : (
          <div className="pb-10">
            <Instructions />
          </div>
        )}
      </div>
    </main>
  );
}
