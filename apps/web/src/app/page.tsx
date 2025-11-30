import Link from "next/link";
import { Zap, Workflow } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { UserBalance } from "@/components/user-balance";
import { TrendingCampaignForm } from "@/components/trending-campaign-form";

export default function Home() {
  return (
    <main className="flex-1">
      {/* Hero Section */}
      <section className="relative py-20 lg:py-32">
        <div className="container px-4 mx-auto max-w-6xl">
          <div className="text-center max-w-4xl mx-auto">
            <div className="inline-flex items-center gap-2 px-3 py-1 mb-8 text-sm font-medium bg-primary/10 text-primary rounded-full border border-primary/20">
              <Zap className="h-4 w-4" />
              Built on Celo + MiniPay
            </div>

            <h1 className="text-4xl md:text-6xl font-bold tracking-tight mb-6">
              Loot boxes sociales para comunidades Farcaster
            </h1>
            <p className="text-lg md:text-xl text-muted-foreground mb-8 max-w-2xl mx-auto leading-relaxed">
              Detecta conversaciones trending, filtra elegibles on-chain y reparte micropagos/cNFTs en MiniPay con un
              pipeline multiagente.
            </p>

            <UserBalance />

            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-16">
              <Button size="lg" className="px-8 py-3 text-base font-medium" asChild>
                <Link href="https://docs.celo.org/build/build-on-minipay/overview" target="_blank">
                  Leer docs de MiniPay
                </Link>
              </Button>
            </div>
          </div>
          <TrendingCampaignForm />
        </div>
      </section>

      {/* Architecture snapshot */}
      <section className="py-16 border-t border-border/40 bg-muted/10">
        <div className="container px-4 mx-auto max-w-6xl grid gap-8 md:grid-cols-2 items-center">
          <Card className="p-6 space-y-4">
            <div className="flex items-center gap-3 text-primary">
              <Workflow className="h-6 w-6" />
              <p className="uppercase tracking-wide text-xs font-semibold">Pipeline</p>
            </div>
            <h2 className="text-2xl font-semibold">Cadena de agentes</h2>
            <p className="text-muted-foreground">
              LangGraph coordina TrendWatcher → Eligibility → RewardDistributor. Cada agente consume herramientas
              dedicadas (Warpcast API, Celo RPC, MiniPay Tool) para decidir campañas, validar reputación y ejecutar
              recompensas.
            </p>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li>• TrendWatcher analiza frames y genera `campaignId`</li>
              <li>• Eligibility consulta `LootAccessRegistry` + señales sociales</li>
              <li>• RewardDistributor llama al vault y a MiniPay Tool</li>
            </ul>
          </Card>

          <div className="space-y-6">
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-2">Contratos Foundry</h3>
              <p className="text-sm text-muted-foreground">
                `LootBoxVault` maneja presupuestos ERC20, `LootAccessRegistry` aplica cooldown y reputación. Scripts de
                deploy (`LootBoxDeployer.s.sol`) listos para Alfajores.
              </p>
            </Card>
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-2">Integración MiniPay</h3>
              <p className="text-sm text-muted-foreground">
                El frontend expone un endpoint `/api/lootbox` que reenvía eventos al servicio Python. Desde ahí se
                orquesta MiniPay Tool para notificar y distribuir loot boxes.
              </p>
            </Card>
          </div>
        </div>
      </section>
    </main>
  );
}
