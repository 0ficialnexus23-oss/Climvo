"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, Users, Wind, Settings } from "lucide-react";

import { cn } from "@/lib/utils";

const items = [
  { href: "/hoy", label: "Hoy", icon: Home },
  { href: "/clientes", label: "Clientes", icon: Users },
  { href: "/equipos", label: "Equipos", icon: Wind },
  { href: "/ajustes", label: "Ajustes", icon: Settings },
];

export function BottomNav() {
  const pathname = usePathname();

  return (
    <nav className="fixed inset-x-0 bottom-0 z-20 border-t border-slate-200 bg-white">
      <ul className="mx-auto flex max-w-3xl">
        {items.map((item) => {
          const active =
            pathname === item.href || pathname.startsWith(`${item.href}/`);
          const Icon = item.icon;
          return (
            <li key={item.href} className="flex-1">
              <Link
                href={item.href}
                className={cn(
                  "flex flex-col items-center gap-1 py-2.5 text-xs font-medium transition-colors",
                  active ? "text-sky-600" : "text-slate-500",
                )}
              >
                <Icon className="h-5 w-5" aria-hidden />
                {item.label}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
