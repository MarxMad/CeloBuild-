"use client";

import { useEffect, useState } from "react";
import { useAccount, usePublicClient } from "wagmi";
import { MINTER_ADDRESS, MINTER_ABI } from "@/lib/contracts";
import { parseAbiItem } from "viem";
import Link from "next/link";
import { ArrowLeft, Crown, Loader2, RefreshCw, Sparkles, Trophy, Zap } from "lucide-react";

type NFT = {
    tokenId: string;
    image: string;
    name: string;
    description: string;
    rarity?: string;
    type?: string;
};

// Bloque reciente de Celo Mainnet para evitar escanear desde el genesis (optimización)
const FROM_BLOCK = 28000000n;

export default function ProfilePage() {
    const { address, isConnected } = useAccount();
    const publicClient = usePublicClient();
    const [nfts, setNfts] = useState<NFT[]>([]);
    const [loading, setLoading] = useState(false);
    const [xp, setXp] = useState(0);
    const [rank, setRank] = useState<number | null>(null);

    const fetchNFTs = async () => {
        if (!address || !publicClient) return;
        setLoading(true);
        console.log("Fetching NFTs for:", address);

        try {
            // 1. Get Mint events
            // Usamos un bloque reciente para evitar timeouts
            const logs = await publicClient.getLogs({
                address: MINTER_ADDRESS,
                event: parseAbiItem('event LootMinted(bytes32 indexed campaignId, address indexed to, uint256 tokenId, bool soulbound)'),
                args: {
                    to: address,
                },
                fromBlock: FROM_BLOCK,
            });

            console.log("Logs found:", logs.length);

            // 2. Fetch tokenURI and metadata in parallel
            const nftPromises = logs.map(async (log) => {
                const tokenId = log.args.tokenId;
                if (tokenId === undefined) return null;

                try {
                    const tokenUri = await publicClient.readContract({
                        address: MINTER_ADDRESS,
                        abi: MINTER_ABI,
                        functionName: "tokenURI",
                        args: [tokenId],
                    });

                    // Handle data URIs (base64) or HTTP URLs
                    let metadata;
                    if (tokenUri.startsWith("data:application/json;base64,")) {
                        const base64 = tokenUri.split(",")[1];
                        metadata = JSON.parse(atob(base64));
                    } else {
                        // Usar gateway de IPFS si es necesario, o fetch directo
                        const url = tokenUri.replace("ipfs://", "https://ipfs.io/ipfs/");
                        const res = await fetch(url);
                        metadata = await res.json();
                    }

                    const nft: NFT = {
                        tokenId: tokenId.toString(),
                        image: metadata.image?.replace("ipfs://", "https://ipfs.io/ipfs/") || "",
                        name: metadata.name || `Artifact #${tokenId}`,
                        description: metadata.description || "No description",
                        rarity: metadata.attributes?.find((a: any) => a.trait_type === "Rarity")?.value,
                        type: metadata.attributes?.find((a: any) => a.trait_type === "Type")?.value,
                    };
                    return nft;
                } catch (err) {
                    console.error(`Error fetching metadata for token ${tokenId}`, err);
                    return null;
                }
            });

            const results = await Promise.all(nftPromises);
            const loadedNfts = results.filter((n): n is NFT => n !== null);

            console.log("NFTs loaded:", loadedNfts.length);
            setNfts(loadedNfts.reverse()); // Show newest first
        } catch (err) {
            console.error("Error fetching NFTs", err);
        } finally {
            setLoading(false);
        }
    };

    // Fetch XP and Rank
    useEffect(() => {
        if (address) {
            const fetchXp = async () => {
                try {
                    const res = await fetch(`/api/lootbox/xp/${address}`);
                    if (res.ok) {
                        const data = await res.json();
                        setXp(data.xp || 0);
                        setRank(data.rank || null);
                    }
                } catch (e) {
                    console.error("Error fetching XP:", e);
                }
            };
            fetchXp();
        }
    }, [address]);

    useEffect(() => {
        if (isConnected) {
            fetchNFTs();
        }
    }, [address, isConnected, publicClient]);

    if (!isConnected) {
        return (
            <div className="flex min-h-screen flex-col items-center justify-center p-4 text-center bg-[#0a0a0a]">
                <h1 className="text-2xl font-bold mb-4 text-white">Conecta tu wallet</h1>
                <p className="text-gray-400">Necesitas conectar tu wallet para ver tus premios.</p>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-[#0a0a0a] text-white p-4 md:p-8 relative overflow-hidden">
            {/* Background Effects */}
            <div className="fixed inset-0 bg-[url('/grid-pattern.svg')] opacity-[0.03] pointer-events-none" />
            <div className="fixed top-[-50%] left-[-50%] w-[200%] h-[200%] bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-green-500/5 via-transparent to-transparent opacity-50 pointer-events-none" />

            {/* Navbar / Header */}
            <div className="sticky top-0 z-50 mb:mb-8">
                <div className="max-w-6xl mx-auto flex items-center justify-between bg-black/40 backdrop-blur-xl rounded-2xl border border-white/10 shadow-lg p-4 mb-6">
                    <Link
                        href="/"
                        className="group flex items-center gap-2 text-gray-400 hover:text-white transition-colors"
                    >
                        <div className="p-1.5 rounded-full bg-white/5 group-hover:bg-[#FCFF52]/20 transition-colors">
                            <ArrowLeft className="w-4 h-4 group-hover:text-[#FCFF52]" />
                        </div>
                        <span className="font-bold text-sm">Volver</span>
                    </Link>
                    <div className="flex items-center gap-4">
                        <button
                            onClick={fetchNFTs}
                            disabled={loading}
                            className="p-2 text-gray-400 hover:text-[#FCFF52] transition-colors disabled:opacity-50"
                            title="Recargar colección"
                        >
                            <RefreshCw className={`w-5 h-5 ${loading ? "animate-spin" : ""}`} />
                        </button>
                        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#FCFF52]/10 border border-[#FCFF52]/30 shadow-[0_0_15px_rgba(252,255,82,0.1)]">
                            <Crown className="w-3.5 h-3.5 text-[#FCFF52]" />
                            <span className="text-xs font-black text-[#FCFF52] uppercase tracking-widest">Colección</span>
                        </div>
                    </div>
                </div>
            </div>

            <div className="max-w-6xl mx-auto relative z-10">
                {/* Stats Section */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-12">
                    <div className="bg-white/5 backdrop-blur-md rounded-2xl border border-white/10 p-5 flex flex-col items-center justify-center text-center hover:border-purple-500/50 transition-colors group">
                        <div className="mb-2 p-2 bg-purple-500/20 rounded-lg text-purple-400 group-hover:scale-110 transition-transform">
                            <Trophy className="w-5 h-5" />
                        </div>
                        <span className="text-gray-400 text-[10px] uppercase font-bold tracking-widest mb-1">Ranking</span>
                        <span className="text-3xl font-black text-transparent bg-clip-text bg-gradient-to-b from-purple-300 to-purple-600">#{rank ?? "-"}</span>
                    </div>

                    <div className="bg-white/5 backdrop-blur-md rounded-2xl border border-white/10 p-5 flex flex-col items-center justify-center text-center hover:border-[#FCFF52]/50 transition-colors group">
                        <div className="mb-2 p-2 bg-[#FCFF52]/20 rounded-lg text-[#FCFF52] group-hover:scale-110 transition-transform">
                            <Zap className="w-5 h-5" />
                        </div>
                        <span className="text-gray-400 text-[10px] uppercase font-bold tracking-widest mb-1">XP Total</span>
                        <span className="text-3xl font-black text-transparent bg-clip-text bg-gradient-to-b from-[#FCFF52] to-yellow-600">{xp}</span>
                    </div>

                    <div className="bg-white/5 backdrop-blur-md rounded-2xl border border-white/10 p-5 flex flex-col items-center justify-center text-center hover:border-green-500/50 transition-colors group">
                        <div className="mb-2 p-2 bg-green-500/20 rounded-lg text-green-400 group-hover:scale-110 transition-transform">
                            <Crown className="w-5 h-5" />
                        </div>
                        <span className="text-gray-400 text-[10px] uppercase font-bold tracking-widest mb-1">Premios</span>
                        <span className="text-3xl font-black text-transparent bg-clip-text bg-gradient-to-b from-green-300 to-green-600">{nfts.length}</span>
                    </div>

                    <div className="bg-white/5 backdrop-blur-md rounded-2xl border border-white/10 p-5 flex flex-col items-center justify-center text-center hover:border-blue-500/50 transition-colors group">
                        <div className="mb-2 p-2 bg-blue-500/20 rounded-lg text-blue-400 group-hover:scale-110 transition-transform">
                            <Sparkles className="w-5 h-5" />
                        </div>
                        <span className="text-gray-400 text-[10px] uppercase font-bold tracking-widest mb-1">Estado</span>
                        <span className="text-sm font-bold text-blue-400 bg-blue-500/10 px-3 py-1 rounded-full border border-blue-500/20">Verificado</span>
                    </div>
                </div>

                <header className="mb-10 text-center relative">
                    <div className="inline-block relative">
                        <h1 className="text-4xl md:text-5xl font-black text-white mb-3 tracking-tight drop-shadow-[0_0_15px_rgba(255,255,255,0.3)]">
                            Mis Artefactos
                        </h1>
                        <div className="absolute -top-6 -right-8 text-[#FCFF52] animate-bounce delay-100 hidden md:block">
                            <Sparkles className="w-8 h-8" />
                        </div>
                    </div>

                    <p className="text-gray-400 text-lg max-w-lg mx-auto font-medium">
                        Colección de recompensas digitales ganadas por tu impacto en la comunidad.
                    </p>
                </header>

                {loading && nfts.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-20 gap-4">
                        <Loader2 className="w-12 h-12 text-[#FCFF52] animate-spin" />
                        <p className="text-gray-400 animate-pulse font-mono text-sm">Escaneando la blockchain...</p>
                    </div>
                ) : nfts.length === 0 ? (
                    <div className="text-center py-24 bg-white/5 backdrop-blur-xl rounded-3xl border border-white/10 shadow-2xl mx-4">
                        <div className="w-20 h-20 bg-white/5 rounded-full flex items-center justify-center mx-auto mb-6 border border-white/10">
                            <Crown className="w-10 h-10 text-gray-500/50" />
                        </div>
                        <p className="text-2xl text-white font-bold mb-3">Tu bóveda está vacía</p>
                        <p className="text-gray-400 mb-8 max-w-xs mx-auto">
                            ¡Participa en las campañas activas para ganar tu primer Loot Box NFT!
                        </p>
                        <Link
                            href="/"
                            className="px-8 py-3 bg-[#FCFF52] hover:bg-[#EBEF40] text-black rounded-xl text-base font-black transition-all hover:scale-105 shadow-[0_0_20px_rgba(252,255,82,0.4)]"
                        >
                            Comenzar Aventura
                        </Link>
                    </div>
                ) : (
                    <div className="grid grid-cols-2 lg:grid-cols-3 gap-6 md:gap-8 px-2">
                        {nfts.map((nft) => (
                            <div
                                key={nft.tokenId}
                                className="group relative bg-[#121212] rounded-3xl border border-white/10 overflow-hidden hover:border-[#FCFF52]/50 transition-all duration-500 hover:shadow-[0_0_30px_rgba(252,255,82,0.1)] hover:-translate-y-1"
                            >
                                {/* Image Container */}
                                <div className="aspect-[2/3] relative overflow-hidden bg-black/50">
                                    <div className="absolute inset-0 bg-gradient-to-t from-[#121212] via-transparent to-transparent opacity-60 z-10" />
                                    <img
                                        src={nft.image}
                                        alt={nft.name}
                                        className="w-full h-full object-cover transform group-hover:scale-110 transition-transform duration-700 ease-out"
                                        loading="lazy"
                                    />

                                    {/* Rarity Badge */}
                                    {nft.rarity && (
                                        <div className="absolute top-4 right-4 z-20">
                                            <span className="bg-black/80 backdrop-blur-md text-[#FCFF52] text-[10px] font-black px-3 py-1 rounded-lg border border-[#FCFF52]/30 shadow-lg uppercase tracking-wider">
                                                {nft.rarity}
                                            </span>
                                        </div>
                                    )}
                                </div>

                                {/* Content */}
                                <div className="relative z-20 -mt-20 p-5 pt-10 bg-gradient-to-t from-[#121212] via-[#121212] to-transparent">
                                    <div className="flex justify-between items-end mb-3">
                                        <h3 className="text-lg md:text-xl font-black text-white group-hover:text-[#FCFF52] transition-colors leading-tight line-clamp-1">
                                            {nft.name}
                                        </h3>
                                    </div>

                                    <div className="flex items-center gap-2 mb-4">
                                        <span className="text-[10px] font-mono font-bold text-gray-500 bg-white/5 px-2 py-1 rounded border border-white/5">
                                            #{nft.tokenId}
                                        </span>
                                        {nft.type && (
                                            <span className="text-[10px] font-bold text-gray-400 bg-white/5 px-2 py-1 rounded border border-white/5">
                                                {nft.type}
                                            </span>
                                        )}
                                    </div>

                                    <p className="text-gray-400 text-xs line-clamp-2 leading-relaxed h-8 mb-4">
                                        {nft.description}
                                    </p>

                                    <div className="pt-4 border-t border-white/5 flex justify-between items-center">
                                        <div className="flex items-center gap-1.5 px-2 py-1 rounded-full bg-green-500/10 border border-green-500/20">
                                            <div className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
                                            <span className="text-[10px] font-black text-green-500 uppercase tracking-widest">Active</span>
                                        </div>
                                        <button className="p-2 rounded-full bg-white/5 hover:bg-white/10 text-gray-400 hover:text-white transition-colors">
                                            <Sparkles className="w-4 h-4" />
                                        </button>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
