"use client"

import Link from "next/link"
import Image from "next/image"
import { ConnectButton } from "@/components/connect-button"

export function Navbar() {
  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/80 backdrop-blur-md">
      <div className="container flex h-14 max-w-md mx-auto items-center justify-between px-4">

        {/* Logo */}
        <Link href="/" className="flex items-center gap-2 transition-opacity hover:opacity-80">
          <div className="relative h-8 w-8">
            <Image
              src="/PremioxyzLogo.svg"
              alt="Premio.xyz Logo"
              fill
              className="object-contain"
              priority
            />
          </div>
          <span className="font-bold text-sm tracking-tight hidden sm:inline-block">
            Premio.xyz
          </span>
        </Link>

        {/* Actions */}
        <div className="flex items-center gap-2">
          <div className="scale-90 origin-right">
            <ConnectButton />
          </div>
        </div>
      </div>
    </header>
  )
}
