"use client";

import { useEffect, useState } from "react";
import { useAccount, usePublicClient } from "wagmi";
import { MINTER_ADDRESS, MINTER_ABI } from "@/lib/contracts";
import { parseAbiItem } from "viem";

type NFT = {
    tokenId: string;
    image: string;
    name: string;
    description: string;
    rarity?: string;
    type?: string;
};

export default function ProfilePage() {
    const { address, isConnected } = useAccount();
    const publicClient = usePublicClient();
    const [nfts, setNfts] = useState<NFT[]>([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        async function fetchNFTs() {
            if (!address || !publicClient) return;
            setLoading(true);
            try {
                // 1. Get Mint events
                const logs = await publicClient.getLogs({
                    address: MINTER_ADDRESS,
                    event: parseAbiItem('event LootMinted(bytes32 indexed campaignId, address indexed to, uint256 tokenId, bool soulbound)'),
                    args: {
                        to: address,
                    },
                    fromBlock: 'earliest',
                });

                const loadedNfts: NFT[] = [];

                // 2. Fetch tokenURI and metadata for each
                for (const log of logs) {
                    const tokenId = log.args.tokenId;
                    if (!tokenId) continue;

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
                            const res = await fetch(tokenUri);
                            metadata = await res.json();
                        }

                        loadedNfts.push({
                            tokenId: tokenId.toString(),
                            image: metadata.image,
                            name: metadata.name,
                            description: metadata.description,
                            rarity: metadata.attributes?.find((a: any) => a.trait_type === "Rarity")?.value,
                            type: metadata.attributes?.find((a: any) => a.trait_type === "Type")?.value,
                        });
                    } catch (err) {
                        console.error(`Error fetching metadata for token ${tokenId}`, err);
                    }
                }

                setNfts(loadedNfts.reverse()); // Show newest first
            } catch (err) {
                console.error("Error fetching NFTs", err);
            } finally {
                setLoading(false);
            }
        }

        if (isConnected) {
            fetchNFTs();
        }
    }, [address, isConnected, publicClient]);

    if (!isConnected) {
        return (
            <div className="flex min-h-screen flex-col items-center justify-center p-4 text-center">
                <h1 className="text-2xl font-bold mb-4 text-white">Conecta tu wallet</h1>
                <p className="text-gray-400">Necesitas conectar tu wallet para ver tus premios.</p>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-[#0a0a0a] p-4 md:p-8">
            <div className="max-w-6xl mx-auto">
                <header className="mb-12 text-center">
                    <h1 className="text-4xl md:text-5xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-yellow-400 to-orange-500 mb-4">
                        Mis Tarjetas Premiadas
                    </h1>
                    <p className="text-gray-400 text-lg">Colección de artefactos digitales ganados en campañas.</p>
                </header>

                {loading ? (
                    <div className="flex justify-center py-20">
                        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-yellow-400"></div>
                    </div>
                ) : nfts.length === 0 ? (
                    <div className="text-center py-20 bg-gray-900/50 rounded-2xl border border-gray-800">
                        <p className="text-xl text-gray-300 mb-2">Aún no tienes tarjetas.</p>
                        <p className="text-gray-500">¡Participa en campañas para ganar!</p>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
                        {nfts.map((nft) => (
                            <div
                                key={nft.tokenId}
                                className="group relative bg-gray-900 rounded-2xl overflow-hidden border border-gray-800 hover:border-yellow-500/50 transition-all duration-300 hover:shadow-[0_0_30px_rgba(255,215,0,0.15)]"
                            >
                                {/* Image Container */}
                                <div className="aspect-[2/3] relative overflow-hidden">
                                    <img
                                        src={nft.image}
                                        alt={nft.name}
                                        className="w-full h-full object-cover transform group-hover:scale-105 transition-transform duration-500"
                                    />

                                    {/* Rarity Badge */}
                                    {nft.rarity && (
                                        <div className="absolute top-4 right-4 bg-black/80 backdrop-blur-md border border-yellow-500/30 px-3 py-1 rounded-full">
                                            <span className="text-xs font-bold text-yellow-400 uppercase tracking-wider">
                                                {nft.rarity}
                                            </span>
                                        </div>
                                    )}
                                </div>

                                {/* Content */}
                                <div className="p-6">
                                    <h3 className="text-xl font-bold text-white mb-2 group-hover:text-yellow-400 transition-colors">
                                        {nft.name}
                                    </h3>
                                    <p className="text-gray-400 text-sm line-clamp-3">
                                        {nft.description}
                                    </p>

                                    <div className="mt-4 pt-4 border-t border-gray-800 flex justify-between items-center">
                                        <span className="text-xs text-gray-500 font-mono">
                                            #{nft.tokenId}
                                        </span>
                                        {nft.type && (
                                            <span className="text-xs text-gray-400 bg-gray-800 px-2 py-1 rounded">
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
