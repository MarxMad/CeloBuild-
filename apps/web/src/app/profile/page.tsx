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
        <div className="min-h-screen bg-background text-foreground p-4 md:p-8">
            {/* Navbar / Header */}
            <div className="sticky top-0 z-50 mb-8">
                <div className="max-w-6xl mx-auto flex items-center justify-between bg-background/60 backdrop-blur-xl rounded-2xl border shadow-sm p-4">
                    <Link
                        href="/"
                        className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors"
                    >
                        <ArrowLeft className="w-5 h-5" />
                        <span className="font-medium">Volver</span>
                    </Link>
                    <div className="flex items-center gap-4">
                        <button
                            onClick={fetchNFTs}
                            disabled={loading}
                            className="p-2 text-muted-foreground hover:text-yellow-600 transition-colors disabled:opacity-50"
                            title="Recargar colección"
                        >
                            <RefreshCw className={`w-5 h-5 ${loading ? "animate-spin" : ""}`} />
                        </button>
                        <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-yellow-500/10 border border-yellow-500/20">
                            <Crown className="w-4 h-4 text-yellow-600" />
                            <span className="text-sm font-bold text-yellow-600 uppercase tracking-wider">Colección</span>
                        </div>
                    </div>
                </div>
            </div>

            <div className="max-w-6xl mx-auto">
                <header className="mb-12 text-center">
                    <h1 className="text-3xl md:text-4xl font-bold text-foreground mb-2">
                        Mis Tarjetas Premiadas
                    </h1>
                    <p className="text-muted-foreground text-lg">
                        Colección de artefactos digitales ganados en campañas.
                    </p>
                </header>

                {loading && nfts.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-20 gap-4">
                        <Loader2 className="w-10 h-10 text-yellow-600 animate-spin" />
                        <p className="text-muted-foreground animate-pulse">Buscando tus tesoros...</p>
                    </div>
                ) : nfts.length === 0 ? (
                    <div className="text-center py-20 bg-background/60 backdrop-blur-xl rounded-2xl border shadow-sm">
                        <div className="w-16 h-16 bg-muted/20 rounded-full flex items-center justify-center mx-auto mb-4">
                            <Crown className="w-8 h-8 text-muted-foreground" />
                        </div>
                        <p className="text-xl text-foreground mb-2 font-medium">Aún no tienes tarjetas</p>
                        <p className="text-muted-foreground">¡Participa en campañas activas para ganar tu primer NFT!</p>
                        <button
                            onClick={fetchNFTs}
                            className="mt-6 px-6 py-2 bg-yellow-500/10 hover:bg-yellow-500/20 text-yellow-600 rounded-full text-sm font-bold transition-colors border border-yellow-500/20"
                        >
                            Intentar recargar
                        </button>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                        {nfts.map((nft) => (
                            <div
                                key={nft.tokenId}
                                className="group relative bg-background/60 backdrop-blur-xl rounded-2xl border shadow-sm overflow-hidden hover:border-yellow-500/30 transition-all duration-300 hover:shadow-md"
                            >
                                {/* Image Container */}
                                <div className="aspect-[2/3] relative overflow-hidden bg-muted">
                                    <img
                                        src={nft.image}
                                        alt={nft.name}
                                        className="w-full h-full object-cover transform group-hover:scale-105 transition-transform duration-500"
                                        loading="lazy"
                                    />

                                    {/* Rarity Badge */}
                                    {nft.rarity && (
                                        <div className="absolute top-3 right-3 bg-yellow-500/10 backdrop-blur-md border border-yellow-500/20 px-2 py-0.5 rounded-full shadow-sm">
                                            <span className="text-[10px] font-bold text-yellow-600 uppercase tracking-wider">
                                                {nft.rarity}
                                            </span>
                                        </div>
                                    )}
                                </div>

                                {/* Content */}
                                <div className="p-4">
                                    <div className="flex justify-between items-start mb-2">
                                        <h3 className="text-lg font-bold text-foreground group-hover:text-yellow-600 transition-colors line-clamp-1">
                                            {nft.name}
                                        </h3>
                                        <span className="text-[10px] font-mono text-muted-foreground bg-muted/30 px-1.5 py-0.5 rounded">
                                            #{nft.tokenId}
                                        </span>
                                    </div>

                                    <p className="text-muted-foreground text-xs line-clamp-2 mb-4 leading-relaxed">
                                        {nft.description}
                                    </p>

                                    <div className="pt-3 border-t border-border flex justify-between items-center">
                                        <div className="px-2 py-0.5 rounded-full bg-green-500/10 text-green-600 text-[10px] font-bold uppercase flex items-center gap-1.5">
                                            <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
                                            Active
                                        </div>
                                        {nft.type && (
                                            <span className="text-[10px] text-muted-foreground bg-muted/30 px-2 py-0.5 rounded border border-border/50">
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
