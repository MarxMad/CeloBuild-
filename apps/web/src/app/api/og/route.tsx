import { ImageResponse } from 'next/og';

export const runtime = 'edge';

export async function GET(request: Request) {
    try {
        const { searchParams } = new URL(request.url);

        // ?title=<title>&score=<score>&reward=<reward>&username=<username>&user=<user>&locale=<en|es>&type=<default|victory>
        const title = searchParams.get('title') || 'Loot Box Winner';
        const score = searchParams.get('score') || '0';
        const reward = searchParams.get('reward') || 'XP';
        const username = searchParams.get('username') || searchParams.get('user') || 'Explorer';
        const locale = searchParams.get('locale') || 'en';
        const type = searchParams.get('type') || 'default';

        // I18n strings
        const text = {
            result: locale === 'es' ? 'Resultado Loot Box' : 'Loot Box Result',
            victory: locale === 'es' ? '¡VICTORIA!' : 'VICTORY!',
            start: locale === 'es' ? 'Participa ahora en Celo' : 'Participate now on Celo',
            score: locale === 'es' ? 'Puntaje' : 'Score',
            reward: locale === 'es' ? 'Premio' : 'Reward',
        };

        const isVictory = type === 'victory';

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
                        backgroundColor: isVictory ? '#1a0b2e' : '#0f172a',
                        backgroundImage: isVictory 
                            ? 'radial-gradient(circle at 30% 20%, rgba(133, 93, 205, 0.3) 0%, transparent 50%), radial-gradient(circle at 70% 80%, rgba(252, 255, 82, 0.2) 0%, transparent 50%)'
                            : 'radial-gradient(circle at 25px 25px, rgba(255, 255, 255, 0.05) 2%, transparent 0%), radial-gradient(circle at 75px 75px, rgba(255, 255, 255, 0.05) 2%, transparent 0%)',
                        backgroundSize: isVictory ? '100% 100%' : '100px 100px',
                        color: 'white',
                        fontFamily: '"Inter", "Roboto", sans-serif',
                        position: 'relative',
                    }}
                >
                    {/* Decorative elements */}
                    {isVictory && (
                        <>
                            <div
                                style={{
                                    position: 'absolute',
                                    top: 0,
                                    left: 0,
                                    right: 0,
                                    height: '4px',
                                    background: 'linear-gradient(90deg, #855DCD, #FCFF52, #855DCD)',
                                }}
                            />
                            <div
                                style={{
                                    position: 'absolute',
                                    top: 50,
                                    left: 50,
                                    width: 200,
                                    height: 200,
                                    borderRadius: '50%',
                                    background: 'radial-gradient(circle, rgba(133, 93, 205, 0.2) 0%, transparent 70%)',
                                    filter: 'blur(60px)',
                                }}
                            />
                            <div
                                style={{
                                    position: 'absolute',
                                    bottom: 50,
                                    right: 50,
                                    width: 150,
                                    height: 150,
                                    borderRadius: '50%',
                                    background: 'radial-gradient(circle, rgba(252, 255, 82, 0.15) 0%, transparent 70%)',
                                    filter: 'blur(50px)',
                                }}
                            />
                        </>
                    )}

                    {/* Main card */}
                    <div
                        style={{
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'center',
                            justifyContent: 'center',
                            border: isVictory ? '3px solid #FCFF52' : '3px solid rgba(255, 255, 255, 0.1)',
                            borderRadius: '24px',
                            padding: '60px 80px',
                            backgroundColor: isVictory ? 'rgba(26, 11, 46, 0.95)' : 'rgba(0, 0, 0, 0.8)',
                            boxShadow: isVictory 
                                ? '0 0 100px rgba(252, 255, 82, 0.4), 0 20px 60px rgba(133, 93, 205, 0.3)' 
                                : '0 0 50px rgba(0,0,0,0.5)',
                            position: 'relative',
                            zIndex: 1,
                        }}
                    >
                        {/* Trophy/Icon */}
                        {isVictory && (
                            <div
                                style={{
                                    fontSize: 80,
                                    marginBottom: 20,
                                    filter: 'drop-shadow(0 0 20px rgba(252, 255, 82, 0.6))',
                                }}
                            >
                                🏆
                            </div>
                        )}

                        {/* Title */}
                        <div
                            style={{
                                fontSize: isVictory ? 56 : 40,
                                fontWeight: '900',
                                color: isVictory ? '#FCFF52' : '#94a3b8',
                                marginBottom: 30,
                                textTransform: 'uppercase',
                                letterSpacing: '6px',
                                textShadow: isVictory ? '0 0 30px rgba(252, 255, 82, 0.5)' : 'none',
                            }}
                        >
                            {isVictory ? text.victory : text.result}
                        </div>

                        {/* Username */}
                        <div
                            style={{
                                fontSize: 72,
                                fontWeight: '900',
                                background: isVictory 
                                    ? 'linear-gradient(135deg, #FCFF52 0%, #855DCD 100%)'
                                    : 'linear-gradient(to right, #fbbf24, #d97706)',
                                color: 'transparent',
                                backgroundClip: 'text',
                                marginBottom: 40,
                                textAlign: 'center',
                                textShadow: 'none',
                            }}
                        >
                            @{username}
                        </div>

                        {/* Stats */}
                        <div
                            style={{
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                gap: '40px',
                                marginTop: 20,
                            }}
                        >
                            <div
                                style={{
                                    display: 'flex',
                                    flexDirection: 'column',
                                    alignItems: 'center',
                                    padding: '20px 30px',
                                    backgroundColor: 'rgba(255, 255, 255, 0.05)',
                                    borderRadius: '16px',
                                    border: '1px solid rgba(255, 255, 255, 0.1)',
                                }}
                            >
                                <div style={{ fontSize: 20, color: '#94a3b8', marginBottom: 8 }}>{text.score}</div>
                                <div style={{ fontSize: 56, fontWeight: 'bold', color: '#FCFF52' }}>{score}</div>
                            </div>

                            <div
                                style={{
                                    display: 'flex',
                                    flexDirection: 'column',
                                    alignItems: 'center',
                                    padding: '20px 30px',
                                    backgroundColor: 'rgba(255, 255, 255, 0.05)',
                                    borderRadius: '16px',
                                    border: '1px solid rgba(255, 255, 255, 0.1)',
                                }}
                            >
                                <div style={{ fontSize: 20, color: '#94a3b8', marginBottom: 8 }}>{text.reward}</div>
                                <div style={{ fontSize: 48, fontWeight: 'bold', color: '#4ade80' }}>{reward.toUpperCase()}</div>
                            </div>
                        </div>

                        {/* CTA */}
                        <div
                            style={{
                                marginTop: 50,
                                padding: '16px 40px',
                                backgroundColor: isVictory ? '#855DCD' : 'rgba(255, 255, 255, 0.1)',
                                borderRadius: '12px',
                                fontSize: 24,
                                fontWeight: 'bold',
                                color: '#ffffff',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '12px',
                                border: isVictory ? '2px solid #FCFF52' : 'none',
                            }}
                        >
                            <span>🚀</span> {text.start}
                        </div>
                    </div>

                    {/* Branding */}
                    <div
                        style={{
                            position: 'absolute',
                            bottom: 30,
                            right: 30,
                            fontSize: 18,
                            color: 'rgba(255, 255, 255, 0.5)',
                            fontWeight: '600',
                        }}
                    >
                        Premio.xyz
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
