"use client";

import { useEffect, useState } from "react";
import { useAccount, useBalance } from "wagmi";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Crown, Wallet, Coins, Trophy, Sparkles } from "lucide-react";
import { useFarcasterUser } from "./farcaster-provider";
import { motion } from "framer-motion";

const cUSD_ADDRESS = "0x765de816845861e75a25fca122bb6898b8b1282a";

interface NFTCard {
    id: string;
    name: string;
    description: string;
    image: string;
    rarity: "Common" | "Rare" | "Epic" | "Legendary";
    type: string;
}

export function Dashboard() {
    const { address, isConnected } = useAccount();
    const farcasterUser = useFarcasterUser();
    const [xp, setXp] = useState(0);
    const [nfts, setNfts] = useState<NFTCard[]>([]);

    // Fetch XP
    useEffect(() => {
        if (address) {
            const fetchXp = async () => {
                try {
                    const res = await fetch(`/api/lootbox/xp/${address}`);
                    if (res.ok) {
                        const data = await res.json();
                        setXp(data.xp || 0);
                    }
                } catch (e) {
                    console.error("Error fetching XP:", e);
                }
            };
            fetchXp();
            const interval = setInterval(fetchXp, 10000);
            return () => clearInterval(interval);
        }
    }, [address]);

    // Fetch Balances
    const { data: celoBalance } = useBalance({
        address,
        query: { enabled: !!address }
    });

    const { data: cUSDBalance } = useBalance({
        address,
        token: cUSD_ADDRESS,
        query: { enabled: !!address }
    });

    // Mock NFTs for now (replace with real fetch later)
    useEffect(() => {
        if (address) {
            // Simulating fetched NFTs
            setNfts([
                {
                    id: "1",
                    name: "Genesis Loot",
                    description: "The first ever loot box opened.",
                    image: "https://placehold.co/400x600/1a1a1a/FFF?text=Genesis+Card",
                    rarity: "Legendary",
                    type: "Artifact"
                }
            ]);
        }
    }, [address]);

    if (!isConnected) return null;

    return (
        <div className="w-full max-w-4xl mx-auto space-y-6 p-4">
            {/* Header Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* XP Card */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                >
                    <Card className="bg-black/40 border-yellow-500/20 backdrop-blur-xl overflow-hidden relative group">
                        <div className="absolute inset-0 bg-gradient-to-br from-yellow-500/10 to-transparent opacity-50 group-hover:opacity-100 transition-opacity" />
                        <CardContent className="p-6 relative z-10 flex items-center justify-between">
                            <div>
                                <p className="text-sm font-medium text-yellow-500/80 uppercase tracking-wider">Experience</p>
                                <h3 className="text-3xl font-bold text-white mt-1">{xp} <span className="text-sm text-muted-foreground">XP</span></h3>
                            </div>
                            <div className="p-3 bg-yellow-500/20 rounded-full">
                                <Crown className="w-6 h-6 text-yellow-500" />
                            </div>
                        </CardContent>
                    </Card>
                </motion.div>

                {/* cUSD Card */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                >
                    <Card className="bg-black/40 border-green-500/20 backdrop-blur-xl overflow-hidden relative group">
                        <div className="absolute inset-0 bg-gradient-to-br from-green-500/10 to-transparent opacity-50 group-hover:opacity-100 transition-opacity" />
                        <CardContent className="p-6 relative z-10 flex items-center justify-between">
                            <div>
                                <p className="text-sm font-medium text-green-500/80 uppercase tracking-wider">Balance</p>
                                <h3 className="text-3xl font-bold text-white mt-1">
                                    {parseFloat(cUSDBalance?.formatted || '0').toFixed(2)}
                                    <span className="text-sm text-muted-foreground ml-1">cUSD</span>
                                </h3>
                            </div>
                            <div className="p-3 bg-green-500/20 rounded-full">
                                <Coins className="w-6 h-6 text-green-500" />
                            </div>
                        </CardContent>
                    </Card>
                </motion.div>

                {/* CELO Card */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 }}
                >
                    <Card className="bg-black/40 border-blue-500/20 backdrop-blur-xl overflow-hidden relative group">
                        <div className="absolute inset-0 bg-gradient-to-br from-blue-500/10 to-transparent opacity-50 group-hover:opacity-100 transition-opacity" />
                        <CardContent className="p-6 relative z-10 flex items-center justify-between">
                            <div>
                                <p className="text-sm font-medium text-blue-500/80 uppercase tracking-wider">Gas Token</p>
                                <h3 className="text-3xl font-bold text-white mt-1">
                                    {parseFloat(celoBalance?.formatted || '0').toFixed(2)}
                                    <span className="text-sm text-muted-foreground ml-1">CELO</span>
                                </h3>
                            </div>
                            <div className="p-3 bg-blue-500/20 rounded-full">
                                <Wallet className="w-6 h-6 text-blue-500" />
                            </div>
                        </CardContent>
                    </Card>
                </motion.div>
            </div>

            {/* NFT Gallery */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 }}
            >
                <div className="flex items-center gap-2 mb-4">
                    <Trophy className="w-5 h-5 text-purple-500" />
                    <h2 className="text-xl font-bold text-white">My Collection</h2>
                </div>

                {nfts.length === 0 ? (
                    <Card className="bg-black/20 border-white/5 border-dashed">
                        <CardContent className="p-12 flex flex-col items-center justify-center text-center">
                            <Sparkles className="w-12 h-12 text-muted-foreground mb-4 opacity-50" />
                            <h3 className="text-lg font-medium text-white">No Artifacts Yet</h3>
                            <p className="text-sm text-muted-foreground mt-1">Participate in campaigns to earn legendary cards.</p>
                        </CardContent>
                    </Card>
                ) : (
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                        {nfts.map((nft) => (
                            <div key={nft.id} className="relative group perspective-1000">
                                <div className="relative transform transition-transform duration-500 group-hover:scale-105 group-hover:rotate-y-12 preserve-3d">
                                    {/* Card Frame */}
                                    <div className={`
                                        rounded-xl overflow-hidden border-4 bg-[#1a1a1a] shadow-2xl
                                        ${nft.rarity === 'Legendary' ? 'border-yellow-500 shadow-yellow-500/20' :
                                            nft.rarity === 'Epic' ? 'border-purple-500 shadow-purple-500/20' :
                                                nft.rarity === 'Rare' ? 'border-blue-500 shadow-blue-500/20' :
                                                    'border-gray-500 shadow-gray-500/20'}
                                    `}>
                                        {/* Image Area */}
                                        <div className="aspect-[59/86] relative">
                                            <img src={nft.image} alt={nft.name} className="w-full h-full object-cover" />

                                            {/* Overlay Info */}
                                            <div className="absolute bottom-0 inset-x-0 bg-black/80 backdrop-blur-sm p-4 border-t border-white/10">
                                                <div className="flex justify-between items-start mb-2">
                                                    <h4 className={`font-bold text-lg ${nft.rarity === 'Legendary' ? 'text-yellow-400' : 'text-white'
                                                        }`}>{nft.name}</h4>
                                                    <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-white/10 text-white/80">
                                                        {nft.rarity}
                                                    </span>
                                                </div>
                                                <p className="text-xs text-gray-300 line-clamp-3">{nft.description}</p>
                                                <div className="mt-2 pt-2 border-t border-white/10 flex justify-between items-center">
                                                    <span className="text-[10px] text-gray-500">{nft.type}</span>
                                                    <span className="text-[10px] text-gray-500">Gemini AI Art</span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </motion.div>
        </div>
    );
}
