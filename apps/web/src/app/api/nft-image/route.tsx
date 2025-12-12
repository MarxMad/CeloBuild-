import { ImageResponse } from "next/og";
import { NextRequest } from "next/server";
import fs from "fs";
import path from "path";

// Switch to Node.js runtime to allow FS access
// Edge runtime often fails to fetch local assets via HTTP
export const runtime = "nodejs";

export async function GET(request: NextRequest) {
    const { searchParams } = new URL(request.url);
    const title = searchParams.get("title") || "Unknown Artifact";
    const rarity = searchParams.get("rarity") || "Common";
    const type = searchParams.get("type") || "Item";

    // Map rarity to image filename
    const rarityMap: Record<string, string> = {
        Common: "card_common_ver2.png",
        Rare: "card_rare_ver2.png",
        Epic: "card_epic_ver2.png",
        Legendary: "card_rare_ver2.png", // Reuse rare (pearlescent) for legendary
    };

    // Default to common if rarity not found (case insensitive check)
    const normalizedRarity = Object.keys(rarityMap).find(
        (k) => k.toLowerCase() === rarity.toLowerCase()
    ) || "Common";

    const imageFilename = rarityMap[normalizedRarity];

    // Use public CDN URL - Most reliable for Vercel/Next.js OG
    // Bypasses local filesystem and internal network resolution issues
    const publicBaseUrl = "https://celo-build-web-8rej.vercel.app";
    const imageUrl = `${publicBaseUrl}/cards/${imageFilename}`;

    // Note: We are not using FS here anymore, so the runtime can be edge or nodejs.
    // Keeping nodejs for safety as we might add other server-side logic, 
    // but fetching from public URL works in both.

    return new ImageResponse(
        (
            <div
                style={{
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    justifyContent: "center",
                    width: "100%",
                    height: "100%",
                    position: "relative",
                    backgroundColor: "#1a1a1a",
                    fontFamily: "sans-serif",
                }}
            >
                {/* Background Image */}
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                    src={imageUrl}
                    alt={rarity}
                    style={{
                        position: "absolute",
                        top: 0,
                        left: 0,
                        width: "100%",
                        height: "100%",
                        objectFit: "cover",
                    }}
                />

                {/* --- 1. TITLE (User Name) --- */}
                {/* Positioned below the 'PREMIO' header */}
                <div
                    style={{
                        position: "absolute",
                        top: 160,
                        width: "80%",
                        display: "flex",
                        justifyContent: "center",
                    }}
                >
                    <h1
                        style={{
                            fontSize: 36,
                            fontWeight: 900,
                            color: "#FFFFFF",
                            textAlign: "center",
                            textTransform: "uppercase",
                            letterSpacing: "2px",
                            textShadow: "0 2px 4px rgba(0,0,0,0.8), 0 0 15px rgba(255, 215, 0, 0.6)",
                            margin: 0,
                            padding: "10px 20px",
                            background: "rgba(0,0,0,0.4)", // Slight backing for readability
                            borderRadius: 12,
                            backdropFilter: "blur(2px)",
                            border: "1px solid rgba(255,255,255,0.1)",
                        }}
                    >
                        {title}
                    </h1>
                </div>

                {/* --- 2. TYPE BADGE --- */}
                {/* Positioned above the bottom data panels */}
                <div
                    style={{
                        position: "absolute",
                        bottom: 200,
                        display: "flex",
                        justifyContent: "center",
                    }}
                >
                    <div
                        style={{
                            background: "linear-gradient(90deg, #FFD700 0%, #FDB931 100%)",
                            padding: "6px 24px",
                            borderRadius: 8,
                            boxShadow: "0 4px 15px rgba(255, 215, 0, 0.3)",
                            border: "1px solid rgba(255, 255, 255, 0.4)",
                        }}
                    >
                        <span
                            style={{
                                fontSize: 20,
                                fontWeight: "bold",
                                color: "#000",
                                textTransform: "uppercase",
                                letterSpacing: "1px",
                            }}
                        >
                            {type}
                        </span>
                    </div>
                </div>

            </div>
        ),
        {
            width: 590,
            height: 860,
        }
    );
}
