"use client";

import { Card, CardContent } from "@/components/ui/card";
import { CheckCircle2, Search, Zap, Gift, MessageSquare, Code2, MapPin, Sparkles } from "lucide-react";
import { useLanguage } from "@/components/language-provider";

export function Instructions() {
    const { t } = useLanguage();
    
    const steps = [
        {
            icon: Zap,
            title: t("guide_step1_title"),
            description: t("guide_step1_desc"),
            color: "text-[#FCFF52]",
            bg: "bg-[#FCFF52]/10",
            border: "border-[#FCFF52]/20"
        },
        {
            icon: Search,
            title: t("guide_step2_title"),
            description: t("guide_step2_desc"),
            color: "text-green-400",
            bg: "bg-green-500/10",
            border: "border-green-500/20"
        },
        {
            icon: Gift,
            title: t("guide_step3_title"),
            description: t("guide_step3_desc"),
            color: "text-purple-400",
            bg: "bg-purple-500/10",
            border: "border-purple-500/20"
        },
    ];

    const useCases = [
        {
            icon: MessageSquare,
            title: t("guide_usecase1_title"),
            desc: t("guide_usecase1_desc")
        },
        {
            icon: Code2,
            title: t("guide_usecase2_title"),
            desc: t("guide_usecase2_desc")
        },
        {
            icon: MapPin,
            title: t("guide_usecase3_title"),
            desc: t("guide_usecase3_desc")
        }
    ];

    return (
        <div className="space-y-8 animate-in fade-in duration-700">
            {/* Main Steps Card */}
            <div className="relative overflow-hidden rounded-3xl p-[1px] bg-gradient-to-br from-white/10 via-white/5 to-transparent">
                <div className="relative bg-black/40 backdrop-blur-xl rounded-[23px] p-6 sm:p-8">
                    {/* Background Glow */}
                    <div className="absolute top-0 right-0 w-64 h-64 bg-[#FCFF52]/5 rounded-full blur-3xl -z-10" />
                    <div className="absolute bottom-0 left-0 w-64 h-64 bg-purple-500/5 rounded-full blur-3xl -z-10" />

                    <div className="flex items-center justify-center gap-2 mb-8">
                        <div className="relative">
                            <div className="absolute inset-0 bg-[#FCFF52]/20 rounded-full animate-pulse" />
                            <Sparkles className="w-6 h-6 text-[#FCFF52] animate-pulse relative" />
                        </div>
                        <h2 className="text-2xl sm:text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-white via-[#FCFF52] to-white tracking-tight text-center">
                            {t("guide_title")}
                        </h2>
                    </div>

                    <div className="grid grid-cols-1 gap-4">
                        {steps.map((step, index) => (
                            <div
                                key={index}
                                className={`group relative flex items-start gap-4 p-5 rounded-2xl border ${step.border} ${step.bg} hover:bg-black/60 hover:scale-[1.02] transition-all duration-300 backdrop-blur-sm`}
                            >
                                {/* Number Badge */}
                                <div className="absolute -top-2 -left-2 w-8 h-8 rounded-full bg-black/80 border-2 border-white/20 flex items-center justify-center text-xs font-black text-white">
                                    {index + 1}
                                </div>
                                
                                <div className={`mt-1 p-3 rounded-xl bg-black/60 backdrop-blur-sm border border-white/10 shadow-lg shrink-0 ${step.color} group-hover:scale-110 transition-transform duration-300`}>
                                    <step.icon className="w-6 h-6" />
                                </div>
                                <div className="space-y-2 flex-1 pt-1">
                                    <h3 className={`font-bold text-lg ${step.color}`}>{step.title}</h3>
                                    <p className="text-sm text-gray-300 leading-relaxed font-medium">
                                        {step.description}
                                    </p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Use Cases Section */}
            <div className="relative">
                <div className="flex items-center justify-center gap-3 mb-6">
                    <div className="h-px flex-1 bg-gradient-to-r from-transparent via-white/20 to-white/20" />
                    <span className="text-xs font-bold uppercase tracking-widest text-white/60 px-3 py-1 bg-black/40 rounded-full border border-white/10">
                        {t("guide_usecases_title")}
                    </span>
                    <div className="h-px flex-1 bg-gradient-to-l from-transparent via-white/20 to-white/20" />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    {useCases.map((useCase, i) => (
                        <div 
                            key={i} 
                            className="group relative p-5 rounded-2xl bg-gradient-to-br from-white/5 via-white/5 to-transparent border border-white/10 hover:border-[#FCFF52]/40 hover:bg-gradient-to-br hover:from-[#FCFF52]/10 hover:via-white/10 hover:to-transparent transition-all duration-300 hover:scale-[1.02] hover:shadow-lg hover:shadow-[#FCFF52]/20"
                        >
                            {/* Background Glow on Hover */}
                            <div className="absolute inset-0 bg-[#FCFF52]/5 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300 blur-xl" />
                            
                            <div className="relative z-10">
                                <div className="mb-4 p-3 w-fit rounded-xl bg-black/40 border border-white/10 text-gray-300 group-hover:text-[#FCFF52] group-hover:border-[#FCFF52]/30 group-hover:scale-110 transition-all duration-300">
                                    <useCase.icon className="w-5 h-5" />
                                </div>
                                <h4 className="font-bold text-base text-gray-200 mb-2 group-hover:text-white transition-colors">
                                    {useCase.title}
                                </h4>
                                <p className="text-xs text-gray-400 leading-relaxed group-hover:text-gray-300 transition-colors">
                                    {useCase.desc}
                                </p>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
