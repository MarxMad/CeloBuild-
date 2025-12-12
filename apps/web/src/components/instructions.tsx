import { Card, CardContent } from "@/components/ui/card";
import { CheckCircle2, Search, Zap, Gift, MessageSquare, Code2, MapPin, Sparkles } from "lucide-react";

export function Instructions() {
    const steps = [
        {
            icon: Zap,
            title: "1. Sistema de Energía",
            description: "Tienes 3 rayos de energía. Cada análisis consume 1 rayo y se recarga cada 20 min. ¡Comparte tu victoria para recargar al instante!",
            color: "text-[#FCFF52]",
            bg: "bg-[#FCFF52]/10",
            border: "border-[#FCFF52]/20"
        },
        {
            icon: Search,
            title: "2. Análisis de Casts",
            description: "Analizamos tu último cast y tu historial reciente. Cuanto más activo seas en tendencias, ¡más chances de premios!",
            color: "text-green-400",
            bg: "bg-green-500/10",
            border: "border-green-500/20"
        },
        {
            icon: Gift,
            title: "3. Gana NFTs y XP",
            description: "Recibe un Loot Box NFT generado por IA y XP. ¡Entre más casts hagas sobre temas calientes, más recompensas ganarás!",
            color: "text-purple-400",
            bg: "bg-purple-500/10",
            border: "border-purple-500/20"
        },
    ];

    const useCases = [
        {
            icon: MessageSquare,
            title: "Campañas de Memes",
            desc: "Premia automáticamente a los usuarios que crean memes virales sobre tu proyecto."
        },
        {
            icon: Code2,
            title: "Builder Grants",
            desc: "Envía micro-funding a desarrolladores que postean PRs o demos en canales técnicos."
        },
        {
            icon: MapPin,
            title: "Eventos POAP",
            desc: "Distribuye NFTs conmemorativos a asistentes que comentan durante una conferencia."
        }
    ];

    return (
        <div className="space-y-8 animate-in fade-in duration-700">
            {/* Main Steps Card */}
            <div className="relative overflow-hidden rounded-3xl p-[1px] bg-gradient-to-br from-white/10 via-white/5 to-transparent">
                <div className="relative bg-black/40 backdrop-blur-xl rounded-[23px] p-6 sm:p-8">
                    {/* Background Glow */}
                    <div className="absolute top-0 right-0 w-64 h-64 bg-[#FCFF52]/5 rounded-full blur-3xl -z-10" />

                    <div className="flex items-center justify-center gap-2 mb-8">
                        <Sparkles className="w-5 h-5 text-[#FCFF52] animate-pulse" />
                        <h2 className="text-2xl font-black text-transparent bg-clip-text bg-gradient-to-r from-white to-white/70 tracking-tight text-center">
                            ¿Cómo Funciona?
                        </h2>
                    </div>

                    <div className="grid grid-cols-1 gap-4">
                        {steps.map((step, index) => (
                            <div
                                key={index}
                                className={`group relative flex items-start gap-4 p-4 rounded-2xl border ${step.border} ${step.bg} hover:bg-black/40 transition-all duration-300`}
                            >
                                <div className={`mt-1 p-2.5 rounded-xl bg-black/40 backdrop-blur-sm border border-white/5 shadow-inner shrink-0 ${step.color}`}>
                                    <step.icon className="w-5 h-5" />
                                </div>
                                <div className="space-y-1">
                                    <h3 className={`font-bold text-base ${step.color}`}>{step.title}</h3>
                                    <p className="text-sm text-gray-400 leading-relaxed font-medium">
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
                <div className="flex items-center justify-center gap-2 mb-6 opacity-70">
                    <div className="h-px w-10 bg-gradient-to-r from-transparent to-white/20" />
                    <span className="text-xs font-bold uppercase tracking-widest text-white/40">Casos de Uso</span>
                    <div className="h-px w-10 bg-gradient-to-l from-transparent to-white/20" />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    {useCases.map((useCase, i) => (
                        <div key={i} className="group p-4 rounded-2xl bg-white/5 border border-white/5 hover:border-[#FCFF52]/30 hover:bg-white/10 transition-all duration-300">
                            <div className="mb-3 p-2 w-fit rounded-lg bg-white/5 text-gray-300 group-hover:text-[#FCFF52] group-hover:scale-110 transition-all duration-300">
                                <useCase.icon className="w-4 h-4" />
                            </div>
                            <h4 className="font-bold text-sm text-gray-200 mb-1">{useCase.title}</h4>
                            <p className="text-[11px] text-gray-500 leading-relaxed group-hover:text-gray-400 transition-colors">
                                {useCase.desc}
                            </p>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
