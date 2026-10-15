import Link from "next/link";
import { Plus, Search } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { requireSession } from "@/lib/session";
import { listarEquipos } from "@/modules/equipment/repository";

export const metadata = { title: "Equipos · Climvo" };

export default async function EquiposPage({
  searchParams,
}: {
  searchParams: Promise<{ q?: string }>;
}) {
  const session = await requireSession();
  const { q } = await searchParams;
  const busqueda = q?.trim() || undefined;
  const equipos = await listarEquipos(session.user.tenantId, busqueda);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-slate-900">Equipos</h1>
        <Link href="/equipos/nuevo">
          <Button size="sm">
            <Plus className="h-4 w-4" aria-hidden />
            Nuevo
          </Button>
        </Link>
      </div>

      <form className="flex gap-2">
        <Input
          name="q"
          defaultValue={q ?? ""}
          placeholder="Buscar por cliente, tipo, marca o serie…"
        />
        <Button type="submit" variant="secondary" aria-label="Buscar">
          <Search className="h-4 w-4" aria-hidden />
        </Button>
      </form>

      {equipos.length === 0 ? (
        <Card>
          <CardContent className="text-sm text-slate-600">
            {busqueda
              ? "Ningún equipo coincide con la búsqueda."
              : "Aún no tienes equipos registrados. Registra el primero para llevar su historial de mantenimiento."}
          </CardContent>
        </Card>
      ) : (
        <ul className="space-y-2">
          {equipos.map((eq) => (
            <li key={eq.id}>
              <Link href={`/equipos/${eq.id}`} className="block">
                <Card className="transition-colors hover:border-sky-300">
                  <CardContent>
                    <p className="font-medium text-slate-900">
                      {eq.type}
                      {eq.brand ? ` · ${eq.brand}` : ""}
                      {eq.model ? ` ${eq.model}` : ""}
                    </p>
                    <p className="text-xs text-slate-500">
                      {eq.customer.name}
                      {eq.location ? ` · ${eq.location.name}` : ""}
                    </p>
                    {eq.serialNumber ? (
                      <p className="mt-0.5 text-xs text-slate-400">
                        Serie {eq.serialNumber}
                      </p>
                    ) : null}
                  </CardContent>
                </Card>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
