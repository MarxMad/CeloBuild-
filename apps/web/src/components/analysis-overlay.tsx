"use client";

import { CheckCircle2, Loader2, Search, ShieldCheck } from "lucide-react";
import { useEffect, useState, useRef } from "react";

const STEPS = [
  {
    id: 1,
    label: "Escaneando Farcaster...",
    icon: Search,
    logs: ["Conectando a Hub...", "Leyendo últimos casts...", "Filtrando spam...", "Verificando firmas..."]
  },
  {
    id: 2,
    label: "Analizando Viralidad...",
    icon: Loader2,
    logs: ["Calculando engagement...", "Midiendo alcance...", "Detectando tendencias...", "Evaluando impacto..."]
  },
  {
    id: 3,
    label: "Verificando Reputación...",
    icon: ShieldCheck,
    logs: ["Consultando Power Badge...", "Verificando antigüedad...", "Analizando grafo social...", "Validando score..."]
  },
  {
    id: 4,
    label: "Calculando Recompensas...",
    icon: CheckCircle2,
    logs: ["Generando semilla aleatoria...", "Consultando oráculo de precios...", "Minteando NFT...", "Firmando transacción..."]
  },
];

export function AnalysisOverlay({ isDone, onComplete }: { isDone: boolean; onComplete: () => void }) {
  const [currentStep, setCurrentStep] = useState(0);
  const [currentLog, setCurrentLog] = useState("");
  const ticksInLastStep = useRef(0);

  // Step progression logic
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentStep((prev) => {
        // Normal progression
        if (prev < STEPS.length - 1) {
          ticksInLastStep.current = 0;
          return prev + 1;
        }

        // At last step
        if (isDone) {
          clearInterval(interval);
          setTimeout(onComplete, 800);
          return prev;
        }

        // Not done, increment wait counter
        // STAY at the last step. Do NOT loop back.
        // The user hates the loop.
        return prev;
      });
    }, 2500); // Slightly slower step progression to let logs breathe

    return () => clearInterval(interval);
  }, [isDone, onComplete]);

  // Micro-logs logic
  useEffect(() => {
    const stepLogs = STEPS[currentStep].logs;
    let logIndex = 0;

    // Set initial log immediately
    setCurrentLog(stepLogs[0]);

    const logInterval = setInterval(() => {
      logIndex = (logIndex + 1) % stepLogs.length;
      setCurrentLog(stepLogs[logIndex]);
    }, 400); // Change log every 400ms

    return () => clearInterval(logInterval);
  }, [currentStep]);

  return (
    <div className="absolute inset-0 bg-background/95 backdrop-blur-md z-50 flex flex-col items-center justify-center rounded-3xl p-6">
      <div className="w-full max-w-[300px] space-y-6">
        {STEPS.map((step, index) => {
          const isActive = index === currentStep;
          const isCompleted = index < currentStep;
          const Icon = step.icon;

          // If we are on the last step and waiting, force the spinner
          const isLastStepWaiting = isActive && index === STEPS.length - 1 && !isDone;

          return (
            <div
              key={step.id}
              className={`flex flex-col gap-1 transition-all duration-500 ${isActive || isCompleted ? "opacity-100 translate-x-0" : "opacity-30 translate-x-4"
                }`}
            >
              <div className="flex items-center gap-4">
                <div className={`
                  w-10 h-10 rounded-full flex items-center justify-center border-2 transition-all duration-500 relative
                  ${isActive ? "border-[#FCFF52] bg-[#FCFF52]/10 scale-100 shadow-[0_0_15px_rgba(252,255,82,0.3)]" :
                    isCompleted ? "border-green-500 bg-green-500/10 text-green-500" : "border-white/10 text-muted-foreground"}
                `}>
                  {isActive && (
                    <div className="absolute inset-0 rounded-full border border-[#FCFF52] animate-ping opacity-20" />
                  )}
                  <Icon className={`w-5 h-5 ${(isActive && step.id === 2) || isLastStepWaiting ? "animate-spin" : ""}`} />
                </div>
                <div className="flex flex-col">
                  <span className={`font-medium text-sm ${isActive ? "text-[#FCFF52]" : isCompleted ? "text-green-500" : "text-muted-foreground"}`}>
                    {step.label}
                  </span>
                  {isActive && (
                    <span className="text-[10px] font-mono text-gray-400 animate-pulse h-4 block">
                      {">"} {currentLog}
                    </span>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
