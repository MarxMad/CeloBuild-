import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CheckCircle2, Search, Zap, Gift, MessageSquare, Code2, MapPin } from "lucide-react";

export function Instructions() {
    const steps = [
        {
            icon: Zap,
            title: "1. Sistema de Energía",
            description: "Tienes 3 rayos de energía máxima. Cada análisis consume 1 rayo. Se recarga 1 rayo cada 20 minutos, ¡o comparte tu victoria para recargar al instante!",
        },
        {
            icon: Search,
            title: "2. Análisis de Último Cast",
            description: "Analizamos tu publicación más reciente en Farcaster. Si es original y no ha sido premiada antes, eres elegible.",
        },
        {
            icon: Gift,
            title: "3. Recompensa Única",
            description: "Recibes un NFT con arte generado por AI basado en lo que escribiste, o XP para subir en el ranking global.",
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
        <div className="space-y-12">
            <Card className="border-none shadow-none bg-transparent">
                <CardHeader>
                    <CardTitle className="text-2xl font-bold text-center mb-2">¿Cómo funciona?</CardTitle>
                    <p className="text-center text-muted-foreground">
                        Un pipeline autónomo que premia la calidad de la conversación.
                    </p>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-1 gap-6">
                        {steps.map((step, index) => (
                            <div key={index} className="flex flex-row items-center text-left space-x-4 p-4 rounded-2xl bg-gradient-to-br from-primary/5 to-secondary/5 border border-primary/10 hover:border-primary/30 transition-all shadow-sm">
                                <div className="p-3 rounded-xl bg-primary/20 text-primary-foreground ring-1 ring-primary/50 shrink-0">
                                    <step.icon className="w-5 h-5" />
                                </div>
                                <div>
                                    <h3 className="font-bold text-base leading-tight mb-1">{step.title}</h3>
                                    <p className="text-xs text-muted-foreground leading-snug">{step.description}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                </CardContent>
            </Card>

            <Card className="border-none shadow-none bg-transparent">
                <CardHeader>
                    <CardTitle className="text-xl font-bold text-center mb-6">Casos de Uso Reales</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-1 gap-4">
                        {useCases.map((useCase, i) => (
                            <div key={i} className="flex items-start gap-4 p-4 rounded-2xl border bg-card shadow-sm hover:shadow-md transition-shadow">
                                <div className="mt-1 p-2 bg-secondary/10 rounded-lg shrink-0">
                                    <useCase.icon className="w-5 h-5 text-secondary-foreground" />
                                </div>
                                <div>
                                    <h4 className="font-bold text-sm mb-1">{useCase.title}</h4>
                                    <p className="text-xs text-muted-foreground leading-relaxed">{useCase.desc}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
