"use client";

import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { ArrowUpRight } from "lucide-react";

const LINKS = [
  { href: "/analizar", label: "Analizar" },
  { href: "/documentos", label: "Documentos" },
  { href: "/como-funciona", label: "Cómo funciona" },
];

export function Nav() {
  const pathname = usePathname();
  return (
    <header className="sticky top-0 z-50 border-b border-line bg-white/85 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-5">
        <Link href="/" className="flex items-center gap-2.5">
          <Image
            src="/uni-escudo-guinda.png"
            alt="Escudo UNI"
            width={24}
            height={32}
            className="h-8 w-auto"
          />
          <span className="text-[15px] font-semibold tracking-tight">
            TDR Risk Auditor
          </span>
        </Link>

        <nav className="hidden items-center gap-1 sm:flex">
          {LINKS.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className={`rounded-lg px-3.5 py-2 text-sm transition ${
                pathname.startsWith(l.href)
                  ? "bg-surface-2 text-fg"
                  : "text-muted hover:bg-surface hover:text-fg"
              }`}
            >
              {l.label}
            </Link>
          ))}
        </nav>

        <Link
          href="/analizar"
          className="inline-flex items-center gap-1.5 rounded-lg bg-flag px-4 py-2 text-sm font-medium text-white transition hover:bg-flag-deep"
        >
          Auditar un TDR
          <ArrowUpRight className="size-4" />
        </Link>
      </div>
    </header>
  );
}
