"use client";

import { CheckCircle2, Loader2, Search, ShieldCheck, Zap, Database, Coins } from "lucide-react";
import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useLanguage } from "@/components/language-provider";

export function AnalysisOverlay({ isDone, onComplete }: { isDone: boolean; onComplete: () => void }) {
  const { t } = useLanguage();
  const [currentStep, setCurrentStep] = useState(0);
  const [currentLog, setCurrentLog] = useState("");

  const STEPS = [
    {
      id: 1,
      label: t("overlay_step1"),
      icon: Search,
      color: "text-blue-400",
      logs: ["Handshake API...", "Auth check...", "Syncing state..."]
    },
    {
      id: 2,
      label: t("overlay_step2"),
      icon: Database,
      color: "text-purple-400",
      logs: ["Indexing...", "Filter spam...", "Graph sync..."]
    },
    {
      id: 3,
      label: "Viral Check", // Dynamic key wasn't added for all steps in dictionary, using fallback or reuse
      icon: Zap,
      color: "text-amber-500 dark:text-yellow-400",
      logs: ["Engagement...", "Reach...", "Impact..."]
    },
    {
      id: 4,
      label: t("overlay_step3"),
      icon: ShieldCheck,
      color: "text-green-400",
      logs: ["Power Badge...", "Vintage...", "Score..."]
    },
    {
      id: 5,
      label: t("form_status_send"),
      icon: Coins,
      color: "text-orange-400",
      logs: ["Oracle...", "Rarity...", "Value..."]
    },
    {
      id: 6,
      label: t("overlay_step4"),
      icon: Loader2,
      color: "text-green-600 dark:text-[#FCFF52]",
      logs: ["Payload...", "Signing...", "Minting...", "Confirming..."]
    },
  ];

  // Step progression logic
  // Step progression logic
  useEffect(() => {
    const stepDuration = isDone ? 50 : 3000; // Hyper-speed if API is done

    const interval = setInterval(() => {
      setCurrentStep((prev) => {
        if (prev < STEPS.length - 1) {
          return prev + 1;
        }
        return prev;
      });
    }, stepDuration);

    return () => clearInterval(interval);
  }, [isDone, STEPS.length]);

  // Completion trigger
  useEffect(() => {
    if (isDone && currentStep === STEPS.length - 1) {
      const timer = setTimeout(onComplete, 1000);
      return () => clearTimeout(timer);
    }
  }, [isDone, currentStep, onComplete, STEPS.length]);

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
  }, [currentStep, STEPS]); // Depend on STEPS which changes with lang

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
              <h2 className="text-2xl font-bold tracking-tight text-foreground dark:text-white">
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
        <div className="mt-12 w-full bg-neutral-200 dark:bg-white/5 h-1.5 rounded-full overflow-hidden">
          <motion.div
            className="h-full bg-green-600 dark:bg-[#FCFF52]"
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
              className={`w-1.5 h-1.5 rounded-full transition-colors duration-300 ${idx <= currentStep ? "bg-green-600 dark:bg-[#FCFF52]" : "bg-neutral-300 dark:bg-white/10"
                }`}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
