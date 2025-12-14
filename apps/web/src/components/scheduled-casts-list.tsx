"use client";

import { useState, useEffect } from "react";
import { Loader2, Calendar, X, CheckCircle2, Clock, XCircle, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getBackendUrl } from "@/lib/backend";

interface ScheduledCast {
  cast_id: string;
  topic: string;
  cast_text: string;
  scheduled_time: string;
  status: "scheduled" | "published" | "cancelled" | "failed";
  published_cast_hash: string | null;
  xp_granted: number;
  created_at: string;
  error_message: string | null;
}

interface ScheduledCastsListProps {
  userAddress: string;
}

export function ScheduledCastsList({ userAddress }: ScheduledCastsListProps) {
  const [casts, setCasts] = useState<ScheduledCast[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchCasts = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const backendUrl = getBackendUrl();
      if (!backendUrl) {
        throw new Error("Backend no configurado. Verifica NEXT_PUBLIC_AGENT_SERVICE_URL");
      }

      const response = await fetch(
        `${backendUrl}/api/casts/scheduled?user_address=${encodeURIComponent(userAddress)}`
      );

      if (!response.ok) {
        let errorMessage = "Error obteniendo casts programados";
        try {
          const error = await response.json();
          errorMessage = error.detail || error.message || errorMessage;
        } catch {
          errorMessage = `Error ${response.status}: ${response.statusText}`;
        }
        throw new Error(errorMessage);
      }

      const data = await response.json();
      setCasts(data.casts || []);
    } catch (err: any) {
      console.error("Error cargando casts programados:", err);
      setError(err.message || "Error cargando casts programados");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchCasts();
    // Refrescar cada 30 segundos
    const interval = setInterval(fetchCasts, 30000);
    return () => clearInterval(interval);
  }, [userAddress]);

  const handleCancel = async (castId: string) => {
    try {
      const backendUrl = getBackendUrl();
      if (!backendUrl) {
        throw new Error("Backend no configurado. Verifica NEXT_PUBLIC_AGENT_SERVICE_URL");
      }

      const response = await fetch(`${backendUrl}/api/casts/cancel`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          cast_id: castId,
          user_address: userAddress,
        }),
      });

      if (!response.ok) {
        let errorMessage = "Error cancelando cast";
        try {
          const error = await response.json();
          errorMessage = error.detail || error.message || errorMessage;
        } catch {
          errorMessage = `Error ${response.status}: ${response.statusText}`;
        }
        throw new Error(errorMessage);
      }

      // Refrescar lista
      fetchCasts();
    } catch (err: any) {
      console.error("Error cancelando cast:", err);
      alert(err.message || "Error cancelando cast");
    }
  };

  const getStatusIcon = (status: ScheduledCast["status"]) => {
    switch (status) {
      case "published":
        return <CheckCircle2 className="h-4 w-4 text-green-600" />;
      case "scheduled":
        return <Clock className="h-4 w-4 text-blue-600" />;
      case "cancelled":
        return <XCircle className="h-4 w-4 text-gray-600" />;
      case "failed":
        return <XCircle className="h-4 w-4 text-red-600" />;
    }
  };

  const getStatusText = (status: ScheduledCast["status"]) => {
    switch (status) {
      case "published":
        return "Publicado";
      case "scheduled":
        return "Programado";
      case "cancelled":
        return "Cancelado";
      case "failed":
        return "Error";
    }
  };

  if (isLoading) {
    return (
      <Card className="border-white/5 bg-background/50 backdrop-blur-sm">
        <CardContent className="pt-6">
          <div className="flex items-center justify-center py-12">
            <div className="relative">
              <div className="absolute inset-0 bg-primary/20 rounded-full animate-pulse" />
              <div className="relative">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="border-white/5 bg-background/50 backdrop-blur-sm">
        <CardContent className="pt-6">
          <div className="text-center py-8">
            <XCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
            <div className="text-red-600 dark:text-red-400 font-semibold">{error}</div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (casts.length === 0) {
    return (
      <Card className="border-white/5 bg-background/50 backdrop-blur-sm">
        <CardContent className="pt-6">
          <div className="text-center py-12 space-y-4">
            <div className="relative h-16 w-16 mx-auto">
              <div className="absolute inset-0 bg-primary/20 rounded-full animate-pulse" />
              <div className="relative h-16 w-16 bg-background/80 rounded-full border border-primary/30 flex items-center justify-center backdrop-blur-md">
                <Calendar className="h-8 w-8 text-primary" />
              </div>
            </div>
            <div className="space-y-2">
              <div className="font-semibold text-lg">No tienes casts programados</div>
              <div className="text-sm text-muted-foreground">
                Genera un cast y programa su publicación para más tarde
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {casts.map((cast) => (
        <Card 
          key={cast.cast_id}
          className="border-white/5 bg-background/50 backdrop-blur-sm"
        >
          <CardHeader>
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-2">
                {getStatusIcon(cast.status)}
                <CardTitle className="text-lg">{getStatusText(cast.status)}</CardTitle>
              </div>
              {cast.status === "scheduled" && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleCancel(cast.cast_id)}
                  className="h-8 w-8 p-0"
                >
                  <X className="h-4 w-4" />
                </Button>
              )}
            </div>
            <CardDescription className="text-xs">
              <div className="flex items-center gap-2 mt-2">
                <Calendar className="h-3 w-3" />
                {new Date(cast.scheduled_time).toLocaleString()}
              </div>
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm mb-4 leading-relaxed">{cast.cast_text}</p>
            <div className="flex items-center justify-between text-xs">
              <div className="text-muted-foreground">Tema: <span className="font-semibold capitalize">{cast.topic}</span></div>
              {cast.xp_granted > 0 && (
                <div className="flex items-center gap-1 text-green-600 dark:text-green-400 font-semibold">
                  <Sparkles className="h-3 w-3" />
                  +{cast.xp_granted} XP
                </div>
              )}
            </div>
            {cast.error_message && (
              <div className="mt-3 p-2 rounded-lg bg-red-500/10 border border-red-500/20 text-xs text-red-600 dark:text-red-400">
                {cast.error_message}
              </div>
            )}
            {cast.published_cast_hash && (
              <div className="mt-2 text-xs text-muted-foreground font-mono">
                Hash: {cast.published_cast_hash.slice(0, 10)}...
              </div>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

