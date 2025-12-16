"use client";

import { useState, useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { CastGenerator } from "@/components/cast-generator";
import { useAccount } from "wagmi";
import { useFarcasterUser } from "@/components/farcaster-provider";
import { Sparkles, Info, PlayCircle } from "lucide-react";
import { useLanguage } from "@/components/language-provider";
import { cn } from "@/lib/utils";

export default function CastsPage() {
  const { t } = useLanguage();
  const router = useRouter();
  const pathname = usePathname();
  const { address, isConnected } = useAccount();
  const farcasterUser = useFarcasterUser();
  const [activeTab, setActiveTab] = useState<"app" | "guide" | "casts">("casts");

  // Sincronizar activeTab con la ruta actual
  useEffect(() => {
    if (pathname === "/casts") {
      setActiveTab("casts");
    } else if (pathname === "/") {
      setActiveTab("app");
    }
  }, [pathname]);

  // Componente de navegación compartido
  const NavigationTabs = () => (
    <div className="container px-4 mx-auto max-w-md mt-6 mb-6">
      <div className="grid grid-cols-3 p-1 bg-muted rounded-xl">
        <button
          onClick={() => {
            setActiveTab("app");
            router.push("/");
          }}
          className={cn(
            "flex items-center justify-center gap-2 py-2.5 text-sm font-medium rounded-lg transition-all",
            activeTab === "app"
              ? "bg-background text-foreground shadow-sm"
              : "text-muted-foreground hover:text-foreground"
          )}
        >
          <PlayCircle className="w-4 h-4" />
          {t("nav_home")}
        </button>
        <button
          onClick={() => {
            setActiveTab("casts");
            router.push("/casts");
          }}
          className={cn(
            "flex items-center justify-center gap-2 py-2.5 text-sm font-medium rounded-lg transition-all",
            activeTab === "casts"
              ? "bg-background text-foreground shadow-sm"
              : "text-muted-foreground hover:text-foreground"
          )}
        >
          <Sparkles className="w-4 h-4" />
          {t("nav_casts")}
        </button>
        <button
          onClick={() => {
            setActiveTab("guide");
            router.push("/");
            setTimeout(() => {
              const guideElement = document.getElementById("guide-section");
              if (guideElement) {
                guideElement.scrollIntoView({ behavior: "smooth" });
              }
            }, 100);
          }}
          className={cn(
            "flex items-center justify-center gap-2 py-2.5 text-sm font-medium rounded-lg transition-all",
            activeTab === "guide"
              ? "bg-background text-foreground shadow-sm"
              : "text-muted-foreground hover:text-foreground"
          )}
        >
          <Info className="w-4 h-4" />
          {t("nav_guide")}
        </button>
      </div>
    </div>
  );

  if (!isConnected || !address) {
    return (
      <main className="flex-1 bg-background min-h-screen pb-20">
        <NavigationTabs />
        <div className="container px-4 mx-auto max-w-md py-12">
          <div className="text-center space-y-4">
            <div className="relative h-24 w-24 mx-auto mb-6">
              <div className="absolute inset-0 bg-primary/20 rounded-full animate-pulse" />
              <div className="relative h-24 w-24 bg-background/80 rounded-full border border-primary/30 flex items-center justify-center backdrop-blur-md">
                <Sparkles className="h-12 w-12 text-primary" />
              </div>
            </div>
            <h1 className="text-2xl font-bold">{t("cast_generate_title")}</h1>
            <p className="text-muted-foreground">
              {t("cast_page_connect_wallet")}
            </p>
          </div>
        </div>
      </main>
    );
  }

  if (!farcasterUser?.fid) {
    return (
      <main className="flex-1 bg-background min-h-screen pb-20">
        <NavigationTabs />
        <div className="container px-4 mx-auto max-w-md py-12">
          <div className="text-center space-y-4">
            <div className="relative h-24 w-24 mx-auto mb-6">
              <div className="absolute inset-0 bg-primary/20 rounded-full animate-pulse" />
              <div className="relative h-24 w-24 bg-background/80 rounded-full border border-primary/30 flex items-center justify-center backdrop-blur-md">
                <Sparkles className="h-12 w-12 text-primary" />
              </div>
            </div>
            <h1 className="text-2xl font-bold">{t("cast_generate_title")}</h1>
            <p className="text-muted-foreground">
              {t("cast_page_farcaster_required")}
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
            <h1 className="text-2xl font-bold mb-2">{t("cast_generate_title")}</h1>
            <p className="text-sm text-muted-foreground">
              {t("cast_page_description")}
            </p>
          </div>
        </div>
      </div>

      {/* Tab Navigation (Segmented Control) */}
      <NavigationTabs />

      {/* Content */}
      <div className="container px-4 mx-auto max-w-md animate-in fade-in slide-in-from-bottom-4 duration-500">
        <CastGenerator 
          userAddress={address}
          userFid={farcasterUser.fid}
        />
      </div>
    </main>
  );
}

