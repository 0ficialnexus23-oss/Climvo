import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft } from "lucide-react";

import {
  EquipmentForm,
  type CustomerOption,
  type LocationOption,
} from "@/components/equipment/equipment-form";
import { Card, CardContent } from "@/components/ui/card";
import { requireSession } from "@/lib/session";
import { actualizarEquipoAction } from "@/modules/equipment/actions";
import { obtenerEquipo } from "@/modules/equipment/repository";
import { listarOpcionesClientes } from "@/modules/customers/repository";
import { listarOpcionesUbicaciones } from "@/modules/locations/repository";

function fechaInput(value: Date | null): string {
  return value ? value.toISOString().slice(0, 10) : "";
}

export default async function EditarEquipoPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const session = await requireSession();
  const { id } = await params;
  const tenantId = session.user.tenantId;

  const [equipo, customers, locations] = await Promise.all([
    obtenerEquipo(tenantId, id),
    listarOpcionesClientes(tenantId),
    listarOpcionesUbicaciones(tenantId),
  ]);

  if (!equipo) notFound();

  const action = actualizarEquipoAction.bind(null, equipo.id);

  return (
    <div className="space-y-4">
      <Link
        href={`/equipos/${equipo.id}`}
        className="inline-flex items-center gap-1 text-sm text-slate-500"
      >
        <ArrowLeft className="h-4 w-4" aria-hidden />
        Volver
      </Link>
      <h1 className="text-xl font-semibold text-slate-900">Editar equipo</h1>
      <Card>
        <CardContent>
          <EquipmentForm
            action={action}
            customers={customers as CustomerOption[]}
            locations={locations as LocationOption[]}
            submitLabel="Guardar cambios"
            defaultValues={{
              customerId: equipo.customerId,
              locationId: equipo.locationId,
              type: equipo.type,
              brand: equipo.brand,
              model: equipo.model,
              serialNumber: equipo.serialNumber,
              capacityTr: equipo.capacityTr ? String(equipo.capacityTr) : "",
              refrigerant: equipo.refrigerant,
              installDate: fechaInput(equipo.installDate),
              warrantyUntil: fechaInput(equipo.warrantyUntil),
              notes: equipo.notes,
            }}
          />
        </CardContent>
      </Card>
    </div>
  );
}
