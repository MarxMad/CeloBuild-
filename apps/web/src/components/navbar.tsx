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
          <div className="relative h-8 w-32">
            <Image
              src="/premio_portada.svg"
              alt="Premio.xyz"
              fill
              className="object-contain object-left"
              priority
            />
          </div>
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
