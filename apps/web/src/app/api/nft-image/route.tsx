import { ImageResponse } from "next/og";
import { NextRequest } from "next/server";

export const runtime = "edge";

export async function GET(request: NextRequest) {
    const { searchParams } = new URL(request.url);
    const title = searchParams.get("title") || "Unknown Artifact";
    const rarity = searchParams.get("rarity") || "Common";
    const type = searchParams.get("type") || "Item";

    // Map rarity to image filename
    const rarityMap: Record<string, string> = {
        Common: "common.png",
        Rare: "rare.png",
        Epic: "epic.png",
        Legendary: "legendary.png",
    };

    // Default to common if rarity not found (case insensitive check)
    const normalizedRarity = Object.keys(rarityMap).find(
        (k) => k.toLowerCase() === rarity.toLowerCase()
    ) || "Common";

    const imageFilename = rarityMap[normalizedRarity];

    // Construct absolute URL for the image
    // In Vercel/Next.js, we need the full URL for fetch() in ImageResponse
    const protocol = request.headers.get("x-forwarded-proto") || "http";
    const host = request.headers.get("host");
    const baseUrl = `${protocol}://${host}`;
    const imageUrl = `${baseUrl}/cards/${imageFilename}`;

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
                }}
            >
                {/* Background Image */}
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

                {/* Text Overlay Container */}
                <div
                    style={{
                        display: "flex",
                        flexDirection: "column",
                        alignItems: "center",
                        justifyContent: "space-between",
                        width: "86%", // Adjust based on card border width
                        height: "88%", // Adjust based on card border height
                        position: "relative",
                        zIndex: 10,
                        paddingTop: 40,
                        paddingBottom: 60,
                    }}
                >
                    {/* Title Area */}
                    <div
                        style={{
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            width: "100%",
                            textAlign: "center",
                        }}
                    >
                        <h1
                            style={{
                                fontSize: 48,
                                fontWeight: "bold",
                                color: "#fff",
                                textShadow: "0 0 10px rgba(0,0,0,0.8)",
                                margin: 0,
                                fontFamily: "sans-serif",
                                textTransform: "uppercase",
                                letterSpacing: "2px",
                            }}
                        >
                            {title}
                        </h1>
                    </div>

                    {/* Bottom Info Area */}
                    <div
                        style={{
                            display: "flex",
                            flexDirection: "column",
                            alignItems: "center",
                            gap: 10,
                        }}
                    >
                        <div
                            style={{
                                display: "flex",
                                alignItems: "center",
                                justifyContent: "center",
                                background: "rgba(0,0,0,0.6)",
                                border: "1px solid rgba(255,255,255,0.3)",
                                borderRadius: 12,
                                padding: "8px 24px",
                            }}
                        >
                            <span
                                style={{
                                    fontSize: 24,
                                    color: "#FCFF52",
                                    fontWeight: "bold",
                                    fontFamily: "monospace",
                                    textTransform: "uppercase",
                                }}
                            >
                                {type}
                            </span>
                        </div>

                        <span
                            style={{
                                fontSize: 18,
                                color: "rgba(255,255,255,0.7)",
                                fontWeight: "normal",
                                fontFamily: "sans-serif",
                            }}
                        >
                            {normalizedRarity} Edition
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
