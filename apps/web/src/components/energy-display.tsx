"use client";

import { useState, useEffect } from "react";
import { Zap } from "lucide-react";

interface EnergyDisplayProps {
    currentEnergy: number;
    maxEnergy: number;
    secondsToRefill: number;
}

export function EnergyDisplay({ currentEnergy, maxEnergy, secondsToRefill }: EnergyDisplayProps) {
    const [timeLeft, setTimeLeft] = useState(secondsToRefill);

    useEffect(() => {
        setTimeLeft(secondsToRefill);
    }, [secondsToRefill]);

    useEffect(() => {
        if (timeLeft <= 0) return;

        const interval = setInterval(() => {
            setTimeLeft((prev) => Math.max(0, prev - 1));
        }, 1000);

        return () => clearInterval(interval);
    }, [timeLeft]);

    const formatTime = (seconds: number) => {
        if (seconds <= 0) return "";
        const m = Math.floor(seconds / 60);
        const s = seconds % 60;
        return `${m}:${s.toString().padStart(2, '0')}`;
    };

    return (
        <div className="flex flex-col items-center gap-1">
            <div className="flex items-center gap-1 bg-black/40 px-3 py-1.5 rounded-full border border-white/10 backdrop-blur-sm shadow-inner">
                {Array.from({ length: maxEnergy }).map((_, i) => {
                    const isActive = i < currentEnergy;
                    // The next bolt to refill is the first non-active one
                    const isRefilling = !isActive && i === currentEnergy;

                    return (
                        <div key={i} className="relative">
                            <Zap
                                className={`w-5 h-5 transition-all duration-300 ${isActive
                                        ? "text-[#FCFF52] fill-[#FCFF52] drop-shadow-[0_0_8px_rgba(252,255,82,0.6)]"
                                        : "text-gray-600 fill-gray-900/50"
                                    }`}
                            />

                            {/* Visual indicator for the one currently refilling? Optional */}
                        </div>
                    );
                })}
            </div>

            {timeLeft > 0 && currentEnergy < maxEnergy && (
                <div className="text-[10px] font-mono font-medium text-[#FCFF52]/80 animate-pulse bg-black/20 px-2 rounded">
                    ⚡ +1 en {formatTime(timeLeft)}
                </div>
            )}
        </div>
    );
}
