import Link from "next/link";
import { notFound } from "next/navigation";
import QRCode from "qrcode";
import { ArrowLeft, Pencil } from "lucide-react";

import { DeleteForm } from "@/components/ui/delete-form";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { requireSession } from "@/lib/session";
import { eliminarEquipoAction } from "@/modules/equipment/actions";
import { obtenerEquipo } from "@/modules/equipment/repository";
import { formatDate } from "@/lib/utils";

export default async function EquipoDetallePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const session = await requireSession();
  const { id } = await params;
  const equipo = await obtenerEquipo(session.user.tenantId, id);

  if (!equipo) notFound();

  const baseUrl = process.env.NEXT_PUBLIC_APP_URL ?? "http://localhost:3000";
  const qrDataUrl = await QRCode.toDataURL(`${baseUrl}/equipos/${equipo.id}`, {
    width: 220,
    margin: 1,
  });

  const filas: Array<[string, string]> = [
    ["Cliente", equipo.customer.name],
    ["Ubicación", equipo.location?.name ?? "—"],
    ["Marca", equipo.brand ?? "—"],
    ["Modelo", equipo.model ?? "—"],
    ["No. de serie", equipo.serialNumber ?? "—"],
    ["Capacidad", equipo.capacityTr ? `${equipo.capacityTr} TR` : "—"],
    ["Refrigerante", equipo.refrigerant ?? "—"],
    ["Instalación", formatDate(equipo.installDate)],
    ["Garantía hasta", formatDate(equipo.warrantyUntil)],
  ];

  return (
    <div className="space-y-5">
      <Link
        href="/equipos"
        className="inline-flex items-center gap-1 text-sm text-slate-500"
      >
        <ArrowLeft className="h-4 w-4" aria-hidden />
        Equipos
      </Link>

      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h1 className="truncate text-xl font-semibold text-slate-900">
            {equipo.type}
          </h1>
          <p className="mt-0.5 text-sm text-slate-500">
            {equipo.customer.name}
            {equipo.location ? ` · ${equipo.location.name}` : ""}
          </p>
        </div>
        <Link href={`/equipos/${equipo.id}/editar`}>
          <Button size="sm" variant="outline">
            <Pencil className="h-4 w-4" aria-hidden />
            Editar
          </Button>
        </Link>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Ficha técnica</CardTitle>
        </CardHeader>
        <CardContent>
          <dl className="divide-y divide-slate-100 text-sm">
            {filas.map(([label, valor]) => (
              <div key={label} className="flex justify-between gap-3 py-2">
                <dt className="text-slate-500">{label}</dt>
                <dd className="text-right font-medium text-slate-900">
                  {valor}
                </dd>
              </div>
            ))}
          </dl>
          {equipo.notes ? (
            <p className="mt-3 rounded-lg bg-slate-50 p-3 text-sm text-slate-600">
              {equipo.notes}
            </p>
          ) : null}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Código QR del equipo</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col items-center gap-3">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={qrDataUrl}
            alt={`Código QR del equipo ${equipo.type}`}
            width={220}
            height={220}
            className="rounded-xl border border-slate-200"
          />
          <p className="text-center text-xs text-slate-500">
            Imprímelo y pégalo en el equipo. Al escanearlo se abre esta ficha
            para consultar su historial.
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Historial de mantenimiento</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-slate-500">
          Aún no hay servicios registrados. El historial se llenará cuando
          completes órdenes de servicio sobre este equipo.
        </CardContent>
      </Card>

      <div className="flex justify-center pt-2">
        <DeleteForm
          action={eliminarEquipoAction.bind(null, equipo.id)}
          label="Eliminar equipo"
          confirmText={`¿Eliminar el equipo ${equipo.type}? Esta acción no se puede deshacer.`}
        />
      </div>
    </div>
  );
}
