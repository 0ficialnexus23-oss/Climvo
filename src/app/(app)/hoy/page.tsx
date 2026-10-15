import Link from "next/link";
import { Users, Wind, CalendarClock } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { prisma } from "@/lib/prisma";
import { requireSession } from "@/lib/session";

export const metadata = { title: "Hoy · Climvo" };

export default async function HoyPage() {
  const session = await requireSession();
  const tenantId = session.user.tenantId;

  const [clientes, equipos] = await Promise.all([
    prisma.customer.count({ where: { tenantId } }),
    prisma.equipment.count({ where: { tenantId } }),
  ]);

  const stats = [
    { label: "Clientes", value: clientes, href: "/clientes", icon: Users },
    { label: "Equipos", value: equipos, href: "/equipos", icon: Wind },
    {
      label: "Mantenimientos",
      value: 0,
      href: "/hoy",
      icon: CalendarClock,
      hint: "Próximamente",
    },
  ];

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-xl font-semibold text-slate-900">
          Hola, {(session.user.name ?? "").split(" ")[0] || "equipo"}
        </h1>
        <p className="text-sm text-slate-500">Este es el estado de tu empresa.</p>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        {stats.map((s) => {
          const Icon = s.icon;
          return (
            <Link key={s.label} href={s.href}>
              <Card className="transition-colors hover:border-sky-300">
                <CardContent className="flex items-center gap-3">
                  <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-sky-50 text-sky-600">
                    <Icon className="h-5 w-5" aria-hidden />
                  </span>
                  <div>
                    <div className="text-2xl font-semibold leading-none text-slate-900">
                      {s.value}
                    </div>
                    <div className="text-xs text-slate-500">
                      {s.label}
                      {s.hint ? ` · ${s.hint}` : ""}
                    </div>
                  </div>
                </CardContent>
              </Card>
            </Link>
          );
        })}
      </div>

      <Card>
        <CardContent className="text-sm text-slate-600">
          Empieza registrando a tus <strong>clientes</strong> y sus{" "}
          <strong>equipos</strong>. Sobre esa base se construyen las
          solicitudes, presupuestos, órdenes y el mantenimiento preventivo.
        </CardContent>
      </Card>
    </div>
  );
}
