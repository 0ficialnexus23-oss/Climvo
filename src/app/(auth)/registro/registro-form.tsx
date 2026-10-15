"use client";

import { useActionState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { registrarAction, type ActionState } from "@/modules/auth/actions";

export function RegistroForm() {
  const [state, formAction, pending] = useActionState<ActionState, FormData>(
    registrarAction,
    undefined,
  );

  return (
    <form action={formAction} className="space-y-4">
      <div className="space-y-1.5">
        <Label htmlFor="companyName">Nombre de la empresa</Label>
        <Input
          id="companyName"
          name="companyName"
          required
          placeholder="Climas del Norte"
        />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="name">Tu nombre</Label>
        <Input id="name" name="name" required placeholder="Juan Pérez" />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="email">Correo</Label>
        <Input
          id="email"
          name="email"
          type="email"
          inputMode="email"
          autoComplete="email"
          required
          placeholder="tu@empresa.com"
        />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="phone">Teléfono (opcional)</Label>
        <Input
          id="phone"
          name="phone"
          type="tel"
          inputMode="tel"
          placeholder="81 1234 5678"
        />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="password">Contraseña</Label>
        <Input
          id="password"
          name="password"
          type="password"
          autoComplete="new-password"
          required
          minLength={8}
          placeholder="Mínimo 8 caracteres"
        />
      </div>

      {state?.error ? (
        <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
          {state.error}
        </p>
      ) : null}

      <Button type="submit" className="w-full" disabled={pending}>
        {pending ? "Creando…" : "Crear empresa"}
      </Button>
    </form>
  );
}
