import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

import { Navbar } from '@/components/navbar';
import { WalletProvider } from "@/components/wallet-provider"
import { FarcasterProvider } from "@/components/farcaster-provider";

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Premio.xyz',
  description: 'Recompensas virales en Farcaster con Celo MiniPay',
  manifest: '/manifest.json',
  icons: {
    icon: '/PremioxyzLogo.svg',
    shortcut: '/PremioxyzLogo.svg',
    apple: '/PremioxyzLogo.svg',
  },
  openGraph: {
    title: 'Premio.xyz',
    description: 'Recompensas virales en Farcaster con Celo MiniPay',
    images: ['/PremioxyzLogo.svg'],
  },
  twitter: {
    card: 'summary',
    title: 'Premio.xyz',
    description: 'Recompensas virales en Farcaster con Celo MiniPay',
    images: ['/PremioxyzLogo.svg'],
  },
  other: {
    "fc:frame": "vNext",
    "fc:frame:image": "https://premio.xyz/PremioxyzLogo.svg",
    "fc:frame:button:1": "Lanzar App",
    "fc:frame:button:1:action": "link", 
    "fc:frame:button:1:target": "https://premio.xyz",
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
