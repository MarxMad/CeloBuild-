"use client";

import { useEffect, useState } from "react";
import { useAccount, usePublicClient } from "wagmi";
import { MINTER_ADDRESS, MINTER_ABI } from "@/lib/contracts";
import { parseAbiItem } from "viem";
import Link from "next/link";
import { ArrowLeft, Crown, Loader2, RefreshCw } from "lucide-react";

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
        <div className="min-h-screen bg-[#0a0a0a] text-white">
            {/* Navbar / Header */}
            <div className="sticky top-0 z-50 border-b border-white/10 bg-[#0a0a0a]/80 backdrop-blur-xl">
                <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
                    <Link
                        href="/"
                        className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors"
                    >
                        <ArrowLeft className="w-5 h-5" />
                        <span className="font-medium">Volver</span>
                    </Link>
                    <div className="flex items-center gap-4">
                        <button
                            onClick={fetchNFTs}
                            disabled={loading}
                            className="p-2 text-gray-400 hover:text-yellow-500 transition-colors disabled:opacity-50"
                            title="Recargar colección"
                        >
                            <RefreshCw className={`w-5 h-5 ${loading ? "animate-spin" : ""}`} />
                        </button>
                        <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-yellow-500/10 border border-yellow-500/20">
                            <Crown className="w-4 h-4 text-yellow-500" />
                            <span className="text-sm font-bold text-yellow-500 uppercase tracking-wider">Colección</span>
                        </div>
                    </div>
                </div>
            </div>

            <div className="max-w-6xl mx-auto p-4 md:p-8">
                <header className="mb-12 text-center relative">
                    <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-32 h-32 bg-yellow-500/20 blur-[100px] rounded-full pointer-events-none" />
                    <h1 className="relative text-4xl md:text-5xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-yellow-200 via-yellow-400 to-yellow-600 mb-4">
                        Mis Tarjetas Premiadas
                    </h1>
                    <p className="relative text-gray-400 text-lg max-w-2xl mx-auto">
                        Explora tu colección de artefactos digitales únicos ganados por tu participación en campañas.
                    </p>
                </header>

                {loading && nfts.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-20 gap-4">
                        <Loader2 className="w-10 h-10 text-yellow-500 animate-spin" />
                        <p className="text-gray-500 animate-pulse">Buscando tus tesoros en la blockchain...</p>
                    </div>
                ) : nfts.length === 0 ? (
                    <div className="text-center py-20 bg-white/5 rounded-3xl border border-white/10 backdrop-blur-sm">
                        <div className="w-16 h-16 bg-white/5 rounded-full flex items-center justify-center mx-auto mb-4">
                            <Crown className="w-8 h-8 text-gray-600" />
                        </div>
                        <p className="text-xl text-gray-300 mb-2 font-medium">Aún no tienes tarjetas</p>
                        <p className="text-gray-500">¡Participa en campañas activas para ganar tu primer NFT!</p>
                        <button
                            onClick={fetchNFTs}
                            className="mt-6 px-6 py-2 bg-yellow-500/10 hover:bg-yellow-500/20 text-yellow-500 rounded-full text-sm font-bold transition-colors"
                        >
                            Intentar recargar
                        </button>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
                        {nfts.map((nft) => (
                            <div
                                key={nft.tokenId}
                                className="group relative bg-gradient-to-b from-white/5 to-white/[0.02] rounded-3xl overflow-hidden border border-white/10 hover:border-yellow-500/50 transition-all duration-500 hover:shadow-[0_0_40px_rgba(255,215,0,0.1)] hover:-translate-y-1"
                            >
                                {/* Image Container */}
                                <div className="aspect-[2/3] relative overflow-hidden bg-[#1a1a1a]">
                                    <img
                                        src={nft.image}
                                        alt={nft.name}
                                        className="w-full h-full object-cover transform group-hover:scale-105 transition-transform duration-700"
                                        loading="lazy"
                                    />

                                    {/* Overlay Gradient */}
                                    <div className="absolute inset-0 bg-gradient-to-t from-[#0a0a0a] via-transparent to-transparent opacity-60" />

                                    {/* Rarity Badge */}
                                    {nft.rarity && (
                                        <div className="absolute top-4 right-4 bg-black/60 backdrop-blur-md border border-yellow-500/30 px-3 py-1 rounded-full shadow-lg">
                                            <span className="text-xs font-bold text-yellow-400 uppercase tracking-wider">
                                                {nft.rarity}
                                            </span>
                                        </div>
                                    )}
                                </div>

                                {/* Content */}
                                <div className="absolute bottom-0 left-0 right-0 p-6 bg-gradient-to-t from-[#0a0a0a] via-[#0a0a0a]/90 to-transparent pt-12">
                                    <h3 className="text-2xl font-bold text-white mb-2 group-hover:text-yellow-400 transition-colors font-display">
                                        {nft.name}
                                    </h3>
                                    <p className="text-gray-300 text-sm line-clamp-2 mb-4 font-light leading-relaxed">
                                        {nft.description}
                                    </p>

                                    <div className="flex justify-between items-center pt-4 border-t border-white/10">
                                        <div className="flex items-center gap-2">
                                            <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                                            <span className="text-xs text-green-400 font-medium uppercase tracking-wider">Active</span>
                                        </div>
                                        {nft.type && (
                                            <span className="text-xs text-gray-400 bg-white/10 px-2 py-1 rounded border border-white/5">
                                                {nft.type}
                                            </span>
                                        )}
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
