import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

import { Navbar } from '@/components/navbar';
import { WalletProvider } from "@/components/wallet-provider"
import { FarcasterProvider } from "@/components/farcaster-provider";

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  metadataBase: new URL('https://celo-build-web-8rej.vercel.app'),
  title: 'Premio.xyz',
  description: 'Recompensas virales en Farcaster con Celo MiniPay',
  manifest: '/manifest.json',
  icons: {
    icon: '/icon.png',
    shortcut: '/icon.png',
    apple: '/icon.png',
  },
  openGraph: {
    title: 'Premio.xyz',
    description: 'Recompensas virales en Farcaster con Celo MiniPay',
    images: [
      {
        url: '/image.png',
        width: 1200,
        height: 630,
        alt: 'Premio.xyz Cover',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Premio.xyz',
    description: 'Recompensas virales en Farcaster con Celo MiniPay',
    images: ['/image.png'],
  },
  other: {
    "fc:frame": "vNext",
    "fc:frame:image": "https://celo-build-web-8rej.vercel.app/image.png",
    "fc:frame:image:aspect_ratio": "1.91:1",
    "fc:frame:button:1": "Lanzar App",
    "fc:frame:button:1:action": "link",
    "fc:frame:button:1:target": "https://celo-build-web-8rej.vercel.app",
  }
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        {/* Navbar is included on all pages */}
        <div className="relative flex min-h-screen flex-col">
          <FarcasterProvider>
            <WalletProvider>
              <Navbar />
              <main className="flex-1">
                {children}
              </main>
            </WalletProvider>
          </FarcasterProvider>
        </div>
      </body>
    </html>
  );
}
