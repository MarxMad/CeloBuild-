"use client";

import { CheckCircle2, Loader2, Search, ShieldCheck, Zap, Database, Coins } from "lucide-react";
import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

const STEPS = [
  {
    id: 1,
    label: "Conectando a Farcaster",
    icon: Search,
    color: "text-blue-400",
    logs: ["Iniciando handshake...", "Autenticando API...", "Verificando nodo...", "Sincronizando estado..."]
  },
  {
    id: 2,
    label: "Recuperando Historial",
    icon: Database,
    color: "text-purple-400",
    logs: ["Leyendo últimos casts...", "Filtrando spam...", "Indexando interacciones...", "Recuperando grafo social..."]
  },
  {
    id: 3,
    label: "Analizando Viralidad",
    icon: Zap,
    color: "text-yellow-400",
    logs: ["Calculando engagement...", "Midiendo alcance...", "Detectando patrones...", "Evaluando impacto..."]
  },
  {
    id: 4,
    label: "Verificando Reputación",
    icon: ShieldCheck,
    color: "text-green-400",
    logs: ["Consultando Power Badge...", "Verificando antigüedad...", "Analizando comportamiento...", "Validando score..."]
  },
  {
    id: 5,
    label: "Calculando Recompensas",
    icon: Coins,
    color: "text-orange-400",
    logs: ["Generando semilla aleatoria...", "Consultando oráculo...", "Determinando rareza...", "Asignando valor..."]
  },
  {
    id: 6,
    label: "Finalizando Transacción",
    icon: Loader2,
    color: "text-[#FCFF52]",
    logs: ["Preparando payload...", "Firmando transacción...", "Minteando activos...", "Confirmando en bloque..."]
  },
];

export function AnalysisOverlay({ isDone, onComplete }: { isDone: boolean; onComplete: () => void }) {
  const [currentStep, setCurrentStep] = useState(0);
  const [currentLog, setCurrentLog] = useState("");

  // Step progression logic
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentStep((prev) => {
        // Normal progression
        if (prev < STEPS.length - 1) {
          return prev + 1;
        }

        // At last step
        if (isDone) {
          clearInterval(interval);
          setTimeout(onComplete, 1000);
          return prev;
        }

        // Stay at last step if not done
        return prev;
      });
    }, 3000); // 3 seconds per step (faster UX)

    return () => clearInterval(interval);
  }, [isDone, onComplete]);

  // Micro-logs logic
  useEffect(() => {
    const stepLogs = STEPS[currentStep].logs;
    let logIndex = 0;
    setCurrentLog(stepLogs[0]);

    const logInterval = setInterval(() => {
      logIndex = (logIndex + 1) % stepLogs.length;
      setCurrentLog(stepLogs[logIndex]);
    }, 400);

    return () => clearInterval(logInterval);
  }, [currentStep]);

  const activeStep = STEPS[currentStep];
  const Icon = activeStep.icon;

  return (
    <div className="fixed inset-0 bg-background/95 backdrop-blur-xl z-[100] flex flex-col items-center justify-center p-6">
      <div className="w-full max-w-sm relative">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeStep.id}
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -20, scale: 1.05 }}
            transition={{ duration: 0.4 }}
            className="flex flex-col items-center text-center space-y-8"
          >
            {/* Large Icon Card */}
            <div className="relative">
              <div className={`w-32 h-32 rounded-3xl bg-white/5 border border-white/10 flex items-center justify-center shadow-2xl backdrop-blur-sm ${activeStep.color}`}>
                <Icon className="w-16 h-16 animate-pulse" />
              </div>
              {/* Decorative rings */}
              <div className={`absolute inset-0 rounded-3xl border border-current opacity-20 animate-ping ${activeStep.color}`} />
            </div>

            {/* Text Content */}
            <div className="space-y-2">
              <h2 className="text-2xl font-bold tracking-tight text-white">
                {activeStep.label}
              </h2>
              <div className="h-6">
                <p className="text-xs font-mono text-muted-foreground animate-pulse">
                  {">"} {currentLog}
                </p>
              </div>
            </div>
          </motion.div>
        </AnimatePresence>

        {/* Progress Bar */}
        <div className="mt-12 w-full bg-white/5 h-1.5 rounded-full overflow-hidden">
          <motion.div
            className="h-full bg-[#FCFF52]"
            initial={{ width: "0%" }}
            animate={{ width: `${((currentStep + 1) / STEPS.length) * 100}%` }}
            transition={{ duration: 0.5 }}
          />
        </div>

        {/* Step Dots */}
        <div className="flex justify-center gap-2 mt-4">
          {STEPS.map((step, idx) => (
            <div
              key={step.id}
              className={`w-1.5 h-1.5 rounded-full transition-colors duration-300 ${idx <= currentStep ? "bg-[#FCFF52]" : "bg-white/10"
                }`}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
