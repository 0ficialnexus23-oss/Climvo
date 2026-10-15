import Link from "next/link";
import { Plus, Search } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { requireSession } from "@/lib/session";
import { listarClientes } from "@/modules/customers/repository";
import { customerTypeLabels } from "@/modules/customers/schema";

export const metadata = { title: "Clientes · Climvo" };

export default async function ClientesPage({
  searchParams,
}: {
  searchParams: Promise<{ q?: string }>;
}) {
  const session = await requireSession();
  const { q } = await searchParams;
  const busqueda = q?.trim() || undefined;
  const clientes = await listarClientes(session.user.tenantId, busqueda);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-slate-900">Clientes</h1>
        <Link href="/clientes/nuevo">
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
          placeholder="Buscar por nombre, contacto o teléfono…"
        />
        <Button type="submit" variant="secondary" aria-label="Buscar">
          <Search className="h-4 w-4" aria-hidden />
        </Button>
      </form>

      {clientes.length === 0 ? (
        <Card>
          <CardContent className="text-sm text-slate-600">
            {busqueda
              ? "Ningún cliente coincide con la búsqueda."
              : "Aún no tienes clientes. Crea el primero para empezar a registrar sus equipos."}
          </CardContent>
        </Card>
      ) : (
        <ul className="space-y-2">
          {clientes.map((c) => (
            <li key={c.id}>
              <Link href={`/clientes/${c.id}`} className="block">
                <Card className="transition-colors hover:border-sky-300">
                  <CardContent>
                    <p className="font-medium text-slate-900">{c.name}</p>
                    <p className="text-xs text-slate-500">
                      {customerTypeLabels[c.type]} · {c._count.equipment}{" "}
                      {c._count.equipment === 1 ? "equipo" : "equipos"} ·{" "}
                      {c._count.locations}{" "}
                      {c._count.locations === 1 ? "ubicación" : "ubicaciones"}
                    </p>
                    {c.phone ? (
                      <p className="mt-0.5 text-xs text-slate-400">{c.phone}</p>
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
