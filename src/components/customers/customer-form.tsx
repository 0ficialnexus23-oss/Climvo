"use client";

import { useActionState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { customerTypeLabels, customerTypes } from "@/modules/customers/schema";

type FormState = { error?: string } | undefined;

type Props = {
  action: (prev: FormState, formData: FormData) => Promise<FormState>;
  defaultValues?: {
    name?: string;
    type?: string;
    contactName?: string | null;
    phone?: string | null;
    email?: string | null;
    notes?: string | null;
  };
  submitLabel?: string;
};

export function CustomerForm({
  action,
  defaultValues,
  submitLabel = "Guardar",
}: Props) {
  const [state, formAction, pending] = useActionState<FormState, FormData>(
    action,
    undefined,
  );

  return (
    <form action={formAction} className="space-y-4">
      <div className="space-y-1.5">
        <Label htmlFor="name">Nombre del cliente *</Label>
        <Input
          id="name"
          name="name"
          required
          defaultValue={defaultValues?.name ?? ""}
          placeholder="Hotel Costa Azul"
        />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="type">Tipo</Label>
        <Select
          id="type"
          name="type"
          defaultValue={defaultValues?.type ?? "COMMERCIAL"}
        >
          {customerTypes.map((t) => (
            <option key={t} value={t}>
              {customerTypeLabels[t]}
            </option>
          ))}
        </Select>
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="contactName">Persona de contacto</Label>
        <Input
          id="contactName"
          name="contactName"
          defaultValue={defaultValues?.contactName ?? ""}
          placeholder="Ing. López"
        />
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="space-y-1.5">
          <Label htmlFor="phone">Teléfono / WhatsApp</Label>
          <Input
            id="phone"
            name="phone"
            type="tel"
            inputMode="tel"
            defaultValue={defaultValues?.phone ?? ""}
            placeholder="81 1234 5678"
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="email">Correo</Label>
          <Input
            id="email"
            name="email"
            type="email"
            inputMode="email"
            defaultValue={defaultValues?.email ?? ""}
            placeholder="contacto@cliente.com"
          />
        </div>
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="notes">Notas</Label>
        <Textarea
          id="notes"
          name="notes"
          defaultValue={defaultValues?.notes ?? ""}
          placeholder="Horario de acceso, indicaciones, etc."
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
