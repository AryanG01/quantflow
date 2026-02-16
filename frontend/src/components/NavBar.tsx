"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/", label: "Dashboard" },
  { href: "/trades", label: "Trades" },
  { href: "/backtest", label: "Backtest" },
  { href: "/settings", label: "Settings" },
];

export function NavBar() {
  const pathname = usePathname();

  return (
    <nav className="flex items-center gap-1 text-xs">
      {links.map((link) => {
        const isActive = pathname === link.href;
        return (
          <Link
            key={link.href}
            href={link.href}
            className={`px-3 py-1.5 rounded-sm transition-colors ${
              isActive
                ? "bg-[var(--color-bg-card)] text-[var(--color-accent-cyan)]"
                : "text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-bg-card-hover)]"
            }`}
          >
            {link.label}
          </Link>
        );
      })}
    </nav>
  );
}
