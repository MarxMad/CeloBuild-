import { Metadata, ResolvingMetadata } from "next";

type Props = {
    searchParams: { [key: string]: string | string[] | undefined };
};

export async function generateMetadata(
    { searchParams }: Props,
    parent: ResolvingMetadata
): Promise<Metadata> {
    const user = searchParams.user as string || "Explorer";
    const xp = searchParams.xp as string || "0";
    const score = searchParams.score as string || "0";
    const reward = searchParams.reward as string || "XP";
    const locale = searchParams.locale as string || "en";

    const appUrl = process.env.NEXT_PUBLIC_APP_URL || "https://celo-build-web-8rej.vercel.app";

    // Construct dynamic OG Image URL
    // Added v=3 to bust cache for new professional design
    const ogImageUrl = `${appUrl}/api/og?type=victory&username=${encodeURIComponent(user)}&user=${encodeURIComponent(user)}&score=${score}&reward=${encodeURIComponent(reward)}&locale=${locale}&v=3`;

    const victoryUrl = `${appUrl}/share/victory?user=${encodeURIComponent(user)}&xp=${xp}&score=${score}&reward=${encodeURIComponent(reward)}&locale=${locale}`;
    
    return {
        title: `Victory: ${user} won ${reward}!`,
        description: `Join ${user} and earn rewards on Premio.xyz`,
        openGraph: {
            title: `Victory: ${user} won ${reward}!`,
            description: `Join ${user} and earn rewards on Premio.xyz`,
            images: [ogImageUrl],
            url: victoryUrl,
            type: "website",
            siteName: "Premio.xyz",
        },
        twitter: {
            card: "summary_large_image",
            title: `Victory: ${user} won ${reward}!`,
            description: `Join ${user} and earn rewards on Premio.xyz`,
            images: [ogImageUrl],
        },
        other: {
            "fc:frame": "vNext",
            "fc:frame:image": ogImageUrl,
            "fc:frame:button:1": locale === "es" ? "🚀 Jugar Ahora" : "🚀 Play Now",
            "fc:frame:button:1:action": "link",
            "fc:frame:button:1:target": appUrl,
            // Optional: Add a second button to view leaderboard
            "fc:frame:button:2": locale === "es" ? "🏆 Ver Ranking" : "🏆 Leaderboard",
            "fc:frame:button:2:action": "link",
            "fc:frame:button:2:target": `${appUrl}/?view=leaderboard`,
        },
    };
}

export default function VictoryPage({ searchParams }: Props) {
    const user = searchParams.user as string || "Explorer";
    const xp = searchParams.xp as string || "0";
    const score = searchParams.score as string || "0";
    const reward = searchParams.reward as string || "XP";
    const locale = searchParams.locale as string || "en";
    const appUrl = process.env.NEXT_PUBLIC_APP_URL || "https://celo-build-web-8rej.vercel.app";

    return (
            <div className="flex flex-col items-center justify-center min-h-screen bg-gradient-to-br from-slate-950 via-purple-950 to-slate-950 text-white p-4">
                <div className="max-w-2xl w-full">
                    <div className="text-center mb-8">
                        <div className="text-6xl mb-4">🏆</div>
                        <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-[#FCFF52] to-[#855DCD] bg-clip-text text-transparent">
                            ¡VICTORIA!
                        </h1>
                        <p className="text-gray-400">Premio.xyz - Celo Build</p>
                    </div>
                    <div className="p-8 border-2 border-[#FCFF52]/30 rounded-2xl bg-gradient-to-br from-purple-900/20 to-slate-900/20 backdrop-blur-sm shadow-2xl">
                        <div className="space-y-4">
                            <div>
                                <p className="text-gray-400 text-sm uppercase tracking-wide mb-1">Ganador</p>
                                <p className="text-2xl font-bold text-[#FCFF52]">@{user}</p>
                            </div>
                            <div className="grid grid-cols-2 gap-4 pt-4 border-t border-white/10">
                                <div>
                                    <p className="text-gray-400 text-sm uppercase tracking-wide mb-1">Puntaje</p>
                                    <p className="text-xl font-bold text-white">{score}</p>
                                </div>
                                <div>
                                    <p className="text-gray-400 text-sm uppercase tracking-wide mb-1">Premio</p>
                                    <p className="text-xl font-bold text-green-400">{reward}</p>
                                </div>
                            </div>
                            {xp !== "0" && (
                                <div className="pt-4 border-t border-white/10">
                                    <p className="text-gray-400 text-sm uppercase tracking-wide mb-1">XP Ganado</p>
                                    <p className="text-2xl font-bold text-[#855DCD]">{xp} XP</p>
                                </div>
                            )}
                        </div>
                    </div>
                    <div className="text-center mt-8">
                        <a 
                            href={process.env.NEXT_PUBLIC_APP_URL || "https://celo-build-web-8rej.vercel.app"}
                            className="inline-block px-6 py-3 bg-[#855DCD] hover:bg-[#7C55C3] text-white font-bold rounded-xl transition-colors"
                        >
                            🚀 Jugar Ahora
                        </a>
                    </div>
                </div>
            </div>
    );
}
