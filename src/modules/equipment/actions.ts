"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { toUserMessage } from "@/lib/errors";
import { requireSession } from "@/lib/session";
import {
  actualizarEquipo,
  crearEquipo,
  eliminarEquipo,
} from "./service";

export type FormState = { error?: string } | undefined;

function field(formData: FormData, name: string): string {
  const value = formData.get(name);
  return typeof value === "string" ? value : "";
}

function leer(formData: FormData) {
  return {
    customerId: field(formData, "customerId"),
    locationId: field(formData, "locationId"),
    type: field(formData, "type"),
    brand: field(formData, "brand"),
    model: field(formData, "model"),
    serialNumber: field(formData, "serialNumber"),
    capacityTr: field(formData, "capacityTr"),
    refrigerant: field(formData, "refrigerant"),
    installDate: field(formData, "installDate"),
    warrantyUntil: field(formData, "warrantyUntil"),
    notes: field(formData, "notes"),
  };
}

export async function crearEquipoAction(
  _prev: FormState,
  formData: FormData,
): Promise<FormState> {
  const session = await requireSession();

  let nuevoId: string;
  try {
    const equipo = await crearEquipo(session.user.tenantId, leer(formData));
    nuevoId = equipo.id;
  } catch (error) {
    return { error: toUserMessage(error) };
  }

  revalidatePath("/equipos");
  redirect(`/equipos/${nuevoId}`);
}

export async function actualizarEquipoAction(
  id: string,
  _prev: FormState,
  formData: FormData,
): Promise<FormState> {
  const session = await requireSession();

  try {
    await actualizarEquipo(session.user.tenantId, id, leer(formData));
  } catch (error) {
    return { error: toUserMessage(error) };
  }

  revalidatePath("/equipos");
  revalidatePath(`/equipos/${id}`);
  redirect(`/equipos/${id}`);
}

export async function eliminarEquipoAction(id: string): Promise<void> {
  const session = await requireSession();
  await eliminarEquipo(session.user.tenantId, id);
  revalidatePath("/equipos");
  redirect("/equipos");
}
