"use client";

import { useActionState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

type FormState = { error?: string; ok?: boolean } | undefined;

export function LocationForm({
  action,
}: {
  action: (prev: FormState, formData: FormData) => Promise<FormState>;
}) {
  const [state, formAction, pending] = useActionState<FormState, FormData>(
    action,
    undefined,
  );

  return (
    <form action={formAction} className="space-y-3">
      <div className="space-y-1.5">
        <Label htmlFor="loc-name">Nombre de la ubicación *</Label>
        <Input
          id="loc-name"
          name="name"
          required
          placeholder="Sucursal Centro"
        />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="loc-address">Dirección</Label>
        <Input id="loc-address" name="address" placeholder="Av. Juárez 123" />
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1.5">
          <Label htmlFor="loc-city">Ciudad</Label>
          <Input id="loc-city" name="city" />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="loc-state">Estado</Label>
          <Input id="loc-state" name="state" />
        </div>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1.5">
          <Label htmlFor="loc-zip">C.P.</Label>
          <Input id="loc-zip" name="zip" inputMode="numeric" />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="loc-phone">Teléfono</Label>
          <Input id="loc-phone" name="phone" type="tel" inputMode="tel" />
        </div>
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="loc-notes">Notas</Label>
        <Textarea id="loc-notes" name="notes" className="min-h-16" />
      </div>

      {state?.error ? (
        <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
          {state.error}
        </p>
      ) : null}

      <Button type="submit" variant="secondary" disabled={pending}>
        {pending ? "Agregando…" : "Agregar ubicación"}
      </Button>
    </form>
  );
}
