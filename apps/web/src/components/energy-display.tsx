"use client";

import { useState, useEffect } from "react";
import { Zap, Info } from "lucide-react";

interface BoltInfo {
  index: number;
  available: boolean;
  seconds_to_refill: number;
  refill_at: number | null;
}

interface EnergyDisplayProps {
  currentEnergy: number;
  maxEnergy: number;
  secondsToRefill: number;
  bolts?: BoltInfo[]; // Información detallada de cada rayo
}

export function EnergyDisplay({ currentEnergy, maxEnergy, secondsToRefill, bolts }: EnergyDisplayProps) {
  const [timeLeft, setTimeLeft] = useState(secondsToRefill);
  const [boltsState, setBoltsState] = useState<BoltInfo[]>(bolts || []);
  const [showInfo, setShowInfo] = useState(false);

  useEffect(() => {
    setTimeLeft(secondsToRefill);
  }, [secondsToRefill]);

  useEffect(() => {
    if (bolts) {
      setBoltsState(bolts);
    }
  }, [bolts]);

  // Actualizar cuenta regresiva de cada rayo cada segundo
  useEffect(() => {
    const interval = setInterval(() => {
      setBoltsState(prev => {
        const now = Date.now() / 1000;
        return prev.map(bolt => {
          if (!bolt.available && bolt.refill_at) {
            const remaining = Math.max(0, Math.floor(bolt.refill_at - now));
            if (remaining === 0) {
              return { ...bolt, available: true, seconds_to_refill: 0, refill_at: null };
            }
            return { ...bolt, seconds_to_refill: remaining };
          }
          return bolt;
        });
      });
      
      if (timeLeft > 0) {
        setTimeLeft(prev => Math.max(0, prev - 1));
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [timeLeft, bolts]);

  const formatTime = (seconds: number) => {
    if (seconds <= 0) return "Listo";
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    if (h > 0) {
      return `${h}h ${m}m`;
    }
    return `${m}m ${s.toString().padStart(2, '0')}s`;
  };

  return (
    <div className="flex flex-col items-center gap-3 w-full">
      {/* Explicación del sistema */}
      <div className="w-full">
        <button
          onClick={() => setShowInfo(!showInfo)}
          className="w-full flex items-center justify-between px-3 py-2 bg-black/20 border border-white/10 rounded-lg hover:bg-black/30 transition-colors"
        >
          <div className="flex items-center gap-2">
            <Zap className="w-4 h-4 text-[#FCFF52]" />
            <span className="text-sm font-medium text-white">
              Sistema de Energía: {currentEnergy}/{maxEnergy} Rayos
            </span>
          </div>
          <Info className={`w-4 h-4 text-gray-400 transition-transform ${showInfo ? 'rotate-180' : ''}`} />
        </button>
        
        {showInfo && (
          <div className="mt-2 p-3 bg-black/30 border border-white/10 rounded-lg text-xs text-gray-300 space-y-2 animate-in fade-in slide-in-from-top-2">
            <p className="font-semibold text-[#FCFF52]">⚡ ¿Cómo funcionan los rayos?</p>
            <ul className="list-disc list-inside space-y-1 ml-2">
              <li>Tienes un máximo de <strong>{maxEnergy} rayos</strong> de energía</li>
              <li>Cada vez que obtienes una recompensa, se consume <strong>1 rayo</strong></li>
              <li>Cada rayo se recarga <strong>independientemente 60 minutos</strong> después de ser consumido</li>
              <li>Si consumes los 3 rayos, se recargan uno por uno cada 60 minutos</li>
            </ul>
          </div>
        )}
      </div>

      {/* Display de rayos con cuenta regresiva */}
      <div className="w-full space-y-2">
        <div className="flex items-center justify-center gap-2 bg-black/40 px-4 py-2 rounded-full border border-white/10 backdrop-blur-sm">
          {Array.from({ length: maxEnergy }).map((_, i) => {
            const boltInfo = boltsState[i] || { available: i < currentEnergy, seconds_to_refill: 0, refill_at: null };
            const isActive = boltInfo.available;

            return (
              <div key={i} className="flex flex-col items-center gap-1">
                <div className="relative">
                  <Zap
                    className={`w-6 h-6 transition-all duration-300 ${
                      isActive
                        ? "text-[#FCFF52] fill-[#FCFF52] drop-shadow-[0_0_8px_rgba(252,255,82,0.6)]"
                        : "text-gray-600 fill-gray-900/50"
                    }`}
                  />
                  {!isActive && (
                    <div className="absolute inset-0 flex items-center justify-center">
                      <div className="w-4 h-4 border-2 border-gray-600 rounded-full animate-spin" />
                    </div>
                  )}
                </div>
                {!isActive && boltInfo.seconds_to_refill > 0 && (
                  <div className="text-[9px] font-mono text-amber-400/80 bg-black/40 px-1.5 py-0.5 rounded">
                    {formatTime(boltInfo.seconds_to_refill)}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Resumen de estado */}
        <div className="text-center">
          {currentEnergy === maxEnergy ? (
            <p className="text-xs text-green-400 font-medium">
              ✅ Todos los rayos disponibles
            </p>
          ) : currentEnergy === 0 ? (
            <p className="text-xs text-amber-400 font-medium">
              ⚠️ Sin rayos disponibles
            </p>
          ) : (
            <p className="text-xs text-[#FCFF52]/80 font-medium">
              {currentEnergy} de {maxEnergy} rayos disponibles
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
