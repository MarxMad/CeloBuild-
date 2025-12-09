import { ImageResponse } from 'next/og';

export const runtime = 'edge';

export async function GET(request: Request) {
    try {
        const { searchParams } = new URL(request.url);

        // ?title=<title>&score=<score>&reward=<reward>&username=<username>
        const title = searchParams.get('title') || 'Loot Box Winner';
        const score = searchParams.get('score') || '0';
        const reward = searchParams.get('reward') || 'XP';
        const username = searchParams.get('username') || 'Explorer';

        return new ImageResponse(
            (
                <div
                    style={{
                        height: '100%',
                        width: '100%',
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        justifyContent: 'center',
                        backgroundColor: '#0f172a',
                        backgroundImage: 'radial-gradient(circle at 25px 25px, #1e293b 2%, transparent 0%), radial-gradient(circle at 75px 75px, #1e293b 2%, transparent 0%)',
                        backgroundSize: '100px 100px',
                        color: 'white',
                        fontFamily: 'sans-serif',
                    }}
                >
                    <div
                        style={{
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'center',
                            justifyContent: 'center',
                            border: '4px solid rgba(255, 255, 255, 0.1)',
                            borderRadius: '20px',
                            padding: '40px 60px',
                            backgroundColor: 'rgba(0, 0, 0, 0.5)',
                            boxShadow: '0 0 50px rgba(0,0,0,0.5)',
                        }}
                    >
                        <div
                            style={{
                                fontSize: 30,
                                fontWeight: 'bold',
                                color: '#94a3b8',
                                marginBottom: 20,
                                textTransform: 'uppercase',
                                letterSpacing: '2px',
                            }}
                        >
                            Loot Box Result
                        </div>

                        <div
                            style={{
                                fontSize: 60,
                                fontWeight: 'bold',
                                background: 'linear-gradient(to right, #fbbf24, #d97706)',
                                backgroundClip: 'text',
                                color: 'transparent',
                                marginBottom: 10,
                                textAlign: 'center',
                            }}
                        >
                            {username}
                        </div>

                        <div
                            style={{
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                gap: '20px',
                                marginTop: 20,
                            }}
                        >
                            <div
                                style={{
                                    display: 'flex',
                                    flexDirection: 'column',
                                    alignItems: 'center',
                                }}
                            >
                                <div style={{ fontSize: 24, color: '#94a3b8' }}>Score</div>
                                <div style={{ fontSize: 48, fontWeight: 'bold' }}>{score}</div>
                            </div>

                            <div style={{ width: 2, height: 60, backgroundColor: '#334155' }} />

                            <div
                                style={{
                                    display: 'flex',
                                    flexDirection: 'column',
                                    alignItems: 'center',
                                }}
                            >
                                <div style={{ fontSize: 24, color: '#94a3b8' }}>Reward</div>
                                <div style={{ fontSize: 48, fontWeight: 'bold', color: '#4ade80' }}>{reward.toUpperCase()}</div>
                            </div>
                        </div>

                        <div
                            style={{
                                marginTop: 40,
                                fontSize: 20,
                                color: '#64748b',
                                fontStyle: 'italic',
                            }}
                        >
                            Participate now on Celo Sepolia
                        </div>
                    </div>
                </div>
            ),
            {
                width: 1200,
                height: 630,
            },
        );
    } catch (e: any) {
        return new Response(`Failed to generate the image`, {
            status: 500,
        });
    }
}
