"use server";

import { revalidatePath } from "next/cache";

import { toUserMessage } from "@/lib/errors";
import { requireSession } from "@/lib/session";
import { crearUbicacion, eliminarUbicacion } from "./service";

export type FormState = { error?: string; ok?: boolean } | undefined;

function field(formData: FormData, name: string): string {
  const value = formData.get(name);
  return typeof value === "string" ? value : "";
}

export async function crearUbicacionAction(
  customerId: string,
  _prev: FormState,
  formData: FormData,
): Promise<FormState> {
  const session = await requireSession();

  try {
    await crearUbicacion(session.user.tenantId, customerId, {
      name: field(formData, "name"),
      address: field(formData, "address"),
      city: field(formData, "city"),
      state: field(formData, "state"),
      zip: field(formData, "zip"),
      contactName: field(formData, "contactName"),
      phone: field(formData, "phone"),
      notes: field(formData, "notes"),
    });
  } catch (error) {
    return { error: toUserMessage(error) };
  }

  revalidatePath(`/clientes/${customerId}`);
  return { ok: true };
}

export async function eliminarUbicacionAction(
  customerId: string,
  locationId: string,
): Promise<void> {
  const session = await requireSession();
  await eliminarUbicacion(session.user.tenantId, locationId);
  revalidatePath(`/clientes/${customerId}`);
}
