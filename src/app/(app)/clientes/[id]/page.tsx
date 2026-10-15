import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft, MapPin, Pencil, Plus, Wind } from "lucide-react";

import { DeleteForm } from "@/components/ui/delete-form";
import { LocationForm } from "@/components/locations/location-form";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { requireSession } from "@/lib/session";
import { eliminarClienteAction } from "@/modules/customers/actions";
import { obtenerCliente } from "@/modules/customers/repository";
import { customerTypeLabels } from "@/modules/customers/schema";
import {
  crearUbicacionAction,
  eliminarUbicacionAction,
} from "@/modules/locations/actions";

export default async function ClienteDetallePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const session = await requireSession();
  const { id } = await params;
  const cliente = await obtenerCliente(session.user.tenantId, id);

  if (!cliente) notFound();

  const crearUbicacion = crearUbicacionAction.bind(null, cliente.id);
  const eliminarCliente = eliminarClienteAction.bind(null, cliente.id);

  return (
    <div className="space-y-5">
      <Link
        href="/clientes"
        className="inline-flex items-center gap-1 text-sm text-slate-500"
      >
        <ArrowLeft className="h-4 w-4" aria-hidden />
        Clientes
      </Link>

      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h1 className="truncate text-xl font-semibold text-slate-900">
            {cliente.name}
          </h1>
          <p className="mt-0.5 text-sm text-slate-500">
            {customerTypeLabels[cliente.type]}
          </p>
        </div>
        <Link href={`/clientes/${cliente.id}/editar`}>
          <Button size="sm" variant="outline">
            <Pencil className="h-4 w-4" aria-hidden />
            Editar
          </Button>
        </Link>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Datos de contacto</CardTitle>
        </CardHeader>
        <CardContent className="space-y-1 text-sm">
          <p>
            <span className="text-slate-500">Contacto:</span>{" "}
            {cliente.contactName ?? "—"}
          </p>
          <p>
            <span className="text-slate-500">Teléfono:</span>{" "}
            {cliente.phone ?? "—"}
          </p>
          <p>
            <span className="text-slate-500">Correo:</span>{" "}
            {cliente.email ?? "—"}
          </p>
          {cliente.notes ? (
            <p className="pt-1 text-slate-600">{cliente.notes}</p>
          ) : null}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <MapPin className="h-4 w-4 text-slate-400" aria-hidden />
            Ubicaciones ({cliente.locations.length})
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {cliente.locations.length === 0 ? (
            <p className="text-sm text-slate-500">
              Sin ubicaciones registradas.
            </p>
          ) : (
            <ul className="divide-y divide-slate-100">
              {cliente.locations.map((loc) => (
                <li
                  key={loc.id}
                  className="flex items-center justify-between gap-2 py-2"
                >
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium text-slate-900">
                      {loc.name}
                    </p>
                    <p className="truncate text-xs text-slate-500">
                      {[loc.address, loc.city, loc.state]
                        .filter(Boolean)
                        .join(", ") || "Sin dirección"}
                    </p>
                  </div>
                  <DeleteForm
                    action={eliminarUbicacionAction.bind(
                      null,
                      cliente.id,
                      loc.id,
                    )}
                    label="Quitar"
                    confirmText={`¿Eliminar la ubicación "${loc.name}"?`}
                  />
                </li>
              ))}
            </ul>
          )}

          <details className="rounded-xl border border-slate-200 p-3">
            <summary className="cursor-pointer text-sm font-medium text-sky-700">
              + Agregar ubicación
            </summary>
            <div className="pt-3">
              <LocationForm action={crearUbicacion} />
            </div>
          </details>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Wind className="h-4 w-4 text-slate-400" aria-hidden />
            Equipos ({cliente.equipment.length})
          </CardTitle>
          <Link href={`/equipos/nuevo?cliente=${cliente.id}`}>
            <Button size="sm" variant="secondary">
              <Plus className="h-4 w-4" aria-hidden />
              Agregar
            </Button>
          </Link>
        </CardHeader>
        <CardContent>
          {cliente.equipment.length === 0 ? (
            <p className="text-sm text-slate-500">
              Sin equipos registrados.
            </p>
          ) : (
            <ul className="divide-y divide-slate-100">
              {cliente.equipment.map((eq) => (
                <li key={eq.id}>
                  <Link
                    href={`/equipos/${eq.id}`}
                    className="flex items-center justify-between gap-2 py-2"
                  >
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium text-slate-900">
                        {eq.type}
                        {eq.brand ? ` · ${eq.brand}` : ""}
                      </p>
                      <p className="truncate text-xs text-slate-500">
                        {eq.location?.name ?? "Sin ubicación"}
                        {eq.serialNumber ? ` · Serie ${eq.serialNumber}` : ""}
                      </p>
                    </div>
                    <Badge tone="neutral">Ver</Badge>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      <div className="pt-2">
        <DeleteForm
          action={eliminarCliente}
          label="Eliminar cliente"
          confirmText={`¿Eliminar a "${cliente.name}"? Se eliminarán también sus equipos y ubicaciones.`}
          className="flex justify-center"
        />
      </div>
    </div>
  );
}
