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

    // Construct absolute URL for the image
    // In Vercel/Next.js, we need the full URL for fetch() in ImageResponse
    const protocol = request.headers.get("x-forwarded-proto") || "http";
    const host = request.headers.get("host");
    const baseUrl = `${protocol}://${host}`;
    const imageUrl = `${baseUrl}/cards/${imageFilename}`;

    const description = searchParams.get("description") || "A mysterious artifact from the decentralized web.";
    const logoUrl = `${baseUrl}/premio_portada.svg`;

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

                {/* Overlay Gradient for readability */}
                <div
                    style={{
                        position: "absolute",
                        top: 0,
                        left: 0,
                        width: "100%",
                        height: "100%",
                        background: "linear-gradient(to bottom, rgba(0,0,0,0.3) 0%, rgba(0,0,0,0.1) 40%, rgba(0,0,0,0.8) 100%)",
                    }}
                />

                {/* Card Content Container */}
                <div
                    style={{
                        display: "flex",
                        flexDirection: "column",
                        alignItems: "center",
                        justifyContent: "space-between",
                        width: "88%",
                        height: "90%",
                        position: "relative",
                        zIndex: 10,
                        paddingTop: 30,
                        paddingBottom: 40,
                        border: "4px solid rgba(255, 215, 0, 0.3)",
                        borderRadius: 24,
                        boxShadow: "inset 0 0 20px rgba(0,0,0,0.5)",
                    }}
                >
                    {/* Header: Logo and Title */}
                    <div
                        style={{
                            display: "flex",
                            flexDirection: "column",
                            alignItems: "center",
                            gap: 10,
                            width: "100%",
                        }}
                    >
                        {/* Logo */}
                        <img
                            src={logoUrl}
                            width="80"
                            height="80"
                            style={{
                                objectFit: "contain",
                                filter: "drop-shadow(0 0 5px rgba(255,255,255,0.5))",
                            }}
                        />

                        {/* Title */}
                        <h1
                            style={{
                                fontSize: 42,
                                fontWeight: "bold",
                                color: "#fff",
                                textShadow: "0 2px 4px rgba(0,0,0,0.8), 0 0 10px rgba(255,215,0,0.5)",
                                margin: 0,
                                fontFamily: "sans-serif",
                                textTransform: "uppercase",
                                textAlign: "center",
                                letterSpacing: "1px",
                                maxWidth: "90%",
                            }}
                        >
                            {title}
                        </h1>
                    </div>

                    {/* Bottom Area: Description and Stats */}
                    <div
                        style={{
                            display: "flex",
                            flexDirection: "column",
                            alignItems: "center",
                            width: "90%",
                            background: "rgba(0, 0, 0, 0.75)",
                            border: "2px solid rgba(255, 255, 255, 0.2)",
                            borderRadius: 16,
                            padding: "20px",
                            gap: 15,
                            backdropFilter: "blur(4px)",
                        }}
                    >
                        {/* Type Badge */}
                        <div
                            style={{
                                display: "flex",
                                alignItems: "center",
                                justifyContent: "center",
                                background: "linear-gradient(90deg, #FFD700 0%, #FFA500 100%)",
                                borderRadius: 8,
                                padding: "4px 16px",
                                marginTop: -30, // Pull up to overlap border
                                boxShadow: "0 4px 6px rgba(0,0,0,0.3)",
                            }}
                        >
                            <span
                                style={{
                                    fontSize: 18,
                                    color: "#000",
                                    fontWeight: "bold",
                                    fontFamily: "monospace",
                                    textTransform: "uppercase",
                                }}
                            >
                                {type}
                            </span>
                        </div>

                        {/* Description Text */}
                        <p
                            style={{
                                fontSize: 20,
                                color: "#e0e0e0",
                                textAlign: "center",
                                lineHeight: 1.4,
                                margin: 0,
                                fontFamily: "serif",
                                fontStyle: "italic",
                                textShadow: "0 1px 2px rgba(0,0,0,0.8)",
                            }}
                        >
                            "{description}"
                        </p>

                        {/* Rarity Footer */}
                        <div
                            style={{
                                width: "100%",
                                height: 2,
                                background: "rgba(255,255,255,0.2)",
                                margin: "5px 0",
                            }}
                        />

                        <span
                            style={{
                                fontSize: 16,
                                color: "#FFD700",
                                fontWeight: "bold",
                                fontFamily: "sans-serif",
                                letterSpacing: "2px",
                                textTransform: "uppercase",
                            }}
                        >
                            ★ {normalizedRarity} Edition ★
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
