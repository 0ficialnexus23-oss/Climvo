"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { toUserMessage } from "@/lib/errors";
import { requireSession } from "@/lib/session";
import {
  actualizarCliente,
  crearCliente,
  eliminarCliente,
} from "./service";

export type FormState = { error?: string } | undefined;

function field(formData: FormData, name: string): string {
  const value = formData.get(name);
  return typeof value === "string" ? value : "";
}

function leer(formData: FormData) {
  return {
    name: field(formData, "name"),
    type: field(formData, "type"),
    contactName: field(formData, "contactName"),
    phone: field(formData, "phone"),
    email: field(formData, "email"),
    notes: field(formData, "notes"),
  };
}

export async function crearClienteAction(
  _prev: FormState,
  formData: FormData,
): Promise<FormState> {
  const session = await requireSession();

  let nuevoId: string;
  try {
    const cliente = await crearCliente(session.user.tenantId, leer(formData));
    nuevoId = cliente.id;
  } catch (error) {
    return { error: toUserMessage(error) };
  }

  revalidatePath("/clientes");
  redirect(`/clientes/${nuevoId}`);
}

export async function actualizarClienteAction(
  id: string,
  _prev: FormState,
  formData: FormData,
): Promise<FormState> {
  const session = await requireSession();

  try {
    await actualizarCliente(session.user.tenantId, id, leer(formData));
  } catch (error) {
    return { error: toUserMessage(error) };
  }

  revalidatePath("/clientes");
  revalidatePath(`/clientes/${id}`);
  redirect(`/clientes/${id}`);
}

export async function eliminarClienteAction(id: string): Promise<void> {
  const session = await requireSession();
  await eliminarCliente(session.user.tenantId, id);
  revalidatePath("/clientes");
  redirect("/clientes");
}
