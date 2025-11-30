"use client";

import { useState } from "react";
import { Loader2, Send } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import type { AgentRunResponse, LootboxEventPayload } from "@/lib/lootbox";
import { DEFAULT_EVENT } from "@/lib/lootbox";

type FormState = {
  frameId: string;
  channelId: string;
  trendScore: number;
};

export function TrendingCampaignForm() {
  const [form, setForm] = useState<FormState>({
    frameId: DEFAULT_EVENT.frameId,
    channelId: DEFAULT_EVENT.channelId,
    trendScore: DEFAULT_EVENT.trendScore,
  });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AgentRunResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleChange = (key: keyof FormState) => (event: React.ChangeEvent<HTMLInputElement>) => {
    const value = key === "trendScore" ? Number(event.target.value) : event.target.value;
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setResult(null);
    setError(null);
    const payload: LootboxEventPayload = {
      frameId: form.frameId.trim(),
      channelId: form.channelId.trim(),
      trendScore: Number(form.trendScore),
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
  }

  return (
    <Card className="p-6 space-y-6 border-primary/20 bg-primary/5">
      <div className="space-y-2">
        <p className="text-sm uppercase tracking-wide text-primary">Simula una campaña</p>
        <h2 className="text-2xl font-semibold">Prueba el pipeline multiagente</h2>
        <p className="text-muted-foreground text-sm">
          Envía un frame trending y observa cómo el backend orquesta TrendWatcher → Eligibility → RewardDistributor.
        </p>
      </div>

      <form className="grid gap-4 md:grid-cols-3" onSubmit={handleSubmit}>
        <div className="space-y-2">
          <label className="text-sm font-medium">Frame ID</label>
          <Input value={form.frameId} onChange={handleChange("frameId")} placeholder="example-frame" required />
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium">Channel</label>
          <Input value={form.channelId} onChange={handleChange("channelId")} placeholder="builders" required />
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium">Trend score</label>
          <Input
            type="number"
            step="0.01"
            min="0"
            max="1"
            value={form.trendScore}
            onChange={handleChange("trendScore")}
            required
          />
        </div>

        <div className="md:col-span-3 flex justify-end">
          <Button type="submit" disabled={loading}>
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Orquestando...
              </>
            ) : (
              <>
                Ejecutar agente
                <Send className="ml-2 h-4 w-4" />
              </>
            )}
          </Button>
        </div>
      </form>

      {result && (
        <div className="rounded-lg border border-primary/30 bg-background/80 p-4 text-sm">
          <p className="font-semibold text-primary">Thread ID</p>
          <p className="break-all text-muted-foreground">{result.thread_id}</p>
          <p className="font-semibold text-primary mt-4">Resumen</p>
          <p className="text-muted-foreground">{result.summary}</p>
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-destructive/40 bg-destructive/10 p-4 text-sm text-destructive">
          {error}
        </div>
      )}
    </Card>
  );
}

