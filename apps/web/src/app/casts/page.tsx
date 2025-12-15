"use client";

import { CastGenerator } from "@/components/cast-generator";
import { useAccount } from "wagmi";
import { useFarcasterUser } from "@/components/farcaster-provider";
import { Sparkles } from "lucide-react";
import { useLanguage } from "@/components/language-provider";

export default function CastsPage() {
  const { t } = useLanguage();
  const { address, isConnected } = useAccount();
  const farcasterUser = useFarcasterUser();

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

