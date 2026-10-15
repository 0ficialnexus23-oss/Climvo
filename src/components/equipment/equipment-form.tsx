"use client";

import { useActionState, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";

type FormState = { error?: string } | undefined;

export type CustomerOption = { id: string; name: string };
export type LocationOption = { id: string; name: string; customerId: string };

type Props = {
  action: (prev: FormState, formData: FormData) => Promise<FormState>;
  customers: CustomerOption[];
  locations: LocationOption[];
  defaultValues?: {
    customerId?: string;
    locationId?: string | null;
    type?: string;
    brand?: string | null;
    model?: string | null;
    serialNumber?: string | null;
    capacityTr?: string | null;
    refrigerant?: string | null;
    installDate?: string | null;
    warrantyUntil?: string | null;
    notes?: string | null;
  };
  submitLabel?: string;
};

export function EquipmentForm({
  action,
  customers,
  locations,
  defaultValues,
  submitLabel = "Guardar equipo",
}: Props) {
  const [state, formAction, pending] = useActionState<FormState, FormData>(
    action,
    undefined,
  );
  const [customerId, setCustomerId] = useState(defaultValues?.customerId ?? "");

  const opcionesUbicacion = useMemo(
    () => locations.filter((l) => l.customerId === customerId),
    [locations, customerId],
  );

  return (
    <form action={formAction} className="space-y-4">
      <div className="space-y-1.5">
        <Label htmlFor="customerId">Cliente *</Label>
        <Select
          id="customerId"
          name="customerId"
          required
          value={customerId}
          onChange={(e) => setCustomerId(e.target.value)}
        >
          <option value="">Selecciona un cliente…</option>
          {customers.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </Select>
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="locationId">Ubicación</Label>
        <Select
          id="locationId"
          name="locationId"
          defaultValue={defaultValues?.locationId ?? ""}
          disabled={!customerId || opcionesUbicacion.length === 0}
        >
          <option value="">
            {customerId && opcionesUbicacion.length === 0
              ? "Este cliente no tiene ubicaciones"
              : "Sin ubicación específica"}
          </option>
          {opcionesUbicacion.map((l) => (
            <option key={l.id} value={l.id}>
              {l.name}
            </option>
          ))}
        </Select>
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="type">Tipo de equipo *</Label>
        <Input
          id="type"
          name="type"
          required
          defaultValue={defaultValues?.type ?? ""}
          placeholder="Minisplit, chiller, fan & coil…"
        />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1.5">
          <Label htmlFor="brand">Marca</Label>
          <Input
            id="brand"
            name="brand"
            defaultValue={defaultValues?.brand ?? ""}
            placeholder="LG, Mirage…"
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="model">Modelo</Label>
          <Input
            id="model"
            name="model"
            defaultValue={defaultValues?.model ?? ""}
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1.5">
          <Label htmlFor="serialNumber">No. de serie</Label>
          <Input
            id="serialNumber"
            name="serialNumber"
            defaultValue={defaultValues?.serialNumber ?? ""}
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="capacityTr">Capacidad (TR)</Label>
          <Input
            id="capacityTr"
            name="capacityTr"
            inputMode="decimal"
            defaultValue={defaultValues?.capacityTr ?? ""}
            placeholder="2.5"
          />
        </div>
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="refrigerant">Refrigerante</Label>
        <Input
          id="refrigerant"
          name="refrigerant"
          defaultValue={defaultValues?.refrigerant ?? ""}
          placeholder="R-410A, R-32…"
        />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1.5">
          <Label htmlFor="installDate">Fecha de instalación</Label>
          <Input
            id="installDate"
            name="installDate"
            type="date"
            defaultValue={defaultValues?.installDate ?? ""}
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="warrantyUntil">Garantía hasta</Label>
          <Input
            id="warrantyUntil"
            name="warrantyUntil"
            type="date"
            defaultValue={defaultValues?.warrantyUntil ?? ""}
          />
        </div>
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="notes">Notas</Label>
        <Textarea
          id="notes"
          name="notes"
          defaultValue={defaultValues?.notes ?? ""}
          placeholder="Observaciones del equipo"
        />
      </div>

      {state?.error ? (
        <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
          {state.error}
        </p>
      ) : null}

      <Button type="submit" className="w-full" disabled={pending}>
        {pending ? "Guardando…" : submitLabel}
      </Button>
    </form>
  );
}
