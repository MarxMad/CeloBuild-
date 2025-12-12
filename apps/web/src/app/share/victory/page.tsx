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
    // Added v=2 to bust cache for new CSS
    const ogImageUrl = `${appUrl}/api/og?type=victory&user=${encodeURIComponent(user)}&score=${score}&reward=${encodeURIComponent(reward)}&locale=${locale}&v=2`;

    return {
        title: `Victory: ${user} won ${reward}!`,
        description: `Join ${user} and earn rewards on Premio.`,
        openGraph: {
            title: `Victory: ${user} won ${reward}!`,
            description: `Join ${user} and earn rewards on Premio.`,
            images: [ogImageUrl],
        },
        other: {
            "fc:frame": "vNext",
            "fc:frame:image": ogImageUrl,
            "fc:frame:button:1": locale === "es" ? "🚀 Jugar Ahora" : "🚀 Play Now",
            "fc:frame:button:1:action": "link",
            "fc:frame:button:1:target": appUrl, // Fix: Launch the app directly
            // Optional: Add a second button to view leaderboard
            "fc:frame:button:2": locale === "es" ? "🏆 Ver Ranking" : "🏆 Leaderboard",
            "fc:frame:button:2:action": "link",
            "fc:frame:button:2:target": `${appUrl}/?view=leaderboard`,
        },
    };
}

export default function VictoryPage({ searchParams }: Props) {
    const user = searchParams.user as string || "Explorer";

    return (
        <div className="flex flex-col items-center justify-center min-h-screen bg-slate-950 text-white p-4">
            <h1 className="text-2xl font-bold mb-4">🏆 Victory Frame</h1>
            <p className="text-gray-400 mb-8">This page is optimized for Farcaster Frames.</p>
            <div className="p-4 border border-white/10 rounded-lg bg-white/5">
                <p>Winner: <span className="text-[#FCFF52] font-mono">{user}</span></p>
            </div>
        </div>
    );
}
