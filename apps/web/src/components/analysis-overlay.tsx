"use client";

import { CheckCircle2, Loader2, Search, ShieldCheck } from "lucide-react";
import { useEffect, useState, useRef } from "react";

const STEPS = [
  { id: 1, label: "Escaneando Farcaster...", icon: Search },
  { id: 2, label: "Analizando Viralidad...", icon: Loader2 },
  { id: 3, label: "Verificando Reputación...", icon: ShieldCheck },
  { id: 4, label: "Calculando Recompensas...", icon: CheckCircle2 },
];

export function AnalysisOverlay({ isDone, onComplete }: { isDone: boolean; onComplete: () => void }) {
  const [currentStep, setCurrentStep] = useState(0);

  const ticksInLastStep = useRef(0);

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
        // Interval is 2000ms. We want to wait 4s (2 ticks) before looping.
        ticksInLastStep.current += 1;

        if (ticksInLastStep.current >= 2) {
          ticksInLastStep.current = 0;
          return 0; // Loop back to start
        }

        return prev;
      });
    }, 2000);

    return () => clearInterval(interval);
  }, [isDone, onComplete]);

  return (
    <div className="absolute inset-0 bg-background/95 backdrop-blur-md z-50 flex flex-col items-center justify-center rounded-3xl p-6">
      <div className="w-full max-w-[280px] space-y-6">
        {STEPS.map((step, index) => {
          const isActive = index === currentStep;
          const isCompleted = index < currentStep;
          const Icon = step.icon;

          // If we are on the last step and waiting, force the spinner
          const isLastStepWaiting = isActive && index === STEPS.length - 1 && !isDone;

          return (
            <div
              key={step.id}
              className={`flex items-center gap-4 transition-all duration-500 ${isActive || isCompleted ? "opacity-100 translate-x-0" : "opacity-30 translate-x-4"
                }`}
            >
              <div className={`
                w-10 h-10 rounded-full flex items-center justify-center border-2 transition-all duration-500
                ${isActive ? "border-[#FCFF52] bg-[#FCFF52]/10 scale-100 shadow-[0_0_10px_rgba(252,255,82,0.2)]" :
                  isCompleted ? "border-green-500 bg-green-500/10 text-green-500" : "border-white/10 text-muted-foreground"}
              `}>
                <Icon className={`w-5 h-5 ${(isActive && step.id === 2) || isLastStepWaiting ? "animate-spin" : ""}`} />
              </div>
              <span className={`font-medium text-sm ${isActive ? "text-[#FCFF52]" : isCompleted ? "text-green-500" : "text-muted-foreground"}`}>
                {step.label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
