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

  // Inicializar y actualizar bolts cuando cambian las props
  // IMPORTANTE: refill_at del backend es la fuente de verdad (timestamp absoluto)
  // Solo calcular refill_at si no está presente, NUNCA recalcular si ya existe
  useEffect(() => {
    if (!bolts || bolts.length === 0) {
      // Si no hay información de bolts, crear estado por defecto
      setBoltsState(
        Array.from({ length: maxEnergy }).map((_, i) => ({
          index: i,
          available: i < currentEnergy,
          seconds_to_refill: 0,
          refill_at: null
        }))
      );
      return;
    }

    // Procesar bolts del backend
    // El backend devuelve refill_at como timestamp absoluto (Unix timestamp en segundos)
    const now = Date.now() / 1000;
    const updatedBolts = bolts.map(bolt => {
      if (!bolt.available && bolt.seconds_to_refill > 0) {
        // Si tiene seconds_to_refill pero no refill_at, calcularlo
        // Esto solo debería pasar si el backend no devolvió refill_at (fallback)
        if (!bolt.refill_at) {
          // Calcular refill_at basándose en seconds_to_refill actual
          // Esto es un fallback, idealmente el backend siempre debería devolver refill_at
          const refill_at = now + bolt.seconds_to_refill;
          console.log(`[EnergyDisplay] ⚠️ Calculando refill_at para bolt ${bolt.index}: ${refill_at} (fallback, ahora: ${now}, seconds_to_refill: ${bolt.seconds_to_refill})`);
          return { ...bolt, refill_at };
        }
        // Si ya tiene refill_at, usarlo tal cual - es la fuente de verdad del backend
        // El backend calcula refill_at como bolt_time + RECHARGE_TIME (timestamp absoluto)
        // NUNCA recalcular, porque eso reiniciaría la cuenta regresiva
        console.log(`[EnergyDisplay] ✅ Usando refill_at del backend para bolt ${bolt.index}: ${bolt.refill_at} (ahora: ${now}, tiempo restante: ${Math.floor(bolt.refill_at - now)}s)`);
        return bolt;
      }
      return bolt;
    });
    
    console.log(`[EnergyDisplay] 🔄 Actualizando boltsState con ${updatedBolts.length} bolts`);
    setBoltsState(updatedBolts);
  }, [bolts, maxEnergy, currentEnergy]);

  // Actualizar cuenta regresiva cada segundo basándose en refill_at (timestamp absoluto)
  // Esto asegura que las cuentas regresivas persistan después de refrescar la página
  // El refill_at viene del backend como timestamp absoluto (Unix timestamp en segundos)
  useEffect(() => {
    const interval = setInterval(() => {
      setBoltsState(prev => {
        const now = Date.now() / 1000; // Tiempo actual en segundos (Unix timestamp)
        return prev.map(bolt => {
          if (!bolt.available && bolt.refill_at) {
            // Calcular tiempo restante basándose en el timestamp absoluto refill_at
            // refill_at es un Unix timestamp en segundos del backend
            // Esto asegura que la cuenta regresiva sea correcta incluso después de refrescar
            // Usamos el refill_at directamente del estado, que viene del backend
            const remaining = Math.max(0, Math.floor(bolt.refill_at - now));
            if (remaining === 0) {
              // El rayo ha recargado
              console.log(`[EnergyDisplay] ⚡ Bolt ${bolt.index} recargado`);
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
  }, [timeLeft]); // No agregar boltsState como dependencia - el intervalo usa el estado más reciente con setBoltsState(prev => ...)

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
      <div className="w-full space-y-3">
        <div className="flex items-center justify-center gap-3 bg-gradient-to-r from-black/60 via-black/40 to-black/60 px-4 py-3 rounded-xl border border-white/10 backdrop-blur-sm shadow-lg">
          {Array.from({ length: maxEnergy }).map((_, i) => {
            const boltInfo = boltsState.find(b => b.index === i) || { 
              index: i,
              available: i < currentEnergy, 
              seconds_to_refill: 0, 
              refill_at: null 
            };
            const isActive = boltInfo.available;

            return (
              <div key={i} className="flex flex-col items-center gap-2 min-w-[60px]">
                <div className="relative">
                  <Zap
                    className={`w-8 h-8 transition-all duration-300 ${
                      isActive
                        ? "text-[#FCFF52] fill-[#FCFF52] drop-shadow-[0_0_12px_rgba(252,255,82,0.8)] animate-pulse"
                        : "text-gray-600 fill-gray-900/50 opacity-50"
                    }`}
                  />
                  {!isActive && (
                    <div className="absolute inset-0 flex items-center justify-center">
                      <div className="w-5 h-5 border-2 border-amber-500/50 rounded-full animate-spin" style={{ borderTopColor: 'transparent' }} />
                    </div>
                  )}
                </div>
                {!isActive && boltInfo.seconds_to_refill > 0 ? (
                  <div className="text-[10px] font-mono text-amber-400 bg-black/60 px-2 py-1 rounded-lg border border-amber-500/30 font-bold">
                    {formatTime(boltInfo.seconds_to_refill)}
                  </div>
                ) : isActive ? (
                  <div className="text-[9px] text-green-400 font-medium">
                    Listo
                  </div>
                ) : null}
              </div>
            );
          })}
        </div>

        {/* Resumen de estado */}
        <div className="text-center space-y-1">
          {currentEnergy === maxEnergy ? (
            <p className="text-sm text-green-400 font-bold">
              ✅ Todos los rayos disponibles
            </p>
          ) : currentEnergy === 0 ? (
            <div className="space-y-1">
              <p className="text-sm text-amber-400 font-bold">
              ⚠️ Sin rayos disponibles
            </p>
              {boltsState.some(b => !b.available && b.seconds_to_refill > 0) && (
                <p className="text-xs text-amber-400/70">
                  Próximo rayo en: {formatTime(boltsState.find(b => !b.available && b.seconds_to_refill > 0)?.seconds_to_refill || 0)}
                </p>
              )}
            </div>
          ) : (
            <div className="space-y-1">
              <p className="text-sm text-[#FCFF52] font-bold">
              {currentEnergy} de {maxEnergy} rayos disponibles
            </p>
              {boltsState.some(b => !b.available && b.seconds_to_refill > 0) && (
                <p className="text-xs text-amber-400/70">
                  Próximo rayo en: {formatTime(boltsState.find(b => !b.available && b.seconds_to_refill > 0)?.seconds_to_refill || 0)}
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
