import Link from "next/link";
import { ArrowLeft } from "lucide-react";

import {
  EquipmentForm,
  type CustomerOption,
  type LocationOption,
} from "@/components/equipment/equipment-form";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { requireSession } from "@/lib/session";
import { crearEquipoAction } from "@/modules/equipment/actions";
import { listarOpcionesClientes } from "@/modules/customers/repository";
import { listarOpcionesUbicaciones } from "@/modules/locations/repository";

export const metadata = { title: "Nuevo equipo · Climvo" };

export default async function NuevoEquipoPage({
  searchParams,
}: {
  searchParams: Promise<{ cliente?: string }>;
}) {
  const session = await requireSession();
  const { cliente } = await searchParams;
  const tenantId = session.user.tenantId;

  const [customers, locations] = await Promise.all([
    listarOpcionesClientes(tenantId),
    listarOpcionesUbicaciones(tenantId),
  ]);

  if (customers.length === 0) {
    return (
      <div className="space-y-4">
        <Link
          href="/equipos"
          className="inline-flex items-center gap-1 text-sm text-slate-500"
        >
          <ArrowLeft className="h-4 w-4" aria-hidden />
          Equipos
        </Link>
        <Card>
          <CardContent className="space-y-3 text-sm text-slate-600">
            <p>
              Para registrar un equipo primero necesitas un cliente.
            </p>
            <Link href="/clientes/nuevo">
              <Button size="sm">Crear cliente</Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <Link
        href="/equipos"
        className="inline-flex items-center gap-1 text-sm text-slate-500"
      >
        <ArrowLeft className="h-4 w-4" aria-hidden />
        Equipos
      </Link>
      <h1 className="text-xl font-semibold text-slate-900">Nuevo equipo</h1>
      <Card>
        <CardContent>
          <EquipmentForm
            action={crearEquipoAction}
            customers={customers as CustomerOption[]}
            locations={locations as LocationOption[]}
            defaultValues={{ customerId: cliente ?? "" }}
          />
        </CardContent>
      </Card>
    </div>
  );
}
